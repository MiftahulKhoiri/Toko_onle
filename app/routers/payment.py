# app/routers/payment.py
import hashlib
import hmac
import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.midtrans_client import SERVER_KEY, core_api, pastikan_midtrans_terkonfigurasi, snap
from app.order_status import mark_as_cancelled, mark_as_paid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payment", tags=["payment"])


def _get_pending_cart(db: Session, user: models.User) -> models.Order:
    cart = (
        db.query(models.Order)
        .filter(models.Order.user_id == user.id, models.Order.status == "pending")
        .first()
    )
    if not cart or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Keranjang kosong")
    return cart


def _batalkan_klaim_checkout(
    db: Session,
    cart_id: int,
    alamat_id_lama: int | None,
    items_stok: list[tuple[int, int, str]],
) -> None:
    """Kembalikan keadaan sebelum checkout kalau transaksi Midtrans gagal dibuat.

    Urutannya sengaja: balikin status pesanan DULU dengan syarat statusnya masih
    "menunggu_pembayaran". Stok baru dikembalikan kalau pesanan memang berhasil dibalikin,
    supaya stok nggak ke-restock dua kali kalau status pesanan sudah berubah dari jalur lain.

    Kalau langkah pemulihan ini sendiri gagal (mis. database bermasalah), pesanan tetap
    "menunggu_pembayaran" dengan stok terpotong — pembeli masih bisa membatalkannya lewat
    Pesanan Saya, dan pembatalan itu yang akan mengembalikan stok. Jadi arah gagalnya aman
    (stok tidak hilang permanen).
    """
    try:
        baris_pesanan = (
            db.query(models.Order)
            .filter(models.Order.id == cart_id, models.Order.status == "menunggu_pembayaran")
            .update(
                {
                    models.Order.status: "pending",
                    models.Order.payment_method: None,
                    models.Order.midtrans_order_id: None,
                    models.Order.alamat_id: alamat_id_lama,
                },
                synchronize_session=False,
            )
        )
        if baris_pesanan == 1:
            for produk_id, jumlah, _nama in items_stok:
                (
                    db.query(models.Produk)
                    .filter(models.Produk.id == produk_id)
                    .update({models.Produk.stok: models.Produk.stok + jumlah}, synchronize_session=False)
                )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Gagal memulihkan keranjang %s setelah Midtrans gagal", cart_id)


@router.post("/checkout")
def checkout(
    data: schemas.CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    cart = _get_pending_cart(db, current_user)
    pastikan_midtrans_terkonfigurasi()

    # ---- Validasi (baca saja, belum ada yang diubah di database) ----
    if cart.metode_pengiriman == "diantar":
        if not data.alamat_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Alamat pengiriman belum dipilih",
            )
        alamat = (
            db.query(models.Alamat)
            .filter(models.Alamat.id == data.alamat_id, models.Alamat.user_id == current_user.id)
            .first()
        )
        if not alamat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alamat tidak ditemukan")
        alamat_id_baru = alamat.id
    else:
        alamat_id_baru = None

    for item in cart.items:
        if not item.produk:
            # Produk dihapus/hilang setelah masuk keranjang — jangan lanjut checkout, daripada
            # crash pas hitung gross_amount atau ngurangin stok.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Salah satu produk di keranjang sudah tidak tersedia, silakan hapus item tersebut dulu",
            )

    # ---- Siapkan semua data SEBELUM transaksi database dimulai ----
    # Semua nilai diambil ke variabel biasa di sini, jadi setelah db.commit() nanti kita nggak
    # perlu menyentuh objek ORM lagi (yang otomatis "kedaluwarsa" setelah commit).
    cart_id = cart.id
    alamat_id_lama = cart.alamat_id
    metode_pengiriman = cart.metode_pengiriman
    items_stok = [(item.produk_id, item.jumlah, item.produk.nama) for item in cart.items]

    order_id = f"cakyud-{cart_id}-{secrets.token_hex(4)}"
    ongkir = int(cart.ongkir or 0)
    gross_amount = int(sum(item.harga_saat_beli * item.jumlah for item in cart.items)) + ongkir

    item_details = [
        {
            "id": str(item.produk_id),
            "price": int(item.harga_saat_beli),
            "quantity": item.jumlah,
            "name": item.produk.nama[:50],
        }
        for item in cart.items
    ]
    if ongkir > 0:
        item_details.append({
            "id": "ongkir",
            "price": ongkir,
            "quantity": 1,
            "name": f"Ongkos Kirim ({metode_pengiriman})",
        })

    # email/telepon sekarang boleh kosong (akun Google tanpa email publik, akun
    # daftar-cepat lewat Facebook/No. HP, dst) — jangan kirim key-nya sama sekali
    # ke Midtrans kalau kosong, daripada kirim null yang bisa ditolak validasi mereka.
    customer_details = {"first_name": current_user.nama}
    if current_user.email:
        customer_details["email"] = current_user.email
    if current_user.telepon:
        customer_details["phone"] = current_user.telepon

    param = {
        "transaction_details": {"order_id": order_id, "gross_amount": gross_amount},
        "customer_details": customer_details,
        "item_details": item_details,
    }

    # ---- Tahap 1: klaim keranjang + potong stok, satu transaksi singkat ----
    # Klaim lewat UPDATE bersyarat (WHERE status = 'pending'): database menjamin hanya SATU
    # request yang dapat rowcount = 1. Kalau ada checkout lain yang barengan (dobel klik, dua
    # tab, dst) dan sudah keburu mengklaim, yang ini ditolak di sini — sebelum stok disentuh
    # dan sebelum bikin transaksi Midtrans kedua. Cek "status masih pending" di
    # _get_pending_cart() di atas saja tidak cukup, karena selisih waktu antara cek itu dan
    # penulisan ke database cukup buat request lain menyelip.
    klaim = (
        db.query(models.Order)
        .filter(models.Order.id == cart_id, models.Order.status == "pending")
        .update(
            {
                models.Order.status: "menunggu_pembayaran",
                models.Order.payment_method: "midtrans",
                models.Order.midtrans_order_id: order_id,
                models.Order.alamat_id: alamat_id_baru,
            },
            synchronize_session=False,
        )
    )
    if klaim == 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pesanan dari keranjang ini sedang diproses atau sudah dibuat. Cek menu Pesanan Saya.",
        )

    # Kurangi stok tiap item lewat UPDATE atomic (stok = stok - jumlah, DENGAN SYARAT
    # stok >= jumlah, dicek di level SQL) — bukan baca-nilai-di-Python-lalu-tulis-belakangan.
    # Rollback di bawah ikut membatalkan klaim di atas, jadi keranjang balik ke "pending".
    for produk_id, jumlah, nama in items_stok:
        baris_terupdate = (
            db.query(models.Produk)
            .filter(models.Produk.id == produk_id, models.Produk.stok >= jumlah)
            .update({models.Produk.stok: models.Produk.stok - jumlah}, synchronize_session=False)
        )
        if baris_terupdate == 0:
            db.rollback()
            stok_sekarang = db.query(models.Produk.stok).filter(models.Produk.id == produk_id).scalar()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stok {nama} tidak cukup, sisa: {stok_sekarang or 0}",
            )

    # Commit di sini melepas kunci database SEBELUM menunggu Midtrans (bisa beberapa detik),
    # jadi request lain nggak ikut macet menunggu.
    db.commit()

    # ---- Tahap 2: bikin transaksi di Midtrans (di luar transaksi database) ----
    try:
        transaction = snap.create_transaction(param)
    except Exception:
        logger.exception("Midtrans gagal membuat transaksi untuk keranjang %s", cart_id)
        _batalkan_klaim_checkout(db, cart_id, alamat_id_lama, items_stok)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gagal membuat transaksi pembayaran, coba lagi",
        )

    return {
        "snap_token": transaction["token"],
        "redirect_url": transaction["redirect_url"],
        "order_id": order_id,
    }


@router.post("/webhook")
async def midtrans_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()

    order_id = payload.get("order_id")
    status_code = payload.get("status_code")
    gross_amount = payload.get("gross_amount")
    signature_key = payload.get("signature_key")
    transaction_status = payload.get("transaction_status")
    fraud_status = payload.get("fraud_status")

    raw_signature = f"{order_id}{status_code}{gross_amount}{SERVER_KEY}"
    expected_signature = hashlib.sha512(raw_signature.encode()).hexdigest()

    if not signature_key or not hmac.compare_digest(signature_key, expected_signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Signature tidak valid")

    order = db.query(models.Order).filter(models.Order.midtrans_order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order tidak ditemukan")

    if transaction_status in ("capture", "settlement") and fraud_status in (None, "accept"):
        mark_as_paid(db, order)
    elif transaction_status in ("cancel", "deny", "expire"):
        mark_as_cancelled(db, order)
    elif transaction_status == "pending":
        order.status = "menunggu_pembayaran"
        db.commit()

    return {"status": "ok"}


@router.get("/status/{order_id}")
def cek_status_manual(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Buat testing lokal — webhook Midtrans nggak bisa nembak localhost tanpa tunnel (ngrok dll).

    Wajib cek kepemilikan (user_id) DULU sebelum tembak ke Midtrans — kalau nggak, siapa aja
    yang login bisa intip (bahkan memicu perubahan status) pesanan ORANG LAIN cuma dengan
    tau/nebak order_id-nya, karena Midtrans-nya sendiri nggak tau siapa yang lagi nanya."""
    order = (
        db.query(models.Order)
        .filter(models.Order.midtrans_order_id == order_id, models.Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pesanan tidak ditemukan")

    pastikan_midtrans_terkonfigurasi()
    result = core_api.transactions.status(order_id)

    transaction_status = result.get("transaction_status")
    if transaction_status in ("capture", "settlement"):
        mark_as_paid(db, order)
    elif transaction_status in ("cancel", "deny", "expire"):
        mark_as_cancelled(db, order)

    return result
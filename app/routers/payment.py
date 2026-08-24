# app/routers/payment.py
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.midtrans_client import SERVER_KEY, core_api, snap
from app.order_status import mark_as_cancelled, mark_as_paid

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


@router.post("/checkout")
def checkout(
    data: schemas.CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    cart = _get_pending_cart(db, current_user)

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
        cart.alamat_id = alamat.id
    else:
        cart.alamat_id = None

    for item in cart.items:
        if item.jumlah > item.produk.stok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stok {item.produk.nama} tidak cukup, sisa: {item.produk.stok}",
            )

    order_id = f"cakyud-{cart.id}-{secrets.token_hex(4)}"
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
            "name": f"Ongkos Kirim ({cart.metode_pengiriman})",
        })

    param = {
        "transaction_details": {"order_id": order_id, "gross_amount": gross_amount},
        "customer_details": {"first_name": current_user.nama, "email": current_user.email},
        "item_details": item_details,
    }

    transaction = snap.create_transaction(param)

    for item in cart.items:
        item.produk.stok -= item.jumlah

    cart.status = "menunggu_pembayaran"
    cart.payment_method = "midtrans"
    cart.midtrans_order_id = order_id
    db.commit()

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

    if signature_key != expected_signature:
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
    """Buat testing lokal — webhook Midtrans nggak bisa nembak localhost tanpa tunnel (ngrok dll)."""
    result = core_api.transactions.status(order_id)

    order = db.query(models.Order).filter(models.Order.midtrans_order_id == order_id).first()
    if order:
        transaction_status = result.get("transaction_status")
        if transaction_status in ("capture", "settlement"):
            mark_as_paid(db, order)
        elif transaction_status in ("cancel", "deny", "expire"):
            mark_as_cancelled(db, order)

    return result
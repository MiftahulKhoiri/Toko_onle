# app/routers/keranjang.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/keranjang",
    tags=["keranjang"],
)

ONGKIR_DIANTAR = 15000  # ongkir flat rate — ubah manual di sini kalau perlu


def _get_or_create_cart(db: Session, user: models.User) -> models.Order:
    cart = (
        db.query(models.Order)
        .filter(models.Order.user_id == user.id, models.Order.status == "pending")
        .first()
    )
    if not cart:
        cart = models.Order(
            user_id=user.id,
            total_harga=0,
            status="pending",
            metode_pengiriman="diantar",
            ongkir=ONGKIR_DIANTAR,
        )
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def _recalc_total(db: Session, cart: models.Order) -> None:
    subtotal = sum(item.jumlah * item.harga_saat_beli for item in cart.items)
    cart.total_harga = subtotal + cart.ongkir
    db.commit()
    db.refresh(cart)


@router.get("/", response_model=schemas.OrderResponse)
def lihat_keranjang(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _get_or_create_cart(db, current_user)


@router.put("/pengiriman", response_model=schemas.OrderResponse)
def ubah_metode_pengiriman(
    data: schemas.PengirimanUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if data.metode_pengiriman not in ("diantar", "ambil_sendiri"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Metode pengiriman harus 'diantar' atau 'ambil_sendiri'",
        )

    cart = _get_or_create_cart(db, current_user)
    cart.metode_pengiriman = data.metode_pengiriman
    cart.ongkir = ONGKIR_DIANTAR if data.metode_pengiriman == "diantar" else 0
    db.commit()
    _recalc_total(db, cart)
    return cart


@router.post("/items", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def tambah_item(
    item: schemas.OrderItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    produk = db.query(models.Produk).filter(models.Produk.id == item.produk_id).first()
    if not produk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan")

    cart = _get_or_create_cart(db, current_user)

    existing_item = next((i for i in cart.items if i.produk_id == item.produk_id), None)
    jumlah_baru = (existing_item.jumlah if existing_item else 0) + item.jumlah

    if jumlah_baru > produk.stok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stok tidak cukup, sisa stok: {produk.stok}",
        )

    if existing_item:
        existing_item.jumlah = jumlah_baru
        if item.catatan is not None:
            existing_item.catatan = item.catatan
    else:
        existing_item = models.OrderItem(
            order_id=cart.id,
            produk_id=produk.id,
            jumlah=item.jumlah,
            harga_saat_beli=produk.harga,
            catatan=item.catatan,
        )
        db.add(existing_item)

    db.commit()
    _recalc_total(db, cart)
    return cart


@router.put("/items/{item_id}", response_model=schemas.OrderResponse)
def update_item(
    item_id: int,
    item: schemas.OrderItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    cart = _get_or_create_cart(db, current_user)
    db_item = next((i for i in cart.items if i.id == item_id), None)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item tidak ditemukan di keranjang")

    produk = db.query(models.Produk).filter(models.Produk.id == db_item.produk_id).first()
    if not produk:
        # Produk-nya sudah dihapus dari katalog (jarang terjadi, tapi jaga-jaga).
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Produk ini sudah tidak tersedia lagi, hapus item ini dari keranjang",
        )
    if item.jumlah > produk.stok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stok tidak cukup, sisa stok: {produk.stok}",
        )

    # schemas.OrderItemCreate sudah mewajibkan jumlah > 0, jadi nggak perlu cabang "hapus kalau <= 0" lagi.
    # Buat menghapus item, pakai endpoint DELETE /keranjang/items/{item_id}.
    db_item.jumlah = item.jumlah
    if item.catatan is not None:
        db_item.catatan = item.catatan

    db.commit()
    _recalc_total(db, cart)
    return cart


@router.delete("/items/{item_id}", response_model=schemas.OrderResponse)
def hapus_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    cart = _get_or_create_cart(db, current_user)
    db_item = next((i for i in cart.items if i.id == item_id), None)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item tidak ditemukan di keranjang")

    db.delete(db_item)
    db.commit()
    _recalc_total(db, cart)
    return cart


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def kosongkan_keranjang(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    cart = _get_or_create_cart(db, current_user)
    for item in list(cart.items):
        db.delete(item)
    cart.total_harga = 0
    db.commit()
    return None
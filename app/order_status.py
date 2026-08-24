# app/order_status.py
"""
Helper buat ubah status pesanan + urus stok yang direservasi saat checkout.
Dipakai bareng oleh payment.py (webhook/cek manual) dan admin.py (ubah status manual),
biar perilakunya konsisten di semua jalur.
"""
from sqlalchemy.orm import Session

from app import models


def mark_as_paid(db: Session, order: models.Order) -> None:
    # Stok udah dikurangi (direservasi) saat checkout, di sini cuma ubah status.
    if order.status not in ("dibayar", "selesai"):
        order.status = "dibayar"
        db.commit()


def mark_as_cancelled(db: Session, order: models.Order) -> None:
    # Kembalikan stok yang sempat direservasi saat checkout, kecuali order sudah lunas.
    if order.status not in ("batal", "dibayar", "selesai"):
        for item in order.items:
            item.produk.stok += item.jumlah
        order.status = "batal"
        db.commit()
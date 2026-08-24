# app/order_status.py
"""
Helper buat ubah status pesanan: urus stok yang direservasi saat checkout,
dan kirim notifikasi email ke pembeli. Dipakai bareng payment.py (webhook,
cek manual) dan admin.py (ubah status manual) biar konsisten di semua jalur.
"""
from sqlalchemy.orm import Session

from app import models
from app.email_utils import kirim_email_status_pesanan


def mark_as_paid(db: Session, order: models.Order) -> None:
    if order.status not in ("dibayar", "selesai"):
        order.status = "dibayar"
        db.commit()
        kirim_email_status_pesanan(order, "dibayar")


def mark_as_cancelled(db: Session, order: models.Order) -> None:
    if order.status not in ("batal", "dibayar", "selesai"):
        for item in order.items:
            item.produk.stok += item.jumlah
        order.status = "batal"
        db.commit()
        kirim_email_status_pesanan(order, "batal")


def set_status(db: Session, order: models.Order, status_baru: str) -> None:
    """Buat status yang nggak ngubah stok (diproses, selesai, menunggu_pembayaran)."""
    if order.status != status_baru:
        order.status = status_baru
        db.commit()
        if status_baru in ("diproses", "selesai"):
            kirim_email_status_pesanan(order, status_baru)
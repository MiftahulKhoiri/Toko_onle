# app/routers/pesanan.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.midtrans_client import core_api
from app.order_status import mark_as_cancelled, mark_as_paid

router = APIRouter(prefix="/pesanan", tags=["pesanan"])


@router.get("/", response_model=List[schemas.OrderResponse])
def daftar_pesanan_saya(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Order)
        .filter(models.Order.user_id == current_user.id, models.Order.status != "pending")
        .order_by(models.Order.created_at.desc())
        .all()
    )


@router.put("/{order_id}/batalkan", response_model=schemas.OrderResponse)
def batalkan_pesanan_saya(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id, models.Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pesanan tidak ditemukan")

    if order.status != "menunggu_pembayaran":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pesanan ini sudah nggak bisa dibatalkan sendiri. Hubungi penjual kalau perlu bantuan.",
        )

    if order.midtrans_order_id:
        try:
            # cek dulu status asli di Midtrans, jaga-jaga kalau ternyata baru aja dibayar
            hasil = core_api.transactions.status(order.midtrans_order_id)
            if hasil.get("transaction_status") in ("capture", "settlement"):
                mark_as_paid(db, order)
                db.refresh(order)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pesanan ini ternyata sudah dibayar, nggak bisa dibatalkan lagi.",
                )
            core_api.transactions.cancel(order.midtrans_order_id)
        except HTTPException:
            raise
        except Exception:
            pass  # kalau Midtrans nggak bisa diajak konfirmasi, lanjut batalkan lokal aja

    mark_as_cancelled(db, order)
    db.refresh(order)
    return order
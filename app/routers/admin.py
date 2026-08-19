# app/routers/admin.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/pesanan", response_model=List[schemas.OrderResponse])
def list_semua_pesanan(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    return (
        db.query(models.Order)
        .filter(models.Order.status != "pending")  # keranjang yang belum checkout nggak usah tampil
        .order_by(models.Order.created_at.desc())
        .all()
    )


@router.put("/pesanan/{order_id}/status", response_model=schemas.OrderResponse)
def update_status_pesanan(
    order_id: int,
    data: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pesanan tidak ditemukan")
    order.status = data.status
    db.commit()
    db.refresh(order)
    return order
# app/routers/pesanan.py
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user

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
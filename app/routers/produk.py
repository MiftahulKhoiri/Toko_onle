# app/routers/produk.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/produk",
    tags=["produk"],
)


@router.get("/", response_model=List[schemas.ProdukResponse])
def list_produk(
    kategori: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(models.Produk)
    if kategori:
        query = query.filter(models.Produk.kategori == kategori)
    return query.offset(skip).limit(limit).all()


@router.get("/{produk_id}", response_model=schemas.ProdukResponse)
def get_produk(produk_id: int, db: Session = Depends(get_db)):
    produk = db.query(models.Produk).filter(models.Produk.id == produk_id).first()
    if not produk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan")
    return produk


@router.post("/", response_model=schemas.ProdukResponse, status_code=status.HTTP_201_CREATED)
def create_produk(produk: schemas.ProdukCreate, db: Session = Depends(get_db)):
    db_produk = models.Produk(**produk.model_dump())
    db.add(db_produk)
    db.commit()
    db.refresh(db_produk)
    return db_produk


@router.put("/{produk_id}", response_model=schemas.ProdukResponse)
def update_produk(produk_id: int, produk: schemas.ProdukUpdate, db: Session = Depends(get_db)):
    db_produk = db.query(models.Produk).filter(models.Produk.id == produk_id).first()
    if not db_produk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan")

    data = produk.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(db_produk, field, value)

    db.commit()
    db.refresh(db_produk)
    return db_produk


@router.delete("/{produk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_produk(produk_id: int, db: Session = Depends(get_db)):
    db_produk = db.query(models.Produk).filter(models.Produk.id == produk_id).first()
    if not db_produk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan")

    db.delete(db_produk)
    db.commit()
    return None
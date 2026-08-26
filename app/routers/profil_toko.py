# app/routers/profil_toko.py
"""
Endpoint buat Profil Toko (halaman landing publik yang dibuka lewat klik logo di navbar)
dan Testimoni pelanggan yang ditampilkan di halaman itu.

ProfilToko cuma punya 1 baris data (semacam "pengaturan toko") — dibuat otomatis kalau
belum ada, mirip pola _get_or_create_cart di keranjang.py.
"""
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_admin

router = APIRouter(tags=["profil_toko"])

UPLOAD_DIR_TOKO = "app/static/img/toko"
EKSTENSI_DIIZINKAN = {".jpg", ".jpeg", ".png", ".webp"}
UKURAN_MAKS = 5 * 1024 * 1024  # 5MB

os.makedirs(UPLOAD_DIR_TOKO, exist_ok=True)


def _get_or_create_profil(db: Session) -> models.ProfilToko:
    profil = db.query(models.ProfilToko).first()
    if not profil:
        profil = models.ProfilToko(nama_toko="Salome Cakyud", is_buka=True)
        db.add(profil)
        db.commit()
        db.refresh(profil)
    return profil


# ---------- Profil Toko ----------

@router.get("/profil-toko", response_model=schemas.ProfilTokoResponse)
def get_profil_toko(db: Session = Depends(get_db)):
    return _get_or_create_profil(db)


@router.put("/profil-toko", response_model=schemas.ProfilTokoResponse)
def update_profil_toko(
    data: schemas.ProfilTokoUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    profil = _get_or_create_profil(db)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profil, field, value)
    db.commit()
    db.refresh(profil)
    return profil


@router.post("/profil-toko/upload-gambar")
async def upload_gambar_toko(
    file: UploadFile = File(...),
    _: models.User = Depends(get_current_admin),
):
    """Dipakai bareng buat logo, banner, dan foto testimoni — biar nggak dobel-dobel endpoint upload."""
    ekstensi = os.path.splitext(file.filename or "")[1].lower()
    if ekstensi not in EKSTENSI_DIIZINKAN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format foto harus jpg, jpeg, png, atau webp",
        )

    isi_file = await file.read()
    if len(isi_file) > UKURAN_MAKS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ukuran foto maksimal 5MB")

    nama_file = f"{uuid.uuid4().hex}{ekstensi}"
    with open(os.path.join(UPLOAD_DIR_TOKO, nama_file), "wb") as f:
        f.write(isi_file)

    return {"url": f"/static/img/toko/{nama_file}"}


# ---------- Testimoni ----------

@router.get("/testimoni", response_model=List[schemas.TestimoniResponse])
def list_testimoni_publik(db: Session = Depends(get_db)):
    """Publik — cuma testimoni yang ditampilkan=True, buat halaman profil toko."""
    return (
        db.query(models.Testimoni)
        .filter(models.Testimoni.ditampilkan == True)  # noqa: E712
        .order_by(models.Testimoni.created_at.desc())
        .limit(50)
        .all()
    )


@router.get("/testimoni/semua", response_model=List[schemas.TestimoniResponse])
def list_testimoni_admin(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    """Khusus admin — termasuk yang lagi disembunyikan, buat panel Kelola Profil Toko."""
    return db.query(models.Testimoni).order_by(models.Testimoni.created_at.desc()).all()


@router.post("/testimoni", response_model=schemas.TestimoniResponse, status_code=status.HTTP_201_CREATED)
def tambah_testimoni(
    data: schemas.TestimoniCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    testimoni = models.Testimoni(**data.model_dump())
    db.add(testimoni)
    db.commit()
    db.refresh(testimoni)
    return testimoni


@router.put("/testimoni/{testimoni_id}", response_model=schemas.TestimoniResponse)
def ubah_testimoni(
    testimoni_id: int,
    data: schemas.TestimoniUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    testimoni = db.query(models.Testimoni).filter(models.Testimoni.id == testimoni_id).first()
    if not testimoni:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Testimoni tidak ditemukan")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(testimoni, field, value)
    db.commit()
    db.refresh(testimoni)
    return testimoni


@router.delete("/testimoni/{testimoni_id}", status_code=status.HTTP_204_NO_CONTENT)
def hapus_testimoni(
    testimoni_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    testimoni = db.query(models.Testimoni).filter(models.Testimoni.id == testimoni_id).first()
    if not testimoni:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Testimoni tidak ditemukan")
    db.delete(testimoni)
    db.commit()
    return None
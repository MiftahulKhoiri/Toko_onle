# app/routers/alamat.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/alamat", tags=["alamat"])


@router.get("/", response_model=List[schemas.AlamatResponse])
def daftar_alamat(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Alamat)
        .filter(models.Alamat.user_id == current_user.id)
        .order_by(models.Alamat.is_default.desc(), models.Alamat.created_at.desc())
        .all()
    )


@router.post("/", response_model=schemas.AlamatResponse, status_code=status.HTTP_201_CREATED)
def tambah_alamat(
    data: schemas.AlamatCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    jumlah_alamat = db.query(models.Alamat).filter(models.Alamat.user_id == current_user.id).count()

    alamat = models.Alamat(
        user_id=current_user.id,
        label=data.label or "Rumah",
        alamat_jalan=data.alamat_jalan,
        kelurahan=data.kelurahan,
        kecamatan=data.kecamatan,
        kota=data.kota,
        provinsi=data.provinsi,
        kode_pos=data.kode_pos,
        is_default=(jumlah_alamat == 0),  # alamat pertama otomatis jadi utama
    )
    db.add(alamat)
    db.commit()
    db.refresh(alamat)
    return alamat


@router.put("/{alamat_id}", response_model=schemas.AlamatResponse)
def ubah_alamat(
    alamat_id: int,
    data: schemas.AlamatCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    alamat = (
        db.query(models.Alamat)
        .filter(models.Alamat.id == alamat_id, models.Alamat.user_id == current_user.id)
        .first()
    )
    if not alamat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alamat tidak ditemukan")

    alamat.label = data.label or alamat.label
    alamat.alamat_jalan = data.alamat_jalan
    alamat.kelurahan = data.kelurahan
    alamat.kecamatan = data.kecamatan
    alamat.kota = data.kota
    alamat.provinsi = data.provinsi
    alamat.kode_pos = data.kode_pos

    db.commit()
    db.refresh(alamat)
    return alamat


@router.put("/{alamat_id}/utama", response_model=schemas.AlamatResponse)
def jadikan_utama(
    alamat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    alamat = (
        db.query(models.Alamat)
        .filter(models.Alamat.id == alamat_id, models.Alamat.user_id == current_user.id)
        .first()
    )
    if not alamat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alamat tidak ditemukan")

    db.query(models.Alamat).filter(models.Alamat.user_id == current_user.id).update({"is_default": False})
    alamat.is_default = True
    db.commit()
    db.refresh(alamat)
    return alamat


@router.delete("/{alamat_id}", status_code=status.HTTP_204_NO_CONTENT)
def hapus_alamat(
    alamat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    alamat = (
        db.query(models.Alamat)
        .filter(models.Alamat.id == alamat_id, models.Alamat.user_id == current_user.id)
        .first()
    )
    if not alamat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alamat tidak ditemukan")

    was_default = alamat.is_default
    db.delete(alamat)
    db.commit()

    if was_default:
        alamat_lain = (
            db.query(models.Alamat)
            .filter(models.Alamat.user_id == current_user.id)
            .order_by(models.Alamat.created_at.desc())
            .first()
        )
        if alamat_lain:
            alamat_lain.is_default = True
            db.commit()

    return None
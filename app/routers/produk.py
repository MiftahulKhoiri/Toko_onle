# app/routers/produk.py
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_admin

router = APIRouter(prefix="/produk", tags=["produk"])

UPLOAD_DIR = "app/static/img/produk"
EKSTENSI_DIIZINKAN = {".jpg", ".jpeg", ".png", ".webp"}
UKURAN_MAKS = 5 * 1024 * 1024  # 5MB

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _hapus_file_foto(gambar_url: Optional[str]) -> None:
    """Hapus file foto lama dari disk — cuma kalau itu file upload lokal, bukan URL luar."""
    if not gambar_url or not gambar_url.startswith("/static/img/produk/"):
        return
    path_file = os.path.join(UPLOAD_DIR, os.path.basename(gambar_url))
    if os.path.isfile(path_file):
        try:
            os.remove(path_file)
        except OSError:
            pass


@router.post("/upload-foto")
async def upload_foto(
    file: UploadFile = File(...),
    _: models.User = Depends(get_current_admin),
):
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
    with open(os.path.join(UPLOAD_DIR, nama_file), "wb") as f:
        f.write(isi_file)

    return {"gambar_url": f"/static/img/produk/{nama_file}"}


@router.get("/", response_model=List[schemas.ProdukResponse])
def list_produk(
    kategori: Optional[str] = None,
    urutan: str = "semua",
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    """
    urutan:
      - "semua"   -> urutan katalog apa adanya (id ascending)
      - "terbaru" -> produk yang baru ditambahkan duluan (created_at descending)
      - "terlaris" -> dihitung dari total jumlah terjual di pesanan yang statusnya
                      sudah lewat pembayaran (dibayar/diproses/selesai). Produk yang
                      belum pernah laku tetap ikut tampil, di urutan paling belakang.
    """
    query = db.query(models.Produk)
    if kategori:
        query = query.filter(models.Produk.kategori == kategori)

    if urutan == "terlaris":
        subq = (
            db.query(
                models.OrderItem.produk_id.label("produk_id"),
                func.sum(models.OrderItem.jumlah).label("total_terjual"),
            )
            .join(models.Order, models.OrderItem.order_id == models.Order.id)
            .filter(models.Order.status.in_(["dibayar", "diproses", "selesai"]))
            .group_by(models.OrderItem.produk_id)
            .subquery()
        )
        query = query.outerjoin(subq, models.Produk.id == subq.c.produk_id).order_by(
            func.coalesce(subq.c.total_terjual, 0).desc(),
            models.Produk.id.desc(),
        )
    elif urutan == "terbaru":
        query = query.order_by(models.Produk.created_at.desc())
    else:
        query = query.order_by(models.Produk.id.asc())

    return query.offset(skip).limit(limit).all()


@router.get("/{produk_id}", response_model=schemas.ProdukResponse)
def get_produk(produk_id: int, db: Session = Depends(get_db)):
    produk = db.query(models.Produk).filter(models.Produk.id == produk_id).first()
    if not produk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan")
    return produk


@router.post("/", response_model=schemas.ProdukResponse, status_code=status.HTTP_201_CREATED)
def create_produk(
    produk: schemas.ProdukCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    db_produk = models.Produk(**produk.model_dump())
    db.add(db_produk)
    db.commit()
    db.refresh(db_produk)
    return db_produk


@router.put("/{produk_id}", response_model=schemas.ProdukResponse)
def update_produk(
    produk_id: int,
    produk: schemas.ProdukUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    db_produk = db.query(models.Produk).filter(models.Produk.id == produk_id).first()
    if not db_produk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan")

    data = produk.model_dump(exclude_unset=True)
    foto_lama = db_produk.gambar_url
    ganti_foto = "gambar_url" in data and data["gambar_url"] != foto_lama

    for field, value in data.items():
        setattr(db_produk, field, value)

    db.commit()
    db.refresh(db_produk)

    if ganti_foto:
        _hapus_file_foto(foto_lama)

    return db_produk


@router.delete("/{produk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_produk(
    produk_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    db_produk = db.query(models.Produk).filter(models.Produk.id == produk_id).first()
    if not db_produk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan")

    pernah_dipesan = (
        db.query(models.OrderItem).filter(models.OrderItem.produk_id == produk_id).first()
    )
    if pernah_dipesan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Produk ini sudah pernah dipesan/masuk keranjang pembeli, jadi nggak bisa "
                "dihapus permanen (biar riwayat pesanan nggak rusak). Set stok ke 0 dan/atau "
                "matikan status Ready lewat menu Edit kalau mau menyembunyikannya dari pembeli."
            ),
        )

    foto = db_produk.gambar_url
    db.delete(db_produk)
    db.commit()
    _hapus_file_foto(foto)
    return None
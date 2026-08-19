# app/schemas.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr


# ---------- Produk ----------
class ProdukBase(BaseModel):
    nama: str
    deskripsi: Optional[str] = None
    harga: float
    stok: int = 0
    kategori: Optional[str] = None
    gambar_url: Optional[str] = None


class ProdukCreate(ProdukBase):
    pass


class ProdukUpdate(BaseModel):
    nama: Optional[str] = None
    deskripsi: Optional[str] = None
    harga: Optional[float] = None
    stok: Optional[int] = None
    kategori: Optional[str] = None
    gambar_url: Optional[str] = None


class ProdukResponse(ProdukBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ---------- User ----------
class UserBase(BaseModel):
    nama: str
    email: EmailStr


class UserCreate(UserBase):
    password: str  # plain text masuk sini, di-hash sebelum simpan ke DB


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    # sengaja TIDAK ada hashed_password di sini


# ---------- OrderItem ----------
class OrderItemCreate(BaseModel):
    produk_id: int
    jumlah: int = 1


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produk_id: int
    jumlah: int
    harga_saat_beli: float
    produk: Optional[ProdukResponse] = None


# ---------- Order ----------
class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    payment_method: Optional[str] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    total_harga: float
    status: str
    payment_method: Optional[str] = None
    created_at: datetime
    items: List[OrderItemResponse] = []
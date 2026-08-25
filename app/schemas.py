# app/schemas.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Produk ----------
class ProdukBase(BaseModel):
    nama: str = Field(..., min_length=1, max_length=100)
    deskripsi: Optional[str] = None
    harga: float = Field(..., ge=0)
    stok: int = Field(0, ge=0)
    kategori: Optional[str] = None
    gambar_url: Optional[str] = None
    is_ready: bool = True
    is_po: bool = False


class ProdukCreate(ProdukBase):
    pass


class ProdukUpdate(BaseModel):
    nama: Optional[str] = Field(None, min_length=1, max_length=100)
    deskripsi: Optional[str] = None
    harga: Optional[float] = Field(None, ge=0)
    stok: Optional[int] = Field(None, ge=0)
    kategori: Optional[str] = None
    gambar_url: Optional[str] = None
    is_ready: Optional[bool] = None
    is_po: Optional[bool] = None


class ProdukResponse(ProdukBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ---------- User ----------
class UserBase(BaseModel):
    nama: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    telepon: Optional[str] = None
    alamat_jalan: Optional[str] = None
    kelurahan: Optional[str] = None
    kecamatan: Optional[str] = None
    kota: Optional[str] = None
    provinsi: Optional[str] = None
    kode_pos: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    nama: Optional[str] = Field(None, min_length=1, max_length=100)
    telepon: Optional[str] = None
    alamat_jalan: Optional[str] = None
    kelurahan: Optional[str] = None
    kecamatan: Optional[str] = None
    kota: Optional[str] = None
    provinsi: Optional[str] = None
    kode_pos: Optional[str] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_admin: bool = False
    foto_url: Optional[str] = None
    created_at: datetime


# ---------- Auth ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


# ---------- Alamat ----------
class AlamatCreate(BaseModel):
    label: Optional[str] = Field("Rumah", max_length=50)
    alamat_jalan: str = Field(..., min_length=1)
    kelurahan: Optional[str] = Field(None, max_length=100)
    kecamatan: Optional[str] = Field(None, max_length=100)
    kota: str = Field(..., min_length=1, max_length=100)
    provinsi: Optional[str] = Field(None, max_length=100)
    kode_pos: Optional[str] = Field(None, max_length=10)


class AlamatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    alamat_jalan: Optional[str] = None
    kelurahan: Optional[str] = None
    kecamatan: Optional[str] = None
    kota: Optional[str] = None
    provinsi: Optional[str] = None
    kode_pos: Optional[str] = None
    is_default: bool


# ---------- OrderItem ----------
class OrderItemCreate(BaseModel):
    produk_id: int
    jumlah: int = Field(1, gt=0)
    catatan: Optional[str] = Field(None, max_length=255)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produk_id: int
    jumlah: int
    harga_saat_beli: float
    catatan: Optional[str] = None
    produk: Optional[ProdukResponse] = None


# ---------- Pengiriman ----------
class PengirimanUpdate(BaseModel):
    metode_pengiriman: str


# ---------- Checkout ----------
class CheckoutRequest(BaseModel):
    alamat_id: Optional[int] = None


# ---------- Order ----------
class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    payment_method: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    status: str


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    total_harga: float
    status: str
    payment_method: Optional[str] = None
    metode_pengiriman: str = "diantar"
    ongkir: float = 0
    created_at: datetime
    items: List[OrderItemResponse] = []
    user: Optional[UserResponse] = None
    alamat: Optional[AlamatResponse] = None
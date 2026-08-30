# app/schemas.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


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
def _normalisasi_telepon(v: str) -> str:
    """Rapikan format nomor HP ke '08xxxxxxxxxx' — orang bisa ngetik pakai
    +62, 62, atau spasi/strip di antara angka, semuanya disamakan biar
    nggak ada 2 akun beda format buat nomor yang sama."""
    if v is None:
        return v
    v = v.strip().replace(" ", "").replace("-", "")
    if v.startswith("+62"):
        v = "0" + v[3:]
    elif v.startswith("62"):
        v = "0" + v[2:]
    if not v.isdigit() or not v.startswith("0") or not (9 <= len(v) <= 15):
        raise ValueError("Nomor HP tidak valid, contoh: 081234567890")
    return v


class UserBase(BaseModel):
    nama: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    telepon: Optional[str] = None
    alamat_jalan: Optional[str] = None
    kelurahan: Optional[str] = None
    kecamatan: Optional[str] = None
    kota: Optional[str] = None
    provinsi: Optional[str] = None
    kode_pos: Optional[str] = None


class UserCreate(BaseModel):
    """Daftar pakai email — email & password tetap wajib di jalur ini."""
    nama: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    telepon: Optional[str] = None
    alamat_jalan: Optional[str] = None
    kelurahan: Optional[str] = None
    kecamatan: Optional[str] = None
    kota: Optional[str] = None
    provinsi: Optional[str] = None
    kode_pos: Optional[str] = None


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
    daftar_via: str = "email"
    created_at: datetime


# ---------- Daftar cepat: No. Telepon ----------
class TeleponRegister(BaseModel):
    nama: str = Field(..., min_length=1, max_length=100)
    telepon: str = Field(..., min_length=9, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("telepon")
    @classmethod
    def _validasi_telepon(cls, v):
        return _normalisasi_telepon(v)


class TeleponLogin(BaseModel):
    telepon: str
    password: str

    @field_validator("telepon")
    @classmethod
    def _validasi_telepon(cls, v):
        return _normalisasi_telepon(v)


# ---------- Daftar cepat: Google & Facebook ----------
class GoogleLogin(BaseModel):
    """credential = ID token JWT yang dikirim tombol Google Identity Services
    di browser. Server WAJIB verifikasi ulang token ini ke Google (lihat
    app/social_auth.py) — nggak boleh dipercaya mentah-mentah dari client."""
    credential: str = Field(..., min_length=1)


class FacebookLogin(BaseModel):
    """access_token = token yang dikirim Facebook JS SDK (FB.login) di
    browser. Server WAJIB verifikasi ulang token ini ke Facebook Graph API
    (lihat app/social_auth.py) — nggak boleh dipercaya mentah-mentah dari client."""
    access_token: str = Field(..., min_length=1)


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


# ---------- Profil Toko ----------
def _cek_format_url(v: Optional[str]) -> Optional[str]:
    """Rapikan URL opsional — kalau lupa ketik http(s):// di depan, tambahin otomatis
    daripada nolak. Ini juga sekalian nutup celah URI aneh (mis. javascript:...) karena
    hasil akhirnya selalu dipaksa berawalan https://."""
    if v is None:
        return None
    v = v.strip()
    if not v:
        return None
    if not (v.startswith("http://") or v.startswith("https://")):
        v = f"https://{v}"
    return v


class ProfilTokoBase(BaseModel):
    nama_toko: str = Field(..., min_length=1, max_length=100)
    tagline: Optional[str] = Field(None, max_length=150)
    deskripsi: Optional[str] = Field(None, max_length=3000)
    alamat: Optional[str] = Field(None, max_length=500)
    maps_embed_url: Optional[str] = None
    jam_operasional: Optional[str] = Field(None, max_length=100)
    is_buka: bool = True
    kontak_wa: Optional[str] = Field(None, max_length=20)
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    gofood_url: Optional[str] = None
    grabfood_url: Optional[str] = None
    shopeefood_url: Optional[str] = None
    instagram_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    facebook_url: Optional[str] = None

    @field_validator(
        "maps_embed_url", "gofood_url", "grabfood_url", "shopeefood_url",
        "instagram_url", "tiktok_url", "facebook_url",
    )
    @classmethod
    def _validasi_url(cls, v):
        return _cek_format_url(v)


class ProfilTokoUpdate(BaseModel):
    nama_toko: Optional[str] = Field(None, min_length=1, max_length=100)
    tagline: Optional[str] = Field(None, max_length=150)
    deskripsi: Optional[str] = Field(None, max_length=3000)
    alamat: Optional[str] = Field(None, max_length=500)
    maps_embed_url: Optional[str] = None
    jam_operasional: Optional[str] = Field(None, max_length=100)
    is_buka: Optional[bool] = None
    kontak_wa: Optional[str] = Field(None, max_length=20)
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    gofood_url: Optional[str] = None
    grabfood_url: Optional[str] = None
    shopeefood_url: Optional[str] = None
    instagram_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    facebook_url: Optional[str] = None

    @field_validator(
        "maps_embed_url", "gofood_url", "grabfood_url", "shopeefood_url",
        "instagram_url", "tiktok_url", "facebook_url",
    )
    @classmethod
    def _validasi_url(cls, v):
        return _cek_format_url(v)


class ProfilTokoResponse(ProfilTokoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ---------- Testimoni ----------
class TestimoniBase(BaseModel):
    nama_pelanggan: str = Field(..., min_length=1, max_length=100)
    rating: int = Field(..., ge=1, le=5)
    ulasan: str = Field(..., min_length=1, max_length=500)
    foto_url: Optional[str] = None
    ditampilkan: bool = True


class TestimoniCreate(TestimoniBase):
    pass


class TestimoniUpdate(BaseModel):
    nama_pelanggan: Optional[str] = Field(None, min_length=1, max_length=100)
    rating: Optional[int] = Field(None, ge=1, le=5)
    ulasan: Optional[str] = Field(None, min_length=1, max_length=500)
    foto_url: Optional[str] = None
    ditampilkan: Optional[bool] = None


class TestimoniKirim(BaseModel):
    """Skema ulasan yang dikirim PEMBELI sendiri (bukan admin) — sengaja nggak ada
    nama_pelanggan/ditampilkan di sini, dua-duanya ditentukan server: nama_pelanggan
    diambil dari akun yang login, ditampilkan dipaksa False sampai admin approve."""
    rating: int = Field(..., ge=1, le=5)
    ulasan: str = Field(..., min_length=1, max_length=500)
    foto_url: Optional[str] = None


class TestimoniResponse(TestimoniBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    created_at: datetime
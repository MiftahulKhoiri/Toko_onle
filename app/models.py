# app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Produk(Base):
    __tablename__ = "produk"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(100), nullable=False)
    deskripsi = Column(Text, nullable=True)
    harga = Column(Float, nullable=False)
    stok = Column(Integer, default=0)
    kategori = Column(String(50), nullable=True)
    gambar_url = Column(String(255), nullable=True)
    is_ready = Column(Boolean, default=True)
    is_po = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order_items = relationship("OrderItem", back_populates="produk")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(100), nullable=False)

    # Email & password sekarang boleh kosong karena akun bisa dibuat lewat
    # Google/Facebook/No. HP yang nggak selalu punya salah satu dari keduanya.
    # Tiap user WAJIB punya minimal satu identitas login (email, telepon, google_sub,
    # atau facebook_id) — ini dijaga di kode router auth, bukan di level kolom.
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    telepon = Column(String(20), unique=True, index=True, nullable=True)
    foto_url = Column(String(255), nullable=True)  # foto profil, cuma 1

    # Login sosial — diisi otomatis pas pertama kali daftar/masuk lewat provider terkait
    google_sub = Column(String(255), unique=True, index=True, nullable=True)
    facebook_id = Column(String(255), unique=True, index=True, nullable=True)
    # Catatan cara akun ini pertama kali dibuat: "email" | "telepon" | "google" | "facebook"
    daftar_via = Column(String(20), nullable=False, default="email")

    # Reset password: nyimpen HASH token-nya doang (bukan token mentah) — kalau database
    # sampai bocor, isinya nggak langsung bisa dipakai buat reset password akun siapa aja.
    # Ditimpa (overwrite) tiap kali user minta link baru, jadi otomatis bikin link lama
    # nggak berlaku lagi. Lihat app/security.py (buat_reset_token) & routers/auth.py.
    reset_token_hash = Column(String(64), nullable=True, index=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)

    # --- Alamat lama di profil (dipertahankan, sudah nggak dipakai di alur checkout baru) ---
    alamat_jalan = Column(Text, nullable=True)
    kelurahan = Column(String(100), nullable=True)
    kecamatan = Column(String(100), nullable=True)
    kota = Column(String(100), nullable=True)
    provinsi = Column(String(100), nullable=True)
    kode_pos = Column(String(10), nullable=True)

    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    orders = relationship("Order", back_populates="user")
    alamat_list = relationship("Alamat", back_populates="user")
    testimoni_list = relationship("Testimoni", back_populates="user")


class Alamat(Base):
    __tablename__ = "alamat"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    label = Column(String(50), default="Rumah")
    alamat_jalan = Column(Text, nullable=True)
    kelurahan = Column(String(100), nullable=True)
    kecamatan = Column(String(100), nullable=True)
    kota = Column(String(100), nullable=True)
    provinsi = Column(String(100), nullable=True)
    kode_pos = Column(String(10), nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="alamat_list")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alamat_id = Column(Integer, ForeignKey("alamat.id"), nullable=True)
    total_harga = Column(Float, nullable=False)
    status = Column(String(20), default="menunggu_pembayaran")
    payment_method = Column(String(30), nullable=True)
    metode_pengiriman = Column(String(20), default="diantar")
    ongkir = Column(Float, default=0)
    midtrans_order_id = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="orders")
    alamat = relationship("Alamat")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    produk_id = Column(Integer, ForeignKey("produk.id"), nullable=False)
    jumlah = Column(Integer, nullable=False)
    harga_saat_beli = Column(Float, nullable=False)
    catatan = Column(String(255), nullable=True)

    order = relationship("Order", back_populates="items")
    produk = relationship("Produk", back_populates="order_items")


class ProfilToko(Base):
    __tablename__ = "profil_toko"

    id = Column(Integer, primary_key=True, index=True)
    nama_toko = Column(String(100), nullable=False, default="Toko Salome Cakyud")
    tagline = Column(String(150), nullable=True)
    deskripsi = Column(Text, nullable=True)
    alamat = Column(String(500), nullable=True)
    maps_embed_url = Column(Text, nullable=True)
    jam_operasional = Column(String(100), nullable=True)
    is_buka = Column(Boolean, default=True)
    kontak_wa = Column(String(20), nullable=True)
    logo_url = Column(String(255), nullable=True)
    banner_url = Column(String(255), nullable=True)
    gofood_url = Column(Text, nullable=True)
    grabfood_url = Column(Text, nullable=True)
    shopeefood_url = Column(Text, nullable=True)
    instagram_url = Column(Text, nullable=True)
    tiktok_url = Column(Text, nullable=True)
    facebook_url = Column(Text, nullable=True)


class Testimoni(Base):
    __tablename__ = "testimoni"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    nama_pelanggan = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False)
    ulasan = Column(Text, nullable=False)
    foto_url = Column(String(255), nullable=True)
    ditampilkan = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="testimoni_list")
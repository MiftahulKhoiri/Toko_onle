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
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    telepon = Column(String(20), nullable=True)

    # --- Alamat lama di profil (dipertahankan biar data lama nggak hilang, sudah nggak dipakai di alur checkout baru) ---
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


class Alamat(Base):
    __tablename__ = "alamat"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    label = Column(String(50), default="Rumah")  # mis: "Rumah", "Kantor"
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
    total_harga = Column(Float, nullable=False, default=0)
    status = Column(String(20), default="pending")
    payment_method = Column(String(50), nullable=True)
    midtrans_order_id = Column(String(100), unique=True, nullable=True, index=True)

    metode_pengiriman = Column(String(20), default="diantar")
    ongkir = Column(Float, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="orders")
    alamat = relationship("Alamat")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    produk_id = Column(Integer, ForeignKey("produk.id"), nullable=False)
    jumlah = Column(Integer, nullable=False, default=1)
    harga_saat_beli = Column(Float, nullable=False)
    catatan = Column(String(255), nullable=True)

    order = relationship("Order", back_populates="items")
    produk = relationship("Produk", back_populates="order_items")
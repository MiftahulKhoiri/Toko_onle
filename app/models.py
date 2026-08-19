# app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
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
    kategori = Column(String(50), nullable=True)  # mis. "bakso", "minuman"
    gambar_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order_items = relationship("OrderItem", back_populates="produk")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    orders = relationship("Order", back_populates="user")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_harga = Column(Float, nullable=False, default=0)
    status = Column(String(20), default="pending")  # pending, dibayar, diproses, selesai, batal
    payment_method = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    produk_id = Column(Integer, ForeignKey("produk.id"), nullable=False)
    jumlah = Column(Integer, nullable=False, default=1)
    harga_saat_beli = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    produk = relationship("Produk", back_populates="order_items")
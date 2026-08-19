# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import models
from app.database import engine
from app.routers import produk, auth, keranjang, payment, pages, admin

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Toko Salome Cakyud")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages.router)
app.include_router(produk.router)
app.include_router(auth.router)
app.include_router(keranjang.router)
app.include_router(payment.router)
app.include_router(admin.router)
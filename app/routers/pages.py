# app/routers/pages.py
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    produk_list = db.query(models.Produk).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "nama_toko": "Salome Cakyud", "produk_list": produk_list},
    )


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "nama_toko": "Salome Cakyud"})


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "nama_toko": "Salome Cakyud"})


@router.get("/keranjang-saya")
def keranjang_page(request: Request):
    return templates.TemplateResponse("keranjang.html", {"request": request, "nama_toko": "Salome Cakyud"})
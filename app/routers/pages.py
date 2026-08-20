# app/routers/pages.py
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    produk_list = db.query(models.Produk).all()
    return templates.TemplateResponse(
        request, "index.html", {"nama_toko": "Salome Cakyud", "produk_list": produk_list}
    )


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"nama_toko": "Salome Cakyud"})


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"nama_toko": "Salome Cakyud"})


@router.get("/keranjang-saya")
def keranjang_page(request: Request):
    return templates.TemplateResponse(request, "keranjang.html", {"nama_toko": "Salome Cakyud"})


@router.get("/panel-admin")
def admin_dashboard_page(request: Request):
    return templates.TemplateResponse(request, "admin_dashboard.html", {"nama_toko": "Salome Cakyud"})


@router.get("/panel-admin/pesanan")
def admin_pesanan_page(request: Request):
    return templates.TemplateResponse(request, "admin_pesanan.html", {"nama_toko": "Salome Cakyud"})

@router.get("/profil", response_class=HTMLResponse)
def halaman_profil(request: Request):
    return templates.TemplateResponse("profil.html", {"request": request, "nama_toko": NAMA_TOKO})

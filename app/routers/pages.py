# app/routers/pages.py
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")

NAMA_TOKO = "Salome Cakyud"


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"nama_toko": NAMA_TOKO}
    )


@router.get("/menu/{produk_id}")
def detail_produk_page(produk_id: int, request: Request, db: Session = Depends(get_db)):
    produk = db.query(models.Produk).filter(models.Produk.id == produk_id).first()
    return templates.TemplateResponse(
        request, "detail_produk.html", {"nama_toko": NAMA_TOKO, "produk": produk}
    )


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request, "login.html", {"nama_toko": NAMA_TOKO}
    )


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request, "register.html", {"nama_toko": NAMA_TOKO}
    )


@router.get("/keranjang-saya")
def keranjang_page(request: Request):
    return templates.TemplateResponse(
        request, "keranjang.html", {"nama_toko": NAMA_TOKO}
    )


@router.get("/checkout/alamat")
def checkout_alamat_page(request: Request):
    return templates.TemplateResponse(
        request, "checkout_alamat.html", {"nama_toko": NAMA_TOKO}
    )


@router.get("/pesanan-saya")
def pesanan_saya_page(request: Request):
    return templates.TemplateResponse(
        request, "pesanan_saya.html", {"nama_toko": NAMA_TOKO}
    )


@router.get("/panel-admin")
def admin_dashboard_page(request: Request):
    return templates.TemplateResponse(
        request, "admin_dashboard.html", {"nama_toko": NAMA_TOKO}
    )


@router.get("/panel-admin/pesanan")
def admin_pesanan_page(request: Request):
    return templates.TemplateResponse(
        request, "admin_pesanan.html", {"nama_toko": NAMA_TOKO}
    )


@router.get("/panel-admin/profil-toko")
def admin_profil_toko_page(request: Request):
    return templates.TemplateResponse(
        request, "admin_profil_toko.html", {"nama_toko": NAMA_TOKO}
    )


@router.get("/profil", response_class=HTMLResponse)
def halaman_profil(request: Request):
    return templates.TemplateResponse(
        request, "profil.html", {"nama_toko": NAMA_TOKO}
    )


@router.get("/profil-toko")
def profil_toko_page(request: Request):
    return templates.TemplateResponse(
        request, "profil_toko.html", {"nama_toko": NAMA_TOKO}
    )
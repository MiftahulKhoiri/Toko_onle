# app/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import models
from app.database import engine
from app.routers import produk, auth

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Toko Salome Cakyud")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(produk.router)
app.include_router(auth.router)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "nama_toko": "Salome Cakyud"})
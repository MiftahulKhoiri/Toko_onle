# app/routers/payment.py
import hashlib
import os
import secrets

import midtransclient
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/payment", tags=["payment"])

IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "False") == "True"
SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY")
CLIENT_KEY = os.getenv("MIDTRANS_CLIENT_KEY")

snap = midtransclient.Snap(is_production=IS_PRODUCTION, server_key=SERVER_KEY, client_key=CLIENT_KEY)
core_api = midtransclient.CoreApi(is_production=IS_PRODUCTION, server_key=SERVER_KEY, client_key=CLIENT_KEY)


def _get_pending_cart(db: Session, user: models.User) -> models.Order:
    cart = (
        db.query(models.Order)
        .filter(models.Order.user_id == user.id, models.Order.status == "pending")
        .first()
    )
    if not cart or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Keranjang kosong")
    return cart


def _mark_as_paid(db: Session, order: models.Order) -> None:
    if order.status != "dibayar":  # cegah stok dikurangi dua kali kalau notifikasi masuk berkali-kali
        for item in order.items:
            item.produk.stok -= item.jumlah
        order.status = "dibayar"
        db.commit()


@router.post("/checkout")
def checkout(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    cart = _get_pending_cart(db, current_user)

    order_id = f"cakyud-{cart.id}-{secrets.token_hex(4)}"
    ongkir = int(cart.ongkir or 0)
    gross_amount = int(sum(item.harga_saat_beli * item.jumlah for item in cart.items)) + ongkir

    item_details = [
        {
            "id": str(item.produk_id),
            "price": int(item.harga_saat_beli),
            "quantity": item.jumlah,
            "name": item.produk.nama[:50],
        }
        for item in cart.items
    ]
    if ongkir > 0:
        item_details.append({
            "id": "ongkir",
            "price": ongkir,
            "quantity": 1,
            "name": f"Ongkos Kirim ({cart.metode_pengiriman})",
        })

    param = {
        "transaction_details": {"order_id": order_id, "gross_amount": gross_amount},
        "customer_details": {"first_name": current_user.nama, "email": current_user.email},
        "item_details": item_details,
    }

    transaction = snap.create_transaction(param)

    cart.status = "menunggu_pembayaran"
    cart.payment_method = "midtrans"
    cart.midtrans_order_id = order_id
    db.commit()

    return {
        "snap_token": transaction["token"],
        "redirect_url": transaction["redirect_url"],
        "order_id": order_id,
    }


@router.post("/webhook")
async def midtrans_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()

    order_id = payload.get("order_id")
    status_code = payload.get("status_code")
    gross_amount = payload.get("gross_amount")
    signature_key = payload.get("signature_key")
    transaction_status = payload.get("transaction_status")
    fraud_status = payload.get("fraud_status")

    raw_signature = f"{order_id}{status_code}{gross_amount}{SERVER_KEY}"
    expected_signature = hashlib.sha512(raw_signature.encode()).hexdigest()

    if signature_key != expected_signature:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Signature tidak valid")

    order = db.query(models.Order).filter(models.Order.midtrans_order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order tidak ditemukan")

    if transaction_status in ("capture", "settlement") and fraud_status in (None, "accept"):
        _mark_as_paid(db, order)
    elif transaction_status in ("cancel", "deny", "expire"):
        order.status = "batal"
        db.commit()
    elif transaction_status == "pending":
        order.status = "menunggu_pembayaran"
        db.commit()

    return {"status": "ok"}


@router.get("/status/{order_id}")
def cek_status_manual(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Buat testing lokal — webhook Midtrans nggak bisa nembak localhost tanpa tunnel (ngrok dll)."""
    result = core_api.transactions.status(order_id)

    order = db.query(models.Order).filter(models.Order.midtrans_order_id == order_id).first()
    if order and result.get("transaction_status") in ("capture", "settlement"):
        _mark_as_paid(db, order)

    return result
# app/social_auth.py
"""
Verifikasi token dari Google & Facebook di sisi SERVER.

Tombol "Daftar/Masuk dengan Google/Facebook" di browser cuma menghasilkan
sebuah token dari Google/Facebook langsung ke JS di halaman — token itu
BELUM boleh dipercaya begitu saja, karena bisa saja dipalsukan orang lewat
DevTools/request manual. Makanya tiap token yang masuk ke endpoint
/auth/google dan /auth/facebook selalu dicek ulang ke server Google/Facebook
di sini dulu, baru dianggap sah.
"""
import os

import httpx
from fastapi import HTTPException, status
from google.auth import exceptions as google_exceptions
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")


def verifikasi_token_google(credential: str) -> dict:
    """Verifikasi ID token dari tombol Google. Balikin dict berisi
    sub (id unik Google), email, nama, foto_url."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login Google belum dikonfigurasi di server (isi GOOGLE_CLIENT_ID di .env)",
        )

    try:
        info = id_token.verify_oauth2_token(
            credential, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Google tidak valid")
    except google_exceptions.TransportError:
        # Gagal konek ke server Google buat verifikasi token (bukan token-nya yang salah)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gagal menghubungi server Google, coba lagi",
        )

    if info.get("email") and not info.get("email_verified", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email Google belum diverifikasi")

    return {
        "sub": info["sub"],
        "email": info.get("email"),
        "nama": info.get("name") or (info.get("email") or "Pengguna Google").split("@")[0],
        "foto_url": info.get("picture"),
    }


def verifikasi_token_facebook(access_token: str) -> dict:
    """Verifikasi access token dari tombol Facebook. Balikin dict berisi
    id (id unik Facebook), email (opsional, FB kadang nggak kasih), nama."""
    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login Facebook belum dikonfigurasi di server (isi FACEBOOK_APP_ID & FACEBOOK_APP_SECRET di .env)",
        )

    try:
        with httpx.Client(timeout=10) as client:
            # 1. Pastikan token ini beneran diterbitkan buat App kita, bukan app orang lain
            resp_debug = client.get(
                "https://graph.facebook.com/debug_token",
                params={
                    "input_token": access_token,
                    "access_token": f"{FACEBOOK_APP_ID}|{FACEBOOK_APP_SECRET}",
                },
            )
            debug = resp_debug.json()
            data_token = debug.get("data", {})
            if not data_token.get("is_valid") or str(data_token.get("app_id")) != str(FACEBOOK_APP_ID):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Facebook tidak valid")

            # 2. Ambil profil pemilik token
            resp_profil = client.get(
                "https://graph.facebook.com/me",
                params={"fields": "id,name,email", "access_token": access_token},
            )
            profil = resp_profil.json()
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gagal menghubungi server Facebook, coba lagi",
        )

    if "id" not in profil:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Facebook tidak valid")

    return {
        "id": profil["id"],
        "email": profil.get("email"),
        "nama": profil.get("name") or "Pengguna Facebook",
    }
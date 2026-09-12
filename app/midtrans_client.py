# app/midtrans_client.py
"""
Klien Midtrans (Snap & Core API) dipusatkan di sini biar bisa dipakai bareng
oleh payment.py (checkout, webhook) dan pesanan.py (batalkan pesanan sendiri).
"""
import os

import midtransclient
from fastapi import HTTPException, status

IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "False") == "True"
SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY")
CLIENT_KEY = os.getenv("MIDTRANS_CLIENT_KEY")

snap = midtransclient.Snap(is_production=IS_PRODUCTION, server_key=SERVER_KEY, client_key=CLIENT_KEY)
core_api = midtransclient.CoreApi(is_production=IS_PRODUCTION, server_key=SERVER_KEY, client_key=CLIENT_KEY)


def pastikan_midtrans_terkonfigurasi() -> None:
    """Dipanggil di awal endpoint yang beneran butuh Midtrans (checkout, cek status manual).

    SENGAJA nggak di-raise langsung pas modul ini di-import (beda dengan SECRET_KEY di
    security.py) — toko harus tetap bisa dijalankan buat lihat produk/kelola admin walau
    MIDTRANS_SERVER_KEY/CLIENT_KEY belum diisi (lihat setup.py, dua-duanya boleh dikosongin
    dulu). Jadi baru dicek pas endpoint pembayaran beneran dipanggil, dengan pesan error yang
    jelas — daripada nyusul error asing dari dalam library midtransclient (mis. gagal bikin
    Basic Auth header dari key kosong)."""
    if not SERVER_KEY or not CLIENT_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Pembayaran belum dikonfigurasi di server — isi MIDTRANS_SERVER_KEY & "
                "MIDTRANS_CLIENT_KEY di .env (jalankan 'python setup.py' buat bantu isi), "
                "lalu restart server."
            ),
        )
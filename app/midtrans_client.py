# app/midtrans_client.py
"""
Klien Midtrans (Snap & Core API) dipusatkan di sini biar bisa dipakai bareng
oleh payment.py (checkout, webhook) dan pesanan.py (batalkan pesanan sendiri).
"""
import os

import midtransclient

IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "False") == "True"
SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY")
CLIENT_KEY = os.getenv("MIDTRANS_CLIENT_KEY")

snap = midtransclient.Snap(is_production=IS_PRODUCTION, server_key=SERVER_KEY, client_key=CLIENT_KEY)
core_api = midtransclient.CoreApi(is_production=IS_PRODUCTION, server_key=SERVER_KEY, client_key=CLIENT_KEY)
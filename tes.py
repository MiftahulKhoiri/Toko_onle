# cek_midtrans_key.py — jalankan sekali: python cek_midtrans_key.py
from dotenv import load_dotenv
import os

load_dotenv()

server_key = os.getenv("MIDTRANS_SERVER_KEY") or ""
client_key = os.getenv("MIDTRANS_CLIENT_KEY") or ""
is_production = os.getenv("MIDTRANS_IS_PRODUCTION")

def mask(key):
    if not key:
        return "(KOSONG)"
    if len(key) <= 12:
        return key[:4] + "..."
    return key[:10] + "..." + key[-4:]

print(f"MIDTRANS_SERVER_KEY   : {mask(server_key)}  (panjang: {len(server_key)})")
print(f"MIDTRANS_CLIENT_KEY   : {mask(client_key)}  (panjang: {len(client_key)})")
print(f"MIDTRANS_IS_PRODUCTION: {is_production}")
print()
print("Cocokkan awalannya sama yang ada di dashboard.midtrans.com > Settings > Access Keys (mode Sandbox).")
print("Untuk Sandbox: Server Key biasanya diawali 'SB-Mid-server-', Client Key diawali 'SB-Mid-client-'.")
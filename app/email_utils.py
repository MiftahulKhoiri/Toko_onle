# app/email_utils.py
"""
Kirim email notifikasi status pesanan ke pembeli lewat SMTP (mis. Gmail).
Konfigurasi lewat .env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_NAME.
Kalau SMTP_USER/SMTP_PASSWORD belum diisi, pengiriman di-skip diam-diam — nggak
bikin proses checkout/ubah status pesanan ikut gagal cuma gara-gara email gagal kekirim.
"""
import os
import smtplib
import traceback
from email.mime.text import MIMEText

from app import models

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Salome Cakyud")

JUDUL_STATUS = {
    "dibayar": "Pembayaran Diterima",
    "diproses": "Pesanan Sedang Diproses",
    "selesai": "Pesanan Selesai",
    "batal": "Pesanan Dibatalkan",
}

PESAN_STATUS = {
    "dibayar": "Pembayaran kamu untuk pesanan #{id} sudah kami terima. Pesanan akan segera kami siapkan.",
    "diproses": "Pesanan #{id} kamu sedang kami siapkan.",
    "selesai": "Pesanan #{id} kamu sudah selesai. Terima kasih sudah belanja di {toko}!",
    "batal": "Pesanan #{id} kamu telah dibatalkan. Kalau ini nggak sesuai harapan, silakan hubungi kami.",
}


def _format_rupiah(angka: float) -> str:
    return f"Rp{angka:,.0f}".replace(",", ".")


def _rincian_item_teks(order: models.Order) -> str:
    baris = []
    for item in order.items:
        nama = item.produk.nama if item.produk else "(produk tidak ditemukan)"
        subtotal = item.harga_saat_beli * item.jumlah
        baris.append(f"- {item.jumlah}x {nama} = {_format_rupiah(subtotal)}")
        if item.catatan:
            baris.append(f"  Catatan: {item.catatan}")
    return "\n".join(baris)


def kirim_email_status_pesanan(order: models.Order, status_baru: str) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        return  # belum dikonfigurasi, skip diam-diam

    if not order.user or not order.user.email:
        return

    judul = JUDUL_STATUS.get(status_baru, "Update Pesanan")
    pesan_pembuka = PESAN_STATUS.get(status_baru, "Status pesanan #{id} kamu berubah.").format(
        id=order.id, toko=SMTP_FROM_NAME
    )

    isi = f"""Halo {order.user.nama},

{pesan_pembuka}

Rincian Pesanan #{order.id}:
{_rincian_item_teks(order)}

Ongkir: {_format_rupiah(order.ongkir)}
Total: {_format_rupiah(order.total_harga)}

Terima kasih,
{SMTP_FROM_NAME}
"""

    msg = MIMEText(isi)
    msg["Subject"] = f"[{SMTP_FROM_NAME}] {judul} — Pesanan #{order.id}"
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = order.user.email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception:
        # Jangan sampai proses checkout/ubah status gagal cuma gara-gara email gagal kekirim.
        traceback.print_exc()
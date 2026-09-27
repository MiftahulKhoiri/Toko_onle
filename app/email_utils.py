# app/email_utils.py
"""
Kirim email notifikasi status pesanan & alur "Lupa Password" ke pembeli lewat SMTP
(mis. Gmail). Konfigurasi lewat .env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
SMTP_FROM_NAME, APP_BASE_URL. Kalau SMTP_USER/SMTP_PASSWORD belum diisi, pengiriman
di-skip diam-diam — nggak bikin proses checkout/ubah status/reset password ikut gagal
cuma gara-gara email gagal kekirim.
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
# Dipakai buat bikin link di email reset password (mis. .../reset-password?token=...).
# Ganti ke domain asli toko di .env begitu sudah online — default ini cuma cocok buat lokal.
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/")

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


def _kirim_smtp(msg: MIMEText) -> None:
    """Satu tempat buat proses kirim SMTP-nya — dipakai bareng semua fungsi
    kirim_email_* di bawah, biar koneksi & try/except-nya nggak diulang-ulang."""
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception:
        # Jangan sampai proses checkout/ubah status/reset password gagal cuma
        # gara-gara email gagal kekirim.
        traceback.print_exc()


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
    _kirim_smtp(msg)


def kirim_email_reset_password(user: models.User, token_mentah: str) -> None:
    """Kirim link reset password. Dipanggil dari POST /auth/lupa-password, HANYA
    kalau akunnya punya password (bukan akun Google/Facebook murni) — buat kasus
    sebaliknya lihat kirim_email_info_akun_sosial di bawah."""
    if not SMTP_USER or not SMTP_PASSWORD:
        return
    if not user.email:
        return

    link_reset = f"{APP_BASE_URL}/reset-password?token={token_mentah}"

    isi = f"""Halo {user.nama},

Ada permintaan buat reset password akun kamu di {SMTP_FROM_NAME}.

Klik link berikut buat bikin password baru (link ini cuma berlaku 30 menit
dan cuma bisa dipakai sekali):
{link_reset}

Kalau kamu ngerasa nggak minta ini, abaikan aja email-nya — password kamu
nggak akan berubah selama link di atas nggak dibuka.

Terima kasih,
{SMTP_FROM_NAME}
"""

    msg = MIMEText(isi)
    msg["Subject"] = f"[{SMTP_FROM_NAME}] Reset Password Akun Kamu"
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = user.email
    _kirim_smtp(msg)


def kirim_email_info_akun_sosial(user: models.User) -> None:
    """Dipanggil kalau ada yang minta reset password buat email yang akunnya ternyata
    daftar lewat Google/Facebook (nggak pernah punya password). Info ini sengaja
    dikirim lewat email (channel privat ke pemilik akun asli) — BUKAN lewat response
    API — biar endpoint /auth/lupa-password tetap nggak bisa dipakai buat nebak-nebak
    email mana yang kedaftar di toko ini."""
    if not SMTP_USER or not SMTP_PASSWORD:
        return
    if not user.email:
        return

    provider = "Google" if user.daftar_via == "google" else "Facebook"

    isi = f"""Halo {user.nama},

Ada permintaan reset password buat akun kamu di {SMTP_FROM_NAME} pakai email ini.

Akun kamu terdaftar lewat {provider} dan nggak pakai password — silakan masuk
lewat tombol "Masuk dengan {provider}" di halaman login seperti biasa.

Kalau kamu ngerasa nggak minta ini, abaikan aja email-nya.

Terima kasih,
{SMTP_FROM_NAME}
"""

    msg = MIMEText(isi)
    msg["Subject"] = f"[{SMTP_FROM_NAME}] Soal Permintaan Reset Password"
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = user.email
    _kirim_smtp(msg)
# setup.py — script sekali jalan buat setup project: .env + akun admin
# Jalankan: python setup.py
# Aman dijalankan berkali-kali — tiap bagian ngecek dulu sebelum bikin/ganti.

import os
import secrets

from app.database import SessionLocal, engine
from app import models


ENV_PATH = ".env"


def baca_env(path):
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip()
    return data


def tulis_env(path, data):
    with open(path, "w") as f:
        for k, v in data.items():
            f.write(f"{k}={v}\n")


def setup_env():
    print("=== 1. Setup .env ===")
    env = baca_env(ENV_PATH)

    if env.get("SECRET_KEY"):
        jawaban = input("SECRET_KEY sudah ada. Ganti dengan yang baru? (y/n): ").strip().lower()
        if jawaban == "y":
            env["SECRET_KEY"] = secrets.token_hex(32)
            print("✓ SECRET_KEY baru di-generate.")
        else:
            print("- SECRET_KEY lama dipakai, dilewati.")
    else:
        env["SECRET_KEY"] = secrets.token_hex(32)
        print("✓ SECRET_KEY belum ada, otomatis di-generate.")

    env.setdefault("MIDTRANS_SERVER_KEY", "")
    env.setdefault("MIDTRANS_CLIENT_KEY", "")
    env.setdefault("MIDTRANS_IS_PRODUCTION", "False")

    env.setdefault("SMTP_HOST", "smtp.gmail.com")
    env.setdefault("SMTP_PORT", "587")
    env.setdefault("SMTP_USER", "")
    env.setdefault("SMTP_PASSWORD", "")
    env.setdefault("SMTP_FROM_NAME", "Salome Cakyud")

    tulis_env(ENV_PATH, env)
    print(f"✓ File '{ENV_PATH}' siap.\n")

    if not env.get("SMTP_USER") or not env.get("SMTP_PASSWORD"):
        print("→ SMTP_USER & SMTP_PASSWORD masih kosong, isi manual nanti kalau mau aktifkan notifikasi email.")
    if not env.get("MIDTRANS_SERVER_KEY") or not env.get("MIDTRANS_CLIENT_KEY"):
        print("→ MIDTRANS_SERVER_KEY & MIDTRANS_CLIENT_KEY masih kosong, isi manual nanti kalau mau aktifkan pembayaran.\n")


def setup_admin():
    print("=== 2. Setup Akun Admin ===")
    models.Base.metadata.create_all(bind=engine)  # jaga-jaga kalau toko.db belum pernah dibuat
    db = SessionLocal()

    admin_sekarang = db.query(models.User).filter(models.User.is_admin == True).first()

    if admin_sekarang:
        print(f"- Sudah ada admin: {admin_sekarang.nama} ({admin_sekarang.email})")
        jawaban = input("Mau jadikan akun lain sebagai admin juga? (y/n): ").strip().lower()
        if jawaban != "y":
            print("- Dilewati, admin yang lama tetap dipakai.\n")
            db.close()
            return

    email = input("Email akun yang mau dijadikan admin: ").strip()
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        print("✗ User tidak ditemukan. Pastikan sudah register dulu lewat /register. Dilewati.\n")
    elif user.is_admin:
        print(f"- {user.nama} ({user.email}) sudah jadi admin sebelumnya. Dilewati.\n")
    else:
        user.is_admin = True
        db.commit()
        print(f"✓ {user.nama} ({user.email}) sekarang jadi admin.\n")

    db.close()


if __name__ == "__main__":
    setup_env()
    setup_admin()
    print("=== Selesai. Jalankan ulang server: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 ===")
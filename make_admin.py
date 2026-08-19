# make_admin.py
from app.database import SessionLocal
from app import models

email = input("Email akun yang mau dijadikan admin: ").strip()

db = SessionLocal()
user = db.query(models.User).filter(models.User.email == email).first()

if not user:
    print("User tidak ditemukan. Pastikan sudah register dulu lewat /register")
else:
    user.is_admin = True
    db.commit()
    print(f"{user.nama} ({user.email}) sekarang jadi admin.")

db.close()
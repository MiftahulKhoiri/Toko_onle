# app/routers/auth.py
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.rate_limit import batasi_percobaan
from app.security import create_access_token, hash_password, verify_password
from app.social_auth import verifikasi_token_facebook, verifikasi_token_google

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

UPLOAD_DIR_FOTO = "app/static/img/profil"
EKSTENSI_DIIZINKAN_FOTO = {".jpg", ".jpeg", ".png", ".webp"}
UKURAN_MAKS_FOTO = 3 * 1024 * 1024  # 3MB — sudah di-resize di browser sebelum diunggah

os.makedirs(UPLOAD_DIR_FOTO, exist_ok=True)


def _hapus_foto_lama(foto_url: Optional[str]) -> None:
    if not foto_url or not foto_url.startswith("/static/img/profil/"):
        return
    path_file = os.path.join(UPLOAD_DIR_FOTO, os.path.basename(foto_url))
    if os.path.isfile(path_file):
        try:
            os.remove(path_file)
        except OSError:
            pass


def _buat_token(user: models.User) -> dict:
    # "sub" pakai id (bukan email) karena sekarang nggak semua user punya email
    # (akun Google tanpa email publik, akun daftar-cepat-HP, dll).
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


def _commit_atau_konflik(db: Session, pesan: str):
    """Commit, tapi tangkep race condition (2 request nyaris bareng daftar
    pakai email/HP/akun sosial yang sama) biar nggak nge-crash jadi 500."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pesan)


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, request: Request, db: Session = Depends(get_db)):
    batasi_percobaan(f"register:{request.client.host}", maks=5, jendela_detik=600)

    # Normalisasi email biar "User@Gmail.com" dan "user@gmail.com" dianggap akun yang sama.
    email_normal = user.email.strip().lower()

    existing = db.query(models.User).filter(models.User.email == email_normal).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email sudah terdaftar")

    db_user = models.User(
        nama=user.nama,
        email=email_normal,
        hashed_password=hash_password(user.password),
        telepon=user.telepon,
        alamat_jalan=user.alamat_jalan,
        kelurahan=user.kelurahan,
        kecamatan=user.kecamatan,
        kota=user.kota,
        provinsi=user.provinsi,
        kode_pos=user.kode_pos,
        daftar_via="email",
    )
    db.add(db_user)
    _commit_atau_konflik(db, "Email sudah terdaftar")
    db.refresh(db_user)
    return db_user


@router.post("/register-telepon", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_telepon(data: schemas.TeleponRegister, request: Request, db: Session = Depends(get_db)):
    """Daftar cepat pakai No. HP + password — tanpa OTP. Karena nggak ada
    verifikasi kepemilikan nomor, password TETAP wajib supaya orang lain
    nggak bisa asal login pakai nomor HP siapa aja."""
    batasi_percobaan(f"register:{request.client.host}", maks=5, jendela_detik=600)

    existing = db.query(models.User).filter(models.User.telepon == data.telepon).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nomor HP sudah terdaftar")

    db_user = models.User(
        nama=data.nama,
        telepon=data.telepon,
        hashed_password=hash_password(data.password),
        daftar_via="telepon",
    )
    db.add(db_user)
    _commit_atau_konflik(db, "Nomor HP sudah terdaftar")
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=schemas.Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    batasi_percobaan(f"login:{request.client.host}", maks=5, jendela_detik=300)

    email_normal = form_data.username.strip().lower()
    user = db.query(models.User).filter(models.User.email == email_normal).first()

    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _buat_token(user)


@router.post("/login-telepon", response_model=schemas.Token)
def login_telepon(data: schemas.TeleponLogin, request: Request, db: Session = Depends(get_db)):
    batasi_percobaan(f"login:{request.client.host}", maks=5, jendela_detik=300)

    user = db.query(models.User).filter(models.User.telepon == data.telepon).first()

    if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nomor HP atau password salah")

    return _buat_token(user)


@router.post("/google", response_model=schemas.Token)
def login_google(data: schemas.GoogleLogin, request: Request, db: Session = Depends(get_db)):
    """Satu endpoint buat DAFTAR sekaligus LOGIN — kalau akun Google-nya
    belum pernah dipakai di sini, otomatis dibikinin akun baru."""
    batasi_percobaan(f"sosial:{request.client.host}", maks=15, jendela_detik=300)

    info = verifikasi_token_google(data.credential)
    email_normal = info["email"].strip().lower() if info["email"] else None

    user = db.query(models.User).filter(models.User.google_sub == info["sub"]).first()

    if not user and email_normal:
        existing = db.query(models.User).filter(models.User.email == email_normal).first()
        if existing:
            if existing.hashed_password:
                # JANGAN auto-tautkan & auto-login ke akun yang sudah punya password —
                # bisa aja itu password buatan orang lain yang daftar duluan pakai email
                # ini (pre-hijacking). Wajibkan login password dulu buat buktikan
                # kepemilikan akun, baru boleh ditautkan.
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email ini sudah terdaftar dengan password. Login pakai email & password itu dulu ya.",
                )
            # Akun lama TANPA password (dulunya daftar sosial juga) -> aman ditautkan.
            existing.google_sub = info["sub"]
            user = existing

    if not user:
        user = models.User(
            nama=info["nama"],
            email=email_normal,
            google_sub=info["sub"],
            foto_url=info.get("foto_url"),
            daftar_via="google",
        )
        db.add(user)

    _commit_atau_konflik(db, "Gagal menautkan akun Google, coba lagi")
    db.refresh(user)
    return _buat_token(user)


@router.post("/facebook", response_model=schemas.Token)
def login_facebook(data: schemas.FacebookLogin, request: Request, db: Session = Depends(get_db)):
    """Sama seperti /auth/google — daftar sekaligus login lewat 1 endpoint."""
    batasi_percobaan(f"sosial:{request.client.host}", maks=15, jendela_detik=300)

    info = verifikasi_token_facebook(data.access_token)
    email_normal = info["email"].strip().lower() if info.get("email") else None

    user = db.query(models.User).filter(models.User.facebook_id == info["id"]).first()

    if not user and email_normal:
        existing = db.query(models.User).filter(models.User.email == email_normal).first()
        if existing:
            if existing.hashed_password:
                # Sama seperti /auth/google — jangan auto-tautkan ke akun berpassword,
                # cegah celah pre-hijacking.
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email ini sudah terdaftar dengan password. Login pakai email & password itu dulu ya.",
                )
            existing.facebook_id = info["id"]
            user = existing

    if not user:
        user = models.User(
            nama=info["nama"],
            email=email_normal,
            facebook_id=info["id"],
            daftar_via="facebook",
        )
        db.add(user)

    _commit_atau_konflik(db, "Gagal menautkan akun Facebook, coba lagi")
    db.refresh(user)
    return _buat_token(user)


@router.get("/me", response_model=schemas.UserResponse)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=schemas.UserResponse)
def update_profile(
    user_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/foto", response_model=schemas.UserResponse)
async def upload_foto_profil(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ekstensi = os.path.splitext(file.filename or "")[1].lower()
    if ekstensi not in EKSTENSI_DIIZINKAN_FOTO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format foto harus jpg, jpeg, png, atau webp",
        )

    isi_file = await file.read()
    if len(isi_file) > UKURAN_MAKS_FOTO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ukuran foto maksimal 3MB")

    foto_lama = current_user.foto_url

    nama_file = f"user{current_user.id}-{uuid.uuid4().hex}{ekstensi}"
    with open(os.path.join(UPLOAD_DIR_FOTO, nama_file), "wb") as f:
        f.write(isi_file)

    current_user.foto_url = f"/static/img/profil/{nama_file}"
    db.commit()
    db.refresh(current_user)

    _hapus_foto_lama(foto_lama)  # hapus foto lama SETELAH foto baru tersimpan, biar cuma nyimpen 1

    return current_user


@router.delete("/me/foto", response_model=schemas.UserResponse)
def hapus_foto_profil(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _hapus_foto_lama(current_user.foto_url)
    current_user.foto_url = None
    db.commit()
    db.refresh(current_user)
    return current_user
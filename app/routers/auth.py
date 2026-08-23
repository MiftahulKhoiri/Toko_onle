# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.rate_limit import batasi_percobaan
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, request: Request, db: Session = Depends(get_db)):
    batasi_percobaan(f"register:{request.client.host}", maks=5, jendela_detik=600)

    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email sudah terdaftar")

    db_user = models.User(
        nama=user.nama,
        email=user.email,
        hashed_password=hash_password(user.password),
        telepon=user.telepon,
        alamat_jalan=user.alamat_jalan,
        kelurahan=user.kelurahan,
        kecamatan=user.kecamatan,
        kota=user.kota,
        provinsi=user.provinsi,
        kode_pos=user.kode_pos,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=schemas.Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    batasi_percobaan(f"login:{request.client.host}", maks=5, jendela_detik=300)

    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserResponse)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user


# ---------- Endpoint Update Profil ----------
@router.put("/me", response_model=schemas.UserResponse)
def update_profile(
    user_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Endpoint untuk memperbarui data profil & alamat lengkap user
    """
    # Hanya memperbarui field yang dikirim dari frontend (bukan None)
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user
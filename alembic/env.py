# alembic/env.py
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Biar "from app...." di bawah bisa ke-import, apa pun folder tempat perintah
# `alembic` ini dijalankan — nunjuk ke folder project (1 tingkat di atas folder alembic/).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SQLALCHEMY_DATABASE_URL
from app.models import Base

config = context.config

# URL koneksi database DIAMBIL dari app/database.py (satu-satunya sumber), bukan
# ditulis ulang manual di alembic.ini — biar nggak ada 2 tempat yang bisa beda-beda.
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata = Base.metadata dari models.py — INI yang dipakai Alembic buat
# membandingkan "skema di models.py" vs "skema aktual di database" pas `--autogenerate`.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # lihat catatan di run_migrations_online()
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # WAJIB buat SQLite: banyak jenis ALTER TABLE (drop kolom, ubah tipe,
            # tambah constraint) nggak didukung SQLite secara native. Mode batch
            # bikin Alembic otomatis akalin lewat "bikin tabel baru + salin data +
            # ganti nama", alih-alih coba ALTER langsung yang bakal gagal.
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
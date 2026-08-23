# 🍢 Toko Salome Cakyud

Toko online untuk jualan bakso & aneka makanan lainnya. Dibangun dari nol pakai FastAPI (Python) — lengkap dengan akun pembeli, keranjang belanja, pembayaran online via Midtrans, dan panel admin buat kelola produk & pesanan.

## Daftar Isi

- [Fitur](#fitur)
- [Teknologi](#teknologi)
- [Struktur Folder](#struktur-folder)
- [Skema Database](#skema-database)
- [Instalasi](#instalasi)
- [Konfigurasi (.env)](#konfigurasi-env)
- [Menjalankan Server](#menjalankan-server)
- [Membuat Akun Admin](#membuat-akun-admin)
- [Daftar Endpoint API](#daftar-endpoint-api)
- [Alur Penggunaan](#alur-penggunaan)
- [Catatan Midtrans](#catatan-midtrans)
- [Troubleshooting](#troubleshooting)
- [Lisensi](#lisensi)

## Fitur

- 🔐 Registrasi & login pembeli dengan JWT (token disimpan di `localStorage` browser)
- 🍜 Katalog produk dengan pencarian instan (filter langsung di halaman utama, tanpa reload)
- 📄 Halaman detail per produk
- 🛒 Keranjang belanja (tambah, ubah jumlah, hapus item)
- 💳 Checkout & pembayaran online via **Midtrans Snap**
- 📦 Riwayat & status pesanan pembeli ("Pesanan Saya")
- 🛠️ Panel admin: CRUD produk + upload foto langsung dari HP, dan kelola status semua pesanan
- 👤 Halaman profil buat lengkapi alamat & no. HP (dipakai untuk pengiriman)
- 🏷️ Status produk **Ready** / **Pre-Order (PO)** per item

## Teknologi

| Bagian | Teknologi |
|---|---|
| Backend | FastAPI + SQLAlchemy |
| Database | SQLite (`toko.db`, otomatis dibuat saat server pertama kali jalan) |
| Auth | JWT (`python-jose`) + hash password `pbkdf2_sha256` (`passlib`) |
| Pembayaran | Midtrans Snap API & Core API (`midtransclient`) |
| Frontend | Jinja2 template + vanilla JS + CSS (server-rendered, bukan SPA) |

## Struktur Folder

Toko_onle-main/
├── app/
│   ├── main.py            # entry point, daftar semua router
│   ├── database.py        # koneksi SQLite + session
│   ├── models.py          # model tabel: Produk, User, Order, OrderItem
│   ├── schemas.py         # schema request/response (Pydantic)
│   ├── security.py        # hash password, buat & decode JWT
│   ├── dependencies.py    # get_current_user & get_current_admin
│   ├── routers/
│   │   ├── auth.py        # register, login, profil
│   │   ├── produk.py      # CRUD produk + upload foto
│   │   ├── keranjang.py   # keranjang belanja
│   │   ├── payment.py     # checkout & webhook Midtrans
│   │   ├── pesanan.py     # riwayat pesanan pembeli
│   │   ├── admin.py       # kelola semua pesanan (admin)
│   │   └── pages.py       # semua halaman HTML (Jinja2)
│   ├── templates/         # index, detail_produk, login, register, keranjang,
│   │                       # pesanan_saya, profil, admin_dashboard, admin_pesanan
│   └── static/
│       ├── css/style.css
│       ├── js/main.js     # logika frontend: token, keranjang, dsb
│       └── img/produk/    # foto produk hasil upload (auto-dibuat)
├── make_admin.py           # script buat jadiin 1 akun sebagai admin
├── requirements.txt
└── .env                    # kamu buat sendiri, lihat bagian Konfigurasi

## Skema Database

**Produk** — `id, nama, deskripsi, harga, stok, kategori, gambar_url, is_ready, is_po, created_at`

**User** — `id, nama, email, hashed_password, telepon, alamat_jalan, kelurahan, kecamatan, kota, provinsi, kode_pos, is_admin, created_at`

**Order** (keranjang & pesanan pakai tabel yang sama) — `id, user_id, total_harga, status, payment_method, midtrans_order_id, created_at`
Status yang dipakai: `pending` (keranjang aktif) → `menunggu_pembayaran` → `dibayar` → `diproses` → `selesai`, atau `batal`.

**OrderItem** — `id, order_id, produk_id, jumlah, harga_saat_beli` (harga disimpan saat itu juga, jadi nggak berubah walau harga produk diubah admin belakangan)

## Instalasi

1. Ekstrak project, lalu masuk ke folder root-nya (folder yang isinya ada `app/`, `make_admin.py`, `requirements.txt`):
   ```bash
   cd Toko_onle-main


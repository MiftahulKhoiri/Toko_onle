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
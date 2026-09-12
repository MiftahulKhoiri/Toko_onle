# 🍢 Toko Salome Cakyud

Toko online untuk jualan bakso & aneka makanan lainnya. Dibangun dari nol pakai FastAPI (Python) — lengkap dengan akun pembeli (email/No. HP/Google/Facebook), keranjang belanja, buku alamat, pembayaran online via Midtrans, notifikasi email, halaman profil toko, testimoni pembeli, dan panel admin buat kelola semuanya.

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

- 🔐 Registrasi & login pembeli — email+password, No. HP+password, atau lewat **Google**/**Facebook** (JWT, token disimpan di `localStorage` browser)
- 🍜 Katalog produk dengan pencarian instan, filter kategori, dan urutan (semua / terbaru / terlaris)
- 📄 Halaman detail per produk, status **Ready** / **Pre-Order (PO)**
- 🛒 Keranjang belanja (tambah, ubah jumlah, catatan per item, hapus item)
- 🛵 Dua metode pengiriman: **Diantar** (ongkir flat) atau **Ambil Sendiri** (gratis)
- 📍 Buku alamat pengiriman (banyak alamat, tandai salah satu jadi utama)
- 💳 Checkout & pembayaran online via **Midtrans Snap**, dengan pengecekan stok atomic (aman dari race condition saat 2 checkout barengan) dan endpoint cek status manual buat testing lokal
- 📦 Riwayat, status, & pembatalan pesanan pembeli ("Pesanan Saya")
- 📧 Notifikasi email otomatis tiap status pesanan berubah (opsional, butuh SMTP)
- 👤 Halaman profil pembeli: ubah data diri, upload/hapus foto profil
- 🏬 Halaman **Profil Toko** publik (landing page): logo, banner, jam operasional, kontak WA, link GoFood/GrabFood/ShopeeFood & medsos
- ⭐ Testimoni dari pembeli asli (login dulu), otomatis disembunyikan sampai disetujui admin
- 🛠️ Panel admin: CRUD produk + upload foto, kelola semua pesanan, kelola profil toko, moderasi testimoni
- 🚦 Rate-limit sederhana di endpoint sensitif (login, daftar, kirim testimoni)
- 🖼️ Upload gambar divalidasi dari isi filenya (bukan cuma ekstensi nama file)

## Teknologi

| Bagian | Teknologi |
|---|---|
| Backend | FastAPI + SQLAlchemy |
| Database | SQLite (`toko.db`, otomatis dibuat saat server pertama kali jalan) |
| Auth | JWT (`python-jose`) + hash password `pbkdf2_sha256` (`passlib`) |
| Login Sosial | `google-auth` (verifikasi ID token Google) + `httpx` (verifikasi token ke Facebook Graph API) |
| Pembayaran | Midtrans Snap API & Core API (`midtransclient`) |
| Notifikasi | Email lewat SMTP (mis. Gmail), pakai `smtplib` bawaan Python |
| Frontend | Jinja2 template + vanilla JS + CSS (server-rendered, bukan SPA) |
| Konfigurasi | `python-dotenv` (baca file `.env`) |

## Struktur Folder

```
Toko_onle-main/
├── app/
│   ├── main.py               # entry point, daftar semua router
│   ├── database.py           # koneksi SQLite + session
│   ├── models.py             # model tabel: Produk, User, Alamat, Order, OrderItem, ProfilToko, Testimoni
│   ├── schemas.py            # schema request/response (Pydantic)
│   ├── security.py           # hash password, buat & decode JWT
│   ├── dependencies.py       # get_current_user & get_current_admin
│   ├── rate_limit.py         # rate-limit sederhana (in-memory, cukup buat 1 proses/skala kecil)
│   ├── order_status.py       # helper ubah status pesanan + trigger email
│   ├── email_utils.py        # kirim email notifikasi lewat SMTP
│   ├── social_auth.py        # verifikasi token Google & Facebook
│   ├── midtrans_client.py    # klien Midtrans Snap & Core API (dipakai bareng)
│   ├── upload_utils.py       # validasi ISI file upload gambar (magic bytes)
│   ├── routers/
│   │   ├── auth.py           # register, login (email/HP/Google/Facebook), profil, foto profil
│   │   ├── produk.py         # CRUD produk + upload foto (admin)
│   │   ├── keranjang.py      # keranjang belanja & metode pengiriman
│   │   ├── alamat.py         # buku alamat pengiriman
│   │   ├── payment.py        # checkout, webhook, & cek status Midtrans
│   │   ├── pesanan.py        # riwayat & pembatalan pesanan pembeli
│   │   ├── admin.py          # kelola status semua pesanan (admin)
│   │   ├── profil_toko.py    # profil toko publik + testimoni
│   │   └── pages.py          # semua halaman HTML (Jinja2)
│   ├── templates/            # index, detail_produk, login, register, keranjang, checkout_alamat,
│   │                          # pesanan_saya, profil, profil_toko, admin_dashboard, admin_pesanan,
│   │                          # admin_profil_toko, base
│   └── static/
│       ├── css/style.css
│       ├── js/main.js        # logika frontend bareng: token, toast, escapeHtml, formatErrorDetail, dst
│       └── img/               # produk/, profil/, toko/, testimoni/ — semua auto-dibuat, isinya di-gitignore
├── setup.py                   # script sekali-jalan: buat .env + jadikan 1 akun sebagai admin
├── migrasi.py                 # migrasi SATU KALI, cuma perlu kalau upgrade dari toko.db versi lama
│                               # sebelum ada tabel alamat — instalasi baru TIDAK perlu jalankan ini
├── requirements.txt
└── .env                        # kamu buat sendiri lewat setup.py, lihat bagian Konfigurasi
```

## Skema Database

**Produk** — `id, nama, deskripsi, harga, stok, kategori, gambar_url, is_ready, is_po, created_at`

**User** — `id, nama, email, hashed_password, telepon, foto_url, google_sub, facebook_id, daftar_via, alamat_jalan, kelurahan, kecamatan, kota, provinsi, kode_pos, is_admin, created_at`
Kolom `alamat_jalan`…`kode_pos` di tabel ini adalah alamat lama di profil (peninggalan versi awal) — alur checkout sekarang pakai tabel **Alamat** terpisah di bawah.

**Alamat** — `id, user_id, label, alamat_jalan, kelurahan, kecamatan, kota, provinsi, kode_pos, is_default, created_at`

**Order** (keranjang & pesanan pakai tabel yang sama) — `id, user_id, alamat_id, total_harga, status, payment_method, midtrans_order_id, metode_pengiriman, ongkir, created_at`
Status yang dipakai: `pending` (keranjang aktif) → `menunggu_pembayaran` → `dibayar` → `diproses` → `selesai`, atau `batal`.

**OrderItem** — `id, order_id, produk_id, jumlah, harga_saat_beli, catatan` (harga disimpan saat itu juga, jadi nggak berubah walau harga produk diubah admin belakangan)

**ProfilToko** (cuma 1 baris) — `id, nama_toko, tagline, deskripsi, alamat, maps_embed_url, jam_operasional, is_buka, kontak_wa, logo_url, banner_url, gofood_url, grabfood_url, shopeefood_url, instagram_url, tiktok_url, facebook_url, updated_at`

**Testimoni** — `id, nama_pelanggan, rating, ulasan, foto_url, ditampilkan, user_id, created_at`

## Instalasi

1. Ekstrak project, lalu masuk ke folder root-nya (folder yang isinya ada `app/`, `setup.py`, `requirements.txt`):
   ```bash
   cd Toko_onle-main
   ```

2. (Opsional tapi disarankan) buat virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. Install semua dependency:
   ```bash
   pip install -r requirements.txt
   ```

## Konfigurasi (.env)

File `.env` **tidak** ikut ter-commit (lihat `.gitignore`), jadi harus dibuat sendiri di folder root. Cara termudah: jalankan `python setup.py` (lihat bagian [Membuat Akun Admin](#membuat-akun-admin)) — otomatis bikin `.env` dengan `SECRET_KEY` acak dan semua key lain kosong/default, tinggal isi manual yang mana yang mau diaktifkan.

| Variabel | Wajib? | Keterangan |
|---|---|---|
| `SECRET_KEY` | ✅ Wajib | Kunci buat tanda tangan JWT. Server **tidak akan menyala** kalau ini kosong. Di-generate otomatis oleh `setup.py`. |
| `MIDTRANS_SERVER_KEY` / `MIDTRANS_CLIENT_KEY` | Opsional | Dari dashboard Midtrans (Settings → Access Keys). Kosongin dulu kalau belum mau aktifkan pembayaran — toko tetap bisa jalan buat lihat produk & kelola admin, checkout aja yang belum bisa. |
| `MIDTRANS_IS_PRODUCTION` | Opsional | `False` (default) = mode Sandbox/testing. Ganti `True` kalau sudah pakai key Production yang asli. |
| `SMTP_HOST` / `SMTP_PORT` | Opsional | Default `smtp.gmail.com` / `587`. |
| `SMTP_USER` / `SMTP_PASSWORD` | Opsional | Akun pengirim email notifikasi. Kalau pakai Gmail, `SMTP_PASSWORD` harus **App Password** (bukan password akun biasa). Kosongin kalau nggak mau notifikasi email. |
| `SMTP_FROM_NAME` | Opsional | Nama pengirim yang muncul di email, default `Salome Cakyud`. |
| `GOOGLE_CLIENT_ID` | Opsional | Dari Google Cloud Console (OAuth Client ID, tipe Web). Kosongin = tombol "Masuk dengan Google" otomatis disembunyikan. |
| `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET` | Opsional | Dari Facebook Developers Console. Kosongin = tombol "Masuk dengan Facebook" otomatis disembunyikan. |

## Menjalankan Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Toko bisa diakses di `http://localhost:8000`. Dokumentasi API interaktif (Swagger UI) otomatis tersedia di `http://localhost:8000/docs`.

## Membuat Akun Admin

Nggak ada akun admin bawaan — semua akun awalnya pembeli biasa. Urutannya:

1. **Sebelum** pernah daftar, jalankan dulu `python setup.py` — ini yang bikinkan file `.env` (lihat bagian Konfigurasi di atas).
2. Nyalakan server, lalu daftar 1 akun lewat halaman `/register` (bebas pakai email, No. HP, Google, atau Facebook).
3. Jalankan `python setup.py` **sekali lagi** — kali ini bagian "Setup Akun Admin" akan minta email ATAU No. HP akun yang tadi didaftarkan, lalu menjadikannya admin.

Aman dijalankan berkali-kali; kalau sudah ada admin, akan ditanya dulu apa mau menambah admin lain atau dilewati.

## Daftar Endpoint API

Daftar lengkap & selalu up-to-date otomatis tersedia di `/docs` (Swagger UI) begitu server jalan. Ringkasannya per grup:

| Prefix | Isi |
|---|---|
| `POST/GET /auth/...` | Register (email/HP), login (email/HP/Google/Facebook), profil sendiri, foto profil |
| `GET/POST/PUT/DELETE /produk/...` | Katalog produk (publik) + CRUD & upload foto (admin) |
| `GET/POST/PUT/DELETE /keranjang/...` | Keranjang belanja & metode pengiriman (login) |
| `GET/POST/PUT/DELETE /alamat/...` | Buku alamat pengiriman (login) |
| `POST /payment/checkout` `/webhook` `/status/{id}` | Checkout, webhook Midtrans, cek status manual |
| `GET/PUT /pesanan/...` | Riwayat & pembatalan pesanan sendiri (login) |
| `GET/PUT /admin/...` | Kelola semua pesanan (admin) |
| `GET/PUT/POST /api/profil-toko`, `/testimoni/...` | Profil toko publik + moderasi testimoni |

## Alur Penggunaan

1. Pembeli buka `/`, cari/filter produk, klik salah satu buat lihat detail di `/menu/{id}`.
2. Tambah ke keranjang → buka `/keranjang-saya`, atur jumlah/catatan, pilih metode pengiriman.
3. Kalau **Diantar**: lanjut ke `/checkout/alamat` buat pilih/tambah alamat, baru checkout. Kalau **Ambil Sendiri**: langsung checkout dari keranjang.
4. Checkout memanggil Midtrans Snap dan mengarahkan pembeli ke halaman pembayaran.
5. Setelah bayar, Midtrans mengirim webhook ke `/payment/webhook` → status pesanan otomatis jadi `dibayar`, email notifikasi terkirim (kalau SMTP diisi).
6. Admin memproses pesanan lewat `/panel-admin/pesanan` (ubah status `diproses` → `selesai`).
7. Pembeli bisa kasih testimoni lewat halaman `/profil-toko` — otomatis nunggu persetujuan admin (`/panel-admin/profil-toko`) sebelum tampil ke publik.

## Catatan Midtrans

- Selama `MIDTRANS_IS_PRODUCTION=False`, semua transaksi jalan di **Sandbox** Midtrans (uang nggak beneran kepotong) — pakai kartu/metode simulasi dari dokumentasi Midtrans buat testing.
- Webhook (`/payment/webhook`) perlu URL publik yang bisa diakses Midtrans — `localhost` nggak bisa langsung ditembak. Buat testing di komputer sendiri, pakai tunnel seperti `ngrok http 8000`, lalu daftarkan URL ngrok-nya (+ `/payment/webhook`) di dashboard Midtrans (Settings → Configuration → Payment Notification URL).
- Kalau nggak mau repot setup ngrok buat testing, ada endpoint `GET /payment/status/{order_id}` yang bisa dipanggil manual (lewat `/docs`) buat narik status transaksi terbaru dari Midtrans dan sinkronkan ke database — cuma bisa buat pesanan milik akun yang sedang login.

## Troubleshooting

| Gejala | Kemungkinan Penyebab |
|---|---|
| Server nggak mau nyala, error soal `SECRET_KEY` | `.env` belum ada / `SECRET_KEY` kosong. Jalankan `python setup.py`. |
| Checkout gagal, pesan "Pembayaran belum dikonfigurasi" | `MIDTRANS_SERVER_KEY`/`MIDTRANS_CLIENT_KEY` masih kosong di `.env`. |
| Upload foto ditolak padahal filenya gambar | Format harus jpg/jpeg/png/webp DAN isi filenya beneran gambar (bukan cuma nama filenya yang diakhiri `.jpg`). Ukuran maks 3MB (foto profil) / 5MB (produk, toko, testimoni). |
| Tombol "Masuk dengan Google"/"Facebook" nggak muncul | `GOOGLE_CLIENT_ID` / `FACEBOOK_APP_ID` belum diisi di `.env` — ini disengaja (fitur otomatis disembunyikan kalau belum disetel). |
| Email notifikasi nggak terkirim | `SMTP_USER`/`SMTP_PASSWORD` kosong, atau (kalau Gmail) pakai password akun biasa — harus **App Password**. Cek juga folder Spam. |
| Webhook Midtrans nggak pernah masuk | URL webhook belum didaftarkan/masih nunjuk ke `localhost` — lihat bagian [Catatan Midtrans](#catatan-midtrans). |

## Lisensi

Proyek ini dilisensikan di bawah **GNU General Public License v3.0** — lihat file [`LICENSE`](./LICENSE) buat detail lengkapnya.
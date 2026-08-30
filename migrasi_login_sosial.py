# migrasi_login_sosial.py — jalankan sekali aja: python migrasi_login_sosial.py
#
# Nambahin dukungan daftar/login cepat pakai Google, Facebook, dan No. HP.
# Kolom email & hashed_password di tabel users tadinya WAJIB diisi (NOT NULL) —
# sekarang harus boleh kosong (akun Google/Facebook/HP nggak selalu punya
# keduanya), dan SQLite nggak bisa "ALTER COLUMN" buat lepas NOT NULL, jadi
# tabel users di-rebuild ulang: disalin ke tabel baru dengan skema yang benar,
# lalu tabel lama dihapus. Data lama (nama, email, alamat, dst) tetap aman.
#
# Aman dijalankan berkali-kali — dicek dulu sebelum diubah.
import sqlite3

conn = sqlite3.connect("toko.db")
conn.execute("PRAGMA foreign_keys = OFF")
cur = conn.cursor()

cur.execute("PRAGMA table_info(users)")
kolom_ada = {baris[1] for baris in cur.fetchall()}
kolom_baru = {"google_sub", "facebook_id", "daftar_via"}

if kolom_baru.issubset(kolom_ada):
    print("- Tabel 'users' sudah punya semua kolom baru, lewati rebuild.")
else:
    print("=== Rebuild tabel 'users' (biar email & password boleh kosong) ===")

    cur.execute("ALTER TABLE users RENAME TO users_lama")

    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            hashed_password VARCHAR(255),
            telepon VARCHAR(20),
            foto_url VARCHAR(255),
            alamat_jalan TEXT,
            kelurahan VARCHAR(100),
            kecamatan VARCHAR(100),
            kota VARCHAR(100),
            provinsi VARCHAR(100),
            kode_pos VARCHAR(10),
            is_admin BOOLEAN DEFAULT 0,
            google_sub VARCHAR(255),
            facebook_id VARCHAR(255),
            daftar_via VARCHAR(20) DEFAULT 'email',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        INSERT INTO users (
            id, nama, email, hashed_password, telepon, foto_url,
            alamat_jalan, kelurahan, kecamatan, kota, provinsi, kode_pos,
            is_admin, daftar_via, created_at
        )
        SELECT
            id, nama, email, hashed_password, telepon, foto_url,
            alamat_jalan, kelurahan, kecamatan, kota, provinsi, kode_pos,
            is_admin, 'email', created_at
        FROM users_lama
    """)

    cur.execute("DROP TABLE users_lama")
    print("✓ Tabel 'users' selesai di-rebuild — semua data lama dipindah aman.")

# Index unik buat kolom yang boleh kosong tapi kalau keisi harus unik.
# SQLite anggap NULL beda dari NULL lain, jadi bisa banyak akun tanpa
# telepon/google_sub/facebook_id sekaligus, tapi begitu keisi nggak boleh kembar.
for nama_index, kolom in [
    ("ix_users_email_unik", "email"),
    ("ix_users_telepon_unik", "telepon"),
    ("ix_users_google_sub_unik", "google_sub"),
    ("ix_users_facebook_id_unik", "facebook_id"),
]:
    try:
        cur.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS {nama_index} ON users({kolom})")
        print(f"✓ Index unik utk '{kolom}' siap")
    except sqlite3.OperationalError as e:
        print(f"✗ Gagal bikin index unik '{kolom}': {e}")
        print(f"  → Ada data '{kolom}' yang kembar di tabel users, beresin manual dulu baru jalankan ulang.")

conn.commit()
conn.execute("PRAGMA foreign_keys = ON")
conn.close()
print("\nSelesai. Boleh hapus file ini setelah dijalankan.")
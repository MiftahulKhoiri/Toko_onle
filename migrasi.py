# migrasi_alamat.py — jalankan sekali aja: python migrasi_alamat.py
import sqlite3

conn = sqlite3.connect("toko.db")
cur = conn.cursor()

# 1. Buat tabel alamat kalau belum ada
cur.execute("""
CREATE TABLE IF NOT EXISTS alamat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    label VARCHAR(50) DEFAULT 'Rumah',
    alamat_jalan TEXT,
    kelurahan VARCHAR(100),
    kecamatan VARCHAR(100),
    kota VARCHAR(100),
    provinsi VARCHAR(100),
    kode_pos VARCHAR(10),
    is_default BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
print("✓ Tabel 'alamat' siap")

# 2. Tambah kolom alamat_id ke orders
try:
    cur.execute("ALTER TABLE orders ADD COLUMN alamat_id INTEGER")
    print("✓ Kolom 'alamat_id' ditambahkan ke tabel 'orders'")
except sqlite3.OperationalError as e:
    print(f"- Lewati 'alamat_id': {e}")

# 3. Pindahkan alamat lama dari profil user (kalau ada) ke tabel alamat baru
cur.execute("""
    SELECT id, nama, alamat_jalan, kelurahan, kecamatan, kota, provinsi, kode_pos
    FROM users
    WHERE alamat_jalan IS NOT NULL AND TRIM(alamat_jalan) != ''
""")
users_dengan_alamat = cur.fetchall()

for (user_id, nama, jalan, kel, kec, kota, prov, kodepos) in users_dengan_alamat:
    cur.execute("SELECT COUNT(*) FROM alamat WHERE user_id = ?", (user_id,))
    sudah_ada = cur.fetchone()[0]
    if sudah_ada == 0:
        cur.execute("""
            INSERT INTO alamat (user_id, label, alamat_jalan, kelurahan, kecamatan, kota, provinsi, kode_pos, is_default)
            VALUES (?, 'Rumah', ?, ?, ?, ?, ?, ?, 1)
        """, (user_id, jalan, kel, kec, kota, prov, kodepos))
        print(f"✓ Alamat lama milik {nama} dipindah ke daftar alamat baru")

conn.commit()
conn.close()
print("Selesai. Boleh hapus file ini setelah dijalankan.")
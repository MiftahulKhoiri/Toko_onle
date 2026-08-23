# migrasi_ongkir_catatan.py — jalankan sekali aja: python migrasi_ongkir_catatan.py
# Setelah berhasil, file ini boleh dihapus.
import sqlite3

conn = sqlite3.connect("toko.db")
cur = conn.cursor()

def tambah_kolom(tabel, kolom, tipe_default):
    try:
        cur.execute(f"ALTER TABLE {tabel} ADD COLUMN {kolom} {tipe_default}")
        print(f"✓ Kolom '{kolom}' ditambahkan ke tabel '{tabel}'")
    except sqlite3.OperationalError as e:
        print(f"- Lewati '{kolom}': {e}")

tambah_kolom("orders", "metode_pengiriman", "VARCHAR(20) DEFAULT 'diantar'")
tambah_kolom("orders", "ongkir", "FLOAT DEFAULT 0")
tambah_kolom("order_items", "catatan", "VARCHAR(255)")

conn.commit()
conn.close()
print("Selesai. Kolom baru siap dipakai.")
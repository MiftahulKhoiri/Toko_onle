# app/upload_utils.py
"""
Validasi ISI file upload gambar (dipakai bareng oleh auth.py, produk.py, profil_toko.py).
Ekstensi nama file (.jpg/.png/.webp) gampang dipalsukan — tinggal ganti akhirannya — makanya
byte pertama file (magic number) ikut dicek di sini, biar nggak ada yang bisa upload file
sembarangan (skrip, dll) yang cuma "menyamar" pakai nama berakhiran gambar.
"""
from fastapi import HTTPException, status


def pastikan_isi_gambar_valid(isi_file: bytes) -> None:
    """Raise HTTPException 400 kalau byte pertama file nggak cocok sama format gambar
    manapun yang kita dukung (JPEG/PNG/WEBP). Dipanggil SETELAH cek ekstensi & ukuran,
    supaya urutan pesan errornya tetap masuk akal (ekstensi -> ukuran -> isi)."""
    cocok = (
        isi_file.startswith(b"\xff\xd8\xff")  # JPEG
        or isi_file.startswith(b"\x89PNG\r\n\x1a\n")  # PNG
        or (isi_file.startswith(b"RIFF") and isi_file[8:12] == b"WEBP")  # WEBP
    )
    if not cocok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Isi file bukan gambar yang valid (tidak cocok dengan format JPG/PNG/WEBP)",
        )
# app/upload_utils.py
"""
Validasi ISI file upload gambar (dipakai bareng oleh auth.py, produk.py, profil_toko.py).
Ekstensi nama file (.jpg/.png/.webp) gampang dipalsukan — tinggal ganti akhirannya — makanya
byte pertama file (magic number) ikut dicek di sini, biar nggak ada yang bisa upload file
sembarangan (skrip, dll) yang cuma "menyamar" pakai nama berakhiran gambar.
"""
from fastapi import HTTPException, UploadFile, status

UKURAN_CHUNK_BACA = 1024 * 1024  # baca per 1MB


async def baca_upload_dengan_batas(file: UploadFile, batas_bytes: int, pesan_error: str) -> bytes:
    """Baca isi UploadFile per-potongan (BUKAN sekali baca semua pakai `await file.read()`
    tanpa argumen) dan LANGSUNG berhenti + tolak begitu totalnya kelewat batas.

    Kalau dibiarkan baca sekaligus, orang bisa sengaja upload file raksasa (berapa pun
    besarnya) dan server bakal coba nampung semuanya dulu ke RAM SEBELUM sempat ditolak —
    celah DoS lewat kehabisan memori, apalagi di perangkat yang RAM-nya terbatas kayak
    Raspberry Pi. Dengan cara ini, paling banyak cuma sekitar (batas_bytes + 1 potongan)
    yang pernah nangkring di memori, berapa pun ukuran asli file yang diunggah."""
    potongan_terkumpul = bytearray()
    while True:
        potongan = await file.read(UKURAN_CHUNK_BACA)
        if not potongan:
            break
        potongan_terkumpul.extend(potongan)
        if len(potongan_terkumpul) > batas_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pesan_error)

    return bytes(potongan_terkumpul)


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
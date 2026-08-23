# app/rate_limit.py
"""
Rate limiter sederhana berbasis memori — cukup buat proyek skala kecil
yang jalan 1 proses (uvicorn tanpa banyak worker). Nggak perlu Redis/dependency baru.
"""
import time
from collections import defaultdict

from fastapi import HTTPException, status

_percobaan = defaultdict(list)


def batasi_percobaan(key: str, maks: int = 5, jendela_detik: int = 6) -> None:
    """
    Batasi jumlah percobaan per `key` (mis. gabungan IP + endpoint) dalam
    jendela waktu tertentu. Lempar HTTP 429 (dengan header Retry-After
    berisi sisa detik) kalau sudah melewati batas.
    """
    sekarang = time.time()
    waktu_list = _percobaan[key]

    # buang catatan percobaan yang sudah lewat jendela waktu
    waktu_list[:] = [t for t in waktu_list if sekarang - t < jendela_detik]

    if len(waktu_list) >= maks:
        waktu_tertua = waktu_list[0]
        sisa_detik = max(1, int(jendela_detik - (sekarang - waktu_tertua)) + 1)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Terlalu banyak percobaan. Coba lagi dalam {sisa_detik} detik.",
            headers={"Retry-After": str(sisa_detik)},
        )

    waktu_list.append(sekarang)
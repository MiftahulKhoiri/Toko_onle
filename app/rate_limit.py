# app/rate_limit.py
"""
Rate limiter sederhana berbasis memori — cukup buat proyek skala kecil
yang jalan 1 proses (uvicorn tanpa banyak worker). Nggak perlu Redis/dependency baru.
"""
import time
from collections import defaultdict

from fastapi import HTTPException, status

_percobaan = defaultdict(list)


def batasi_percobaan(key: str, maks: int = 5, jendela_detik: int = 300) -> None:
    """
    Batasi jumlah percobaan per `key` (mis. gabungan IP + endpoint) dalam
    jendela waktu tertentu. Lempar HTTP 429 kalau sudah melewati batas.
    """
    sekarang = time.time()
    waktu_list = _percobaan[key]

    # buang catatan percobaan yang sudah lewat jendela waktu
    waktu_list[:] = [t for t in waktu_list if sekarang - t < jendela_detik]

    if len(waktu_list) >= maks:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Terlalu banyak percobaan, coba lagi beberapa menit lagi.",
        )

    waktu_list.append(sekarang)
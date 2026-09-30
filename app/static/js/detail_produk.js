// app/static/js/detail_produk.js — logika halaman detail produk (/produk/{id})
// Bergantung pada helper global di main.js: formatErrorDetail, showToast, updateCartBadge
// Stok maksimal dibaca dari atribut data-stok di .detail-produk (diisi Jinja di detail_produk.html)

let jumlahDipilih = 1;
const stokMaks = parseInt(document.querySelector(".detail-produk").dataset.stok, 10);

/* ---------- Stepper jumlah ---------- */

function ubahJumlahDetail(delta) {
    const baru = jumlahDipilih + delta;
    if (baru < 1 || baru > stokMaks) return;
    jumlahDipilih = baru;
    document.getElementById("detail-jumlah").textContent = jumlahDipilih;
}

/* ---------- Tambah ke keranjang ---------- */

async function tambahDetailKeKeranjang(produkId) {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/login";
        return;
    }

    const res = await fetch("/keranjang/items", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ produk_id: produkId, jumlah: jumlahDipilih }),
    });

    if (!res.ok) {
        const err = await res.json();
        showToast(formatErrorDetail(err.detail) || "Gagal menambahkan ke keranjang", "error");
        return;
    }
    updateCartBadge();
    showToast("Ditambahkan ke keranjang!");
}
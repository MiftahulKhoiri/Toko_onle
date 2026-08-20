// Fungsi untuk merender status autentikasi & nama user di header (Pojok Kanan Top)
async function renderNavAuth() {
    const navAuth = document.getElementById("nav-auth");
    if (!navAuth) return;

    const token = localStorage.getItem("access_token");

    // Jika belum login / tidak ada token
    if (!token) {
        navAuth.innerHTML = `
            <a href="/login" class="btn-login">Login</a>
            <a href="/register" class="btn-register">Daftar</a>
        `;
        return;
    }

    try {
        const res = await fetch("/auth/me", {
            headers: { Authorization: `Bearer ${token}` },
        });

        if (res.ok) {
            const user = await res.json();
            
            // Link tambahan jika user adalah admin
            let adminLink = user.is_admin ? '<a href="/admin/dashboard" class="nav-admin-link">Admin</a>' : '';

            // Menampilkan nama user di pojok kanan yang mengarah ke /profil
            navAuth.innerHTML = `
                ${adminLink}
                <a href="/profil" class="user-profile-link" title="Buka Profil">
                    👤 <span>${user.nama}</span>
                </a>
            `;
        } else {
            // Jika token kadaluwarsa atau tidak valid
            localStorage.removeItem("access_token");
            navAuth.innerHTML = `
                <a href="/login" class="btn-login">Login</a>
                <a href="/register" class="btn-register">Daftar</a>
            `;
        }
    } catch (err) {
        console.error("Gagal memuat info user", err);
        navAuth.innerHTML = `
            <a href="/login" class="btn-login">Login</a>
            <a href="/register" class="btn-register">Daftar</a>
        `;
    }
}

// Fungsi Tambah Ke Keranjang (Dipakai di halaman produk)
async function tambahKeKeranjang(produkId) {
    const token = localStorage.getItem("access_token");
    if (!token) {
        alert("Silakan login terlebih dahulu untuk menambah produk ke keranjang.");
        window.location.href = "/login";
        return;
    }

    try {
        const res = await fetch("/keranjang/items", {
            method: "POST",
            headers: { 
                Authorization: `Bearer ${token}`, 
                "Content-Type": "application/json" 
            },
            body: JSON.stringify({ produk_id: produkId, jumlah: 1 }),
        });

        if (!res.ok) {
            const err = await res.json();
            alert(err.detail || "Gagal menambahkan ke keranjang");
            return;
        }

        alert("Ditambahkan ke keranjang!");
    } catch (err) {
        console.error("Kesalahan saat menambah keranjang", err);
        alert("Terjadi kesalahan koneksi");
    }
}

// Panggil fungsi renderNavAuth setelah DOM siap sepenuhnya
document.addEventListener("DOMContentLoaded", renderNavAuth);

// app/static/js/main.js
async function updateNavAuthState() {
    const token = localStorage.getItem("access_token");
    const navAuth = document.getElementById("nav-auth");
    if (!navAuth) return;

    if (!token) {
        navAuth.innerHTML = '<a href="/login">Login</a>';
        return;
    }

    try {
        const res = await fetch("/auth/me", { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) {
            localStorage.removeItem("access_token");
            navAuth.innerHTML = '<a href="/login">Login</a>';
            return;
        }
        const user = await res.json();

        let html = `<span class="nav-user">Halo, ${user.nama}`;
        if (user.is_admin) html += ' <span class="badge-admin">Admin</span>';
        html += "</span>";

        if (user.is_admin) {
            html += ' <a href="/panel-admin">Kelola Produk</a> <a href="/panel-admin/pesanan">Kelola Pesanan</a>';
        }
        html += ' <a href="#" onclick="logout()">Logout</a>';

        navAuth.innerHTML = html;
    } catch (err) {
        navAuth.innerHTML = '<a href="/login">Login</a>';
    }
}

function logout() {
    localStorage.removeItem("access_token");
    window.location.href = "/";
}

async function tambahKeKeranjang(produkId) {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/login";
        return;
    }

    const res = await fetch("/keranjang/items", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ produk_id: produkId, jumlah: 1 }),
    });

    if (!res.ok) {
        const err = await res.json();
        alert(err.detail || "Gagal menambahkan ke keranjang");
        return;
    }
    alert("Ditambahkan ke keranjang!");
}

updateNavAuthState();

async function renderNavAuth() {
    const navAuth = document.getElementById("nav-auth");
    if (!navAuth) return;

    const token = localStorage.getItem("access_token");

    if (!token) {
        // Tampilan jika belum login
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
            // POJOK KANAN: Nama user diklik menuju menu profil (/profil)
            let adminLink = user.is_admin ? '<a href="/admin/dashboard">Admin</a>' : '';
            
            navAuth.innerHTML = `
                ${adminLink}
                <a href="/profil" class="user-profile-link">
                    👤 <span>${user.nama}</span>
                </a>
            `;
        } else {
            // Token kadaluwarsa / tidak valid
            localStorage.removeItem("access_token");
            navAuth.innerHTML = `<a href="/login">Login</a>`;
        }
    } catch (err) {
        console.error("Gagal memuat info user", err);
        navAuth.innerHTML = `<a href="/login">Login</a>`;
    }
}

document.addEventListener("DOMContentLoaded", renderNavAuth);

// app/static/js/main.js
async function renderNavAuth() {
    const token = localStorage.getItem("access_token");
    const navAuth = document.getElementById("nav-auth");
    if (!navAuth) return;

    if (!token) {
        navAuth.innerHTML = '<a href="/login">Login</a> <a href="/register">Daftar</a>';
        return;
    }

    try {
        const res = await fetch("/auth/me", { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) {
            localStorage.removeItem("access_token");
            navAuth.innerHTML = '<a href="/login">Login</a> <a href="/register">Daftar</a>';
            return;
        }
        const user = await res.json();

        let html = "";
        if (user.is_admin) {
            html += '<a href="/panel-admin">Kelola Produk</a> <a href="/panel-admin/pesanan">Kelola Pesanan</a> ';
        }
        html += `<a href="/profil" class="nav-profil">👤 ${user.nama}`;
        if (user.is_admin) html += ' <span class="badge-admin">Admin</span>';
        html += "</a>";

        navAuth.innerHTML = html;
    } catch (err) {
        navAuth.innerHTML = '<a href="/login">Login</a> <a href="/register">Daftar</a>';
    }
}

async function updateCartBadge() {
    const badge = document.getElementById("cart-badge");
    if (!badge) return;

    const token = localStorage.getItem("access_token");
    if (!token) {
        badge.style.display = "none";
        return;
    }

    try {
        const res = await fetch("/keranjang/", { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) {
            badge.style.display = "none";
            return;
        }
        const cart = await res.json();
        const totalItem = cart.items.reduce((sum, item) => sum + item.jumlah, 0);

        if (totalItem > 0) {
            badge.textContent = totalItem;
            badge.style.display = "inline-block";
        } else {
            badge.style.display = "none";
        }
    } catch (err) {
        badge.style.display = "none";
    }
}

// Notifikasi kecil di bawah layar, ganti pengganti alert() bawaan browser.
// Panggil dari halaman mana pun: showToast("Pesan sukses") atau showToast("Pesan gagal", "error")
function showToast(pesan, tipe = "sukses") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast toast-${tipe}`;
    toast.textContent = pesan;
    container.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add("toast-show"));

    setTimeout(() => {
        toast.classList.remove("toast-show");
        setTimeout(() => toast.remove(), 300);
    }, 2800);
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
        showToast(err.detail || "Gagal menambahkan ke keranjang", "error");
        return;
    }
    updateCartBadge();
    showToast("Ditambahkan ke keranjang!");
}

renderNavAuth();
updateCartBadge();
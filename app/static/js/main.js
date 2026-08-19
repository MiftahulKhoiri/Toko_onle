// app/static/js/main.js
function updateNavAuthState() {
    const token = localStorage.getItem("access_token");
    const navAuth = document.getElementById("nav-auth");
    if (!navAuth) return;
    navAuth.innerHTML = token
        ? '<a href="#" onclick="logout()">Logout</a>'
        : '<a href="/login">Login</a>';
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
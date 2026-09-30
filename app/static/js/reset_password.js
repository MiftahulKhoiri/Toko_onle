// app/static/js/reset_password.js — logika halaman /reset-password
// Bergantung pada helper global di main.js: formatErrorDetail

const params = new URLSearchParams(window.location.search);
const token = params.get("token");

const form = document.getElementById("reset-password-form");
const pesan = document.getElementById("pesan");
const tombol = document.getElementById("reset-btn");

// Link tanpa ?token=... dianggap tidak valid
if (!token) {
    pesan.textContent = "Link reset tidak valid — pastikan kamu membuka link lengkap dari email.";
    tombol.disabled = true;
}

// ---------- Simpan password baru ----------
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    pesan.style.color = "";
    pesan.textContent = "";

    const passwordBaru = document.getElementById("password-baru").value;
    const passwordUlang = document.getElementById("password-ulang").value;

    if (passwordBaru !== passwordUlang) {
        pesan.textContent = "Password baru & pengulangannya nggak sama";
        return;
    }

    try {
        const res = await fetch("/auth/reset-password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token, password_baru: passwordBaru }),
        });

        const data = await res.json();
        if (!res.ok) {
            pesan.textContent = formatErrorDetail(data.detail) || "Gagal reset password";
            return;
        }

        localStorage.setItem("access_token", data.access_token);
        pesan.style.color = "#2e7d32";
        pesan.textContent = "Password berhasil diganti! Mengarahkan ke beranda...";
        setTimeout(() => { window.location.href = "/"; }, 1500);
    } catch (err) {
        pesan.textContent = "Tidak bisa terhubung ke server";
    }
});
// app/static/js/profil.js — logika halaman /profil
// Bergantung pada helper global di main.js: formatErrorDetail, showToast, renderNavAuth

const token = localStorage.getItem("access_token");

/* ---------- Ganti tampilan: view <-> edit ---------- */

function tampilkanEdit() {
    document.getElementById("tampilan-profil").style.display = "none";
    document.getElementById("form-edit-profil").style.display = "block";
}

function tampilkanView() {
    document.getElementById("form-edit-profil").style.display = "none";
    document.getElementById("tampilan-profil").style.display = "block";
}

/* ---------- Foto profil ---------- */

function resizeGambarKeSquare(file, ukuran = 400) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        const reader = new FileReader();
        reader.onload = (e) => { img.src = e.target.result; };
        reader.onerror = reject;
        img.onload = () => {
            const canvas = document.createElement("canvas");
            canvas.width = ukuran;
            canvas.height = ukuran;
            const ctx = canvas.getContext("2d");

            // crop tengah jadi persegi dulu, baru resize ke ukuran target
            const sisi = Math.min(img.width, img.height);
            const sx = (img.width - sisi) / 2;
            const sy = (img.height - sisi) / 2;
            ctx.drawImage(img, sx, sy, sisi, sisi, 0, 0, ukuran, ukuran);

            canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.85);
        };
        img.onerror = reject;
        reader.readAsDataURL(file);
    });
}

document.getElementById("input-foto-profil").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
        showToast("Format foto harus jpg, png, atau webp", "error");
        return;
    }

    try {
        const blob = await resizeGambarKeSquare(file, 400);
        const formData = new FormData();
        formData.append("file", blob, "foto-profil.jpg");

        const res = await fetch("/auth/me/foto", {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json();
            showToast(formatErrorDetail(err.detail) || "Gagal upload foto", "error");
            return;
        }

        showToast("Foto profil berhasil diperbarui!");
        await loadProfil();
        if (typeof renderNavAuth === "function") renderNavAuth();
    } catch (err) {
        showToast("Gagal memproses foto", "error");
    }

    e.target.value = "";
});

async function hapusFotoProfil() {
    if (!confirm("Hapus foto profil?")) return;
    await fetch("/auth/me/foto", {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
    });
    await loadProfil();
    if (typeof renderNavAuth === "function") renderNavAuth();
}

/* ---------- Muat data profil ---------- */

async function loadProfil() {
    if (!token) {
        window.location.href = "/login";
        return;
    }

    try {
        const res = await fetch("/auth/me", {
            headers: { Authorization: `Bearer ${token}` }
        });

        if (!res.ok) {
            localStorage.removeItem("access_token");
            window.location.href = "/login";
            return;
        }

        const user = await res.json();

        document.getElementById("view-nama").textContent = user.nama || "-";
        document.getElementById("view-email").textContent = user.email || "-";
        document.getElementById("view-telepon").textContent = user.telepon || "Belum diisi";

        const avatarEl = document.getElementById("profil-avatar");
        const btnHapusFoto = document.getElementById("btn-hapus-foto");
        if (user.foto_url) {
            avatarEl.innerHTML = `<img src="${user.foto_url}" alt="Foto profil">`;
            avatarEl.classList.add("profil-avatar-ada-foto");
            btnHapusFoto.style.display = "inline-block";
        } else {
            avatarEl.textContent = (user.nama || "?").trim().charAt(0).toUpperCase();
            avatarEl.classList.remove("profil-avatar-ada-foto");
            btnHapusFoto.style.display = "none";
        }

        const komponenAlamat = [
            user.alamat_jalan,
            user.kelurahan ? `Kel. ${user.kelurahan}` : null,
            user.kecamatan ? `Kec. ${user.kecamatan}` : null,
            user.kota,
            user.provinsi,
            user.kode_pos
        ].filter(Boolean);

        document.getElementById("view-alamat-gabungan").textContent =
            komponenAlamat.length > 0 ? komponenAlamat.join(", ") : "Belum diisi";

        document.getElementById("edit-nama").value = user.nama || "";
        document.getElementById("edit-email").value = user.email || "";
        document.getElementById("edit-telepon").value = user.telepon || "";
        document.getElementById("edit-alamat-jalan").value = user.alamat_jalan || "";
        document.getElementById("edit-kelurahan").value = user.kelurahan || "";
        document.getElementById("edit-kecamatan").value = user.kecamatan || "";
        document.getElementById("edit-kota").value = user.kota || "";
        document.getElementById("edit-provinsi").value = user.provinsi || "";
        document.getElementById("edit-kode-pos").value = user.kode_pos || "";
    } catch (err) {
        console.error("Gagal memuat data profil", err);
    }
}

/* ---------- Simpan perubahan profil ---------- */

document.getElementById("edit-profil-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
        nama: document.getElementById("edit-nama").value,
        telepon: document.getElementById("edit-telepon").value || null,
        alamat_jalan: document.getElementById("edit-alamat-jalan").value || null,
        kelurahan: document.getElementById("edit-kelurahan").value || null,
        kecamatan: document.getElementById("edit-kecamatan").value || null,
        kota: document.getElementById("edit-kota").value || null,
        provinsi: document.getElementById("edit-provinsi").value || null,
        kode_pos: document.getElementById("edit-kode-pos").value || null,
    };

    try {
        const res = await fetch("/auth/me", {
            method: "PUT",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            showToast("Profil berhasil diperbarui!");
            await loadProfil();
            tampilkanView();
            if (typeof renderNavAuth === "function") renderNavAuth();
        } else {
            const err = await res.json();
            showToast(formatErrorDetail(err.detail) || "Gagal memperbarui profil", "error");
        }
    } catch (err) {
        showToast("Terjadi kesalahan koneksi", "error");
    }
});

/* ---------- Logout ---------- */

function logout() {
    if (confirm("Apakah kamu yakin ingin keluar?")) {
        localStorage.removeItem("access_token");
        window.location.href = "/";
    }
}

/* ---------- Init ---------- */

document.addEventListener("DOMContentLoaded", loadProfil);
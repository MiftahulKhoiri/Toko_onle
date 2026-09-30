// app/static/js/admin_profil_toko.js — logika halaman /panel-admin/profil-toko
// Bergantung pada helper global di main.js: escapeHtml, formatErrorDetail, showToast

const token = localStorage.getItem("access_token");
let TESTIMONI_CACHE = [];

/* ---------- Cek akses admin ---------- */

async function cekAdmin() {
    const checkDiv = document.getElementById("admin-check");
    if (!token) {
        checkDiv.innerHTML = '<p>Silakan <a href="/login">login</a> dulu.</p>';
        return false;
    }
    const res = await fetch("/auth/me", { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) {
        checkDiv.innerHTML = '<p>Sesi habis, silakan <a href="/login">login</a> lagi.</p>';
        return false;
    }
    const user = await res.json();
    if (!user.is_admin) {
        checkDiv.innerHTML = "<p>Akses ditolak — halaman ini khusus admin.</p>";
        return false;
    }
    document.getElementById("admin-content").style.display = "block";
    return true;
}

/* ---------- Upload & pratinjau gambar ---------- */

async function uploadGambarToko(fileInputEl) {
    if (!fileInputEl.files || !fileInputEl.files[0]) return null;
    const formData = new FormData();
    formData.append("file", fileInputEl.files[0]);

    const res = await fetch("/api/profil-toko/upload-gambar", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
    });

    if (!res.ok) {
        const err = await res.json();
        throw new Error(formatErrorDetail(err.detail) || "Gagal upload gambar");
    }
    const data = await res.json();
    return data.url;
}

function pratinjauFile(inputEl, previewEl) {
    inputEl.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
            previewEl.src = URL.createObjectURL(e.target.files[0]);
            previewEl.style.display = "block";
        } else {
            previewEl.style.display = "none";
        }
    });
}
pratinjauFile(document.getElementById("pt-logo-file"), document.getElementById("pt-logo-preview"));
pratinjauFile(document.getElementById("pt-banner-file"), document.getElementById("pt-banner-preview"));
pratinjauFile(document.getElementById("tt-foto-file"), document.getElementById("tt-foto-preview"));
pratinjauFile(document.getElementById("edit-tt-foto-file"), document.getElementById("edit-tt-foto-preview"));

/* ---------- Profil toko ---------- */

async function muatProfilToko() {
    const res = await fetch("/api/profil-toko");
    const profil = await res.json();

    document.getElementById("pt-nama").value = profil.nama_toko || "";
    document.getElementById("pt-tagline").value = profil.tagline || "";
    document.getElementById("pt-deskripsi").value = profil.deskripsi || "";
    document.getElementById("pt-buka").checked = !!profil.is_buka;
    document.getElementById("pt-jam").value = profil.jam_operasional || "";
    document.getElementById("pt-wa").value = profil.kontak_wa || "";
    document.getElementById("pt-alamat").value = profil.alamat || "";
    document.getElementById("pt-maps").value = profil.maps_embed_url || "";
    document.getElementById("pt-logo-url").value = profil.logo_url || "";
    document.getElementById("pt-banner-url").value = profil.banner_url || "";
    document.getElementById("pt-gofood").value = profil.gofood_url || "";
    document.getElementById("pt-grabfood").value = profil.grabfood_url || "";
    document.getElementById("pt-shopeefood").value = profil.shopeefood_url || "";
    document.getElementById("pt-ig").value = profil.instagram_url || "";
    document.getElementById("pt-tiktok").value = profil.tiktok_url || "";
    document.getElementById("pt-fb").value = profil.facebook_url || "";

    if (profil.logo_url) {
        document.getElementById("pt-logo-preview").src = profil.logo_url;
        document.getElementById("pt-logo-preview").style.display = "block";
    }
    if (profil.banner_url) {
        document.getElementById("pt-banner-preview").src = profil.banner_url;
        document.getElementById("pt-banner-preview").style.display = "block";
    }
}

document.getElementById("profil-toko-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("profil-toko-msg");
    msg.textContent = "";

    try {
        let logoUrl = document.getElementById("pt-logo-url").value.trim() || null;
        const logoFile = document.getElementById("pt-logo-file");
        if (logoFile.files && logoFile.files[0]) {
            logoUrl = await uploadGambarToko(logoFile);
        }

        let bannerUrl = document.getElementById("pt-banner-url").value.trim() || null;
        const bannerFile = document.getElementById("pt-banner-file");
        if (bannerFile.files && bannerFile.files[0]) {
            bannerUrl = await uploadGambarToko(bannerFile);
        }

        const payload = {
            nama_toko: document.getElementById("pt-nama").value,
            tagline: document.getElementById("pt-tagline").value || null,
            deskripsi: document.getElementById("pt-deskripsi").value || null,
            is_buka: document.getElementById("pt-buka").checked,
            jam_operasional: document.getElementById("pt-jam").value || null,
            kontak_wa: document.getElementById("pt-wa").value || null,
            alamat: document.getElementById("pt-alamat").value || null,
            maps_embed_url: document.getElementById("pt-maps").value || null,
            logo_url: logoUrl,
            banner_url: bannerUrl,
            gofood_url: document.getElementById("pt-gofood").value || null,
            grabfood_url: document.getElementById("pt-grabfood").value || null,
            shopeefood_url: document.getElementById("pt-shopeefood").value || null,
            instagram_url: document.getElementById("pt-ig").value || null,
            tiktok_url: document.getElementById("pt-tiktok").value || null,
            facebook_url: document.getElementById("pt-fb").value || null,
        };

        const res = await fetch("/api/profil-toko", {
            method: "PUT",
            headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(formatErrorDetail(err.detail) || "Gagal menyimpan profil toko");
        }
    } catch (err) {
        // Ini nangkep kegagalan SIMPAN aja (upload foto / PUT profil-toko).
        msg.textContent = err.message || "Gagal menyimpan profil toko";
        return;
    }

    // Data sudah pasti kesimpen di titik ini. Muat ulang form itu langkah terpisah —
    // kalau ini yang gagal (mis. koneksi ke server sempat putus), jangan sampai kelihatan
    // seperti simpannya yang gagal.
    showToast("Profil toko berhasil disimpan!");
    try {
        await muatProfilToko();
    } catch (err) {
        msg.textContent = "Tersimpan, tapi gagal memuat ulang form. Refresh halaman ini manual buat lihat datanya.";
    }
});

/* ---------- Testimoni: daftar ---------- */

async function muatDaftarTestimoni() {
    const container = document.getElementById("daftar-testimoni");
    const res = await fetch("/testimoni/semua", { headers: { Authorization: `Bearer ${token}` } });
    const list = await res.json();
    TESTIMONI_CACHE = list;

    if (!list.length) {
        container.innerHTML = "<p>Belum ada testimoni.</p>";
        return;
    }

    let html = `
        <table class="keranjang-table">
            <tr>
                <th>Pelanggan</th>
                <th>Sumber</th>
                <th>Rating</th>
                <th>Ulasan</th>
                <th>Tampil?</th>
                <th>Aksi</th>
            </tr>`;

    for (const t of list) {
        const bintang = "★".repeat(t.rating) + "☆".repeat(5 - t.rating);
        const sumber = t.user_id ? "🧑 Pembeli" : "👤 Admin";
        html += `<tr>
            <td><strong>${escapeHtml(t.nama_pelanggan)}</strong></td>
            <td>${sumber}</td>
            <td>${bintang}</td>
            <td class="kolom-ulasan">${escapeHtml(t.ulasan)}</td>
            <td>${t.ditampilkan ? "✅" : "🚫"}</td>
            <td>
                <button onclick="bukaEditTestimoni(${t.id})">✏️ Edit</button>
                <button onclick="hapusTestimoni(${t.id})" class="btn-hapus">🗑️ Hapus</button>
            </td>
        </tr>`;
    }
    html += "</table>";
    container.innerHTML = html;
}

/* ---------- Testimoni: tambah ---------- */

document.getElementById("tambah-testimoni-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("testimoni-msg");
    msg.textContent = "";

    try {
        let fotoUrl = null;
        const fotoFile = document.getElementById("tt-foto-file");
        if (fotoFile.files && fotoFile.files[0]) {
            fotoUrl = await uploadGambarToko(fotoFile);
        }

        const payload = {
            nama_pelanggan: document.getElementById("tt-nama").value,
            rating: parseInt(document.getElementById("tt-rating").value, 10),
            ulasan: document.getElementById("tt-ulasan").value,
            foto_url: fotoUrl,
            ditampilkan: document.getElementById("tt-ditampilkan").checked,
        };

        const res = await fetch("/testimoni", {
            method: "POST",
            headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(formatErrorDetail(err.detail) || "Gagal menambah testimoni");
        }
    } catch (err) {
        msg.textContent = err.message || "Gagal menambah testimoni";
        return;
    }

    showToast("Testimoni berhasil ditambahkan!");
    e.target.reset();
    document.getElementById("tt-foto-preview").style.display = "none";
    document.getElementById("tt-rating").value = 5;
    document.getElementById("tt-ditampilkan").checked = true;
    try {
        await muatDaftarTestimoni();
    } catch (err) {
        msg.textContent = "Tersimpan, tapi gagal memuat ulang daftar. Refresh halaman ini manual.";
    }
});

/* ---------- Testimoni: edit (modal) ---------- */

function bukaEditTestimoni(id) {
    const t = TESTIMONI_CACHE.find((x) => x.id === id);
    if (!t) return;

    document.getElementById("edit-tt-id").value = t.id;
    document.getElementById("edit-tt-nama").value = t.nama_pelanggan;
    document.getElementById("edit-tt-rating").value = t.rating;
    document.getElementById("edit-tt-ulasan").value = t.ulasan;
    document.getElementById("edit-tt-ditampilkan").checked = !!t.ditampilkan;
    document.getElementById("edit-tt-foto-url").value = t.foto_url || "";

    document.getElementById("edit-tt-foto-file").value = "";
    const preview = document.getElementById("edit-tt-foto-preview");
    if (t.foto_url) {
        preview.src = t.foto_url;
        preview.style.display = "block";
    } else {
        preview.style.display = "none";
    }

    document.getElementById("edit-testimoni-modal").style.display = "flex";
}

function tutupEditTestimoni() {
    document.getElementById("edit-testimoni-modal").style.display = "none";
}

async function simpanEditTestimoni() {
    const id = document.getElementById("edit-tt-id").value;
    try {
        let fotoUrl = document.getElementById("edit-tt-foto-url").value.trim() || null;
        const fotoFile = document.getElementById("edit-tt-foto-file");
        if (fotoFile.files && fotoFile.files[0]) {
            fotoUrl = await uploadGambarToko(fotoFile);
        }

        const payload = {
            nama_pelanggan: document.getElementById("edit-tt-nama").value,
            rating: parseInt(document.getElementById("edit-tt-rating").value, 10),
            ulasan: document.getElementById("edit-tt-ulasan").value,
            foto_url: fotoUrl,
            ditampilkan: document.getElementById("edit-tt-ditampilkan").checked,
        };

        const res = await fetch(`/testimoni/${id}`, {
            method: "PUT",
            headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(formatErrorDetail(err.detail) || "Gagal menyimpan perubahan");
        }
    } catch (err) {
        showToast(err.message || "Gagal menyimpan perubahan", "error");
        return;
    }

    showToast("Testimoni berhasil diperbarui!");
    tutupEditTestimoni();
    try {
        await muatDaftarTestimoni();
    } catch (err) {
        showToast("Tersimpan, tapi gagal memuat ulang daftar. Refresh halaman ini manual.", "error");
    }
}

/* ---------- Testimoni: hapus ---------- */

async function hapusTestimoni(id) {
    if (!confirm("Hapus testimoni ini?")) return;
    const res = await fetch(`/testimoni/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
        showToast("Testimoni dihapus");
    } else {
        showToast("Gagal menghapus testimoni", "error");
    }
    muatDaftarTestimoni();
}

/* ---------- Init ---------- */

(async () => {
    if (await cekAdmin()) {
        await muatProfilToko();
        await muatDaftarTestimoni();
    }
})();
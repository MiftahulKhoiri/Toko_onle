// app/static/js/admin_dashboard.js — logika halaman /panel-admin (kelola produk)
// Bergantung pada helper global di main.js: escapeHtml, formatErrorDetail, showToast

const token = localStorage.getItem("access_token");
const PER_HALAMAN = 10;
let halamanProduk = 1;
let PRODUK_CACHE = [];

/* ---------- Upload & preview foto ---------- */

async function uploadFoto(fileInputEl) {
    if (!fileInputEl.files || !fileInputEl.files[0]) return null;
    const formData = new FormData();
    formData.append("file", fileInputEl.files[0]);

    const res = await fetch("/produk/upload-foto", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
    });

    if (!res.ok) {
        const err = await res.json();
        throw new Error(formatErrorDetail(err.detail) || "Gagal upload foto");
    }
    const data = await res.json();
    return data.gambar_url;
}

document.getElementById("p-foto").addEventListener("change", (e) => {
    const preview = document.getElementById("p-foto-preview");
    if (e.target.files && e.target.files[0]) {
        preview.src = URL.createObjectURL(e.target.files[0]);
        preview.style.display = "block";
    } else {
        preview.style.display = "none";
    }
});

document.getElementById("edit-foto").addEventListener("change", (e) => {
    const preview = document.getElementById("edit-foto-preview");
    if (e.target.files && e.target.files[0]) {
        preview.src = URL.createObjectURL(e.target.files[0]);
        preview.style.display = "block";
    }
});

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

/* ---------- Daftar produk & pagination ---------- */

async function muatProduk() {
    const container = document.getElementById("daftar-produk");
    const skip = (halamanProduk - 1) * PER_HALAMAN;
    const res = await fetch(`/produk/?skip=${skip}&limit=${PER_HALAMAN}`);
    const produkList = await res.json();
    PRODUK_CACHE = produkList;

    if (!produkList.length && halamanProduk > 1) {
        halamanProduk -= 1;
        return muatProduk();
    }

    if (!produkList.length) {
        container.innerHTML = "<p>Belum ada produk.</p>";
        return;
    }

    let html = `
        <table class="keranjang-table">
            <tr>
                <th>Foto</th>
                <th>Nama</th>
                <th>Harga</th>
                <th>Stok</th>
                <th>Status</th>
                <th>Aksi</th>
            </tr>`;

    for (const p of produkList) {
        const fotoHtml = p.gambar_url
            ? `<img src="${escapeHtml(p.gambar_url)}" class="produk-thumb" alt="">`
            : '❌';

        const statusBadge = p.is_po
            ? '⏳ PO'
            : (p.is_ready ? '✅ Ready' : '❌ Habis');

        html += `<tr>
            <td class="kolom-foto">${fotoHtml}</td>
            <td><strong>${escapeHtml(p.nama)}</strong><br><small class="produk-kategori">${escapeHtml(p.kategori || '-')}</small></td>
            <td>Rp${p.harga.toLocaleString("id-ID")}</td>
            <td>${p.stok}</td>
            <td>${statusBadge}</td>
            <td>
                <button onclick="bukaEditModal(${p.id})">✏️ Edit</button>
                <button onclick="hapusProduk(${p.id})" class="btn-hapus">🗑️ Hapus</button>
            </td>
        </tr>`;
    }
    html += "</table>";

    html += `
    <div class="pagination">
        <button type="button" onclick="gantiHalamanProduk(-1)" ${halamanProduk <= 1 ? "disabled" : ""}>◀ Sebelumnya</button>
        <span class="pagination-info">Halaman ${halamanProduk}</span>
        <button type="button" onclick="gantiHalamanProduk(1)" ${produkList.length < PER_HALAMAN ? "disabled" : ""}>Berikutnya ▶</button>
    </div>`;

    container.innerHTML = html;
}

function gantiHalamanProduk(arah) {
    halamanProduk += arah;
    if (halamanProduk < 1) halamanProduk = 1;
    muatProduk();
}

/* ---------- Modal edit produk ---------- */

function bukaEditModal(id) {
    const p = PRODUK_CACHE.find((x) => x.id === id);
    if (!p) return;

    document.getElementById("edit-id").value = p.id;
    document.getElementById("edit-nama").value = p.nama;
    document.getElementById("edit-deskripsi").value = p.deskripsi || "";
    document.getElementById("edit-harga").value = p.harga;
    document.getElementById("edit-stok").value = p.stok;
    document.getElementById("edit-kategori").value = p.kategori || "";
    document.getElementById("edit-gambar").value = p.gambar_url || "";
    document.getElementById("edit-ready").checked = p.is_ready ?? true;
    document.getElementById("edit-po").checked = p.is_po ?? false;

    document.getElementById("edit-foto").value = "";
    const preview = document.getElementById("edit-foto-preview");
    if (p.gambar_url) {
        preview.src = p.gambar_url;
        preview.style.display = "block";
    } else {
        preview.style.display = "none";
    }

    document.getElementById("edit-modal").style.display = "flex";
}

function tutupEditModal() {
    document.getElementById("edit-modal").style.display = "none";
}

async function simpanEditProduk() {
    const id = document.getElementById("edit-id").value;

    let gambarUrl = document.getElementById("edit-gambar").value || null;
    try {
        const hasilUpload = await uploadFoto(document.getElementById("edit-foto"));
        if (hasilUpload) gambarUrl = hasilUpload;
    } catch (err) {
        showToast(err.message, "error");
        return;
    }

    const body = {
        nama: document.getElementById("edit-nama").value,
        deskripsi: document.getElementById("edit-deskripsi").value || null,
        harga: parseFloat(document.getElementById("edit-harga").value),
        stok: parseInt(document.getElementById("edit-stok").value),
        kategori: document.getElementById("edit-kategori").value || null,
        gambar_url: gambarUrl,
        is_ready: document.getElementById("edit-ready").checked,
        is_po: document.getElementById("edit-po").checked
    };

    const res = await fetch(`/produk/${id}`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    if (res.ok) {
        showToast("Produk berhasil diperbarui!");
        tutupEditModal();
        muatProduk();
    } else {
        const err = await res.json();
        showToast(formatErrorDetail(err.detail) || "Gagal memperbarui produk", "error");
    }
}

/* ---------- Hapus produk ---------- */

async function hapusProduk(produkId) {
    if (!confirm("Apakah Anda yakin ingin menghapus produk ini?")) return;
    const res = await fetch(`/produk/${produkId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
        showToast("Produk berhasil dihapus!");
    } else {
        showToast("Gagal menghapus produk", "error");
    }
    muatProduk();
}

/* ---------- Form tambah produk ---------- */

document.getElementById("tambah-produk-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("form-msg");
    msg.textContent = "";

    let gambarUrl = document.getElementById("p-gambar").value || null;
    try {
        const hasilUpload = await uploadFoto(document.getElementById("p-foto"));
        if (hasilUpload) gambarUrl = hasilUpload;
    } catch (err) {
        msg.textContent = err.message;
        return;
    }

    const body = {
        nama: document.getElementById("p-nama").value,
        deskripsi: document.getElementById("p-deskripsi").value || null,
        harga: parseFloat(document.getElementById("p-harga").value),
        stok: parseInt(document.getElementById("p-stok").value),
        kategori: document.getElementById("p-kategori").value || null,
        gambar_url: gambarUrl,
        is_ready: document.getElementById("p-ready").checked,
        is_po: document.getElementById("p-po").checked
    };

    const res = await fetch("/produk/", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const err = await res.json();
        msg.textContent = formatErrorDetail(err.detail) || "Gagal menambah produk";
        return;
    }

    showToast("Produk berhasil ditambahkan!");
    document.getElementById("tambah-produk-form").reset();
    document.getElementById("p-ready").checked = true;
    document.getElementById("p-foto-preview").style.display = "none";
    halamanProduk = 1;
    muatProduk();
});

/* ---------- Init ---------- */

(async () => {
    if (await cekAdmin()) muatProduk();
})();
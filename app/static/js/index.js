// app/static/js/index.js — logika halaman utama (/): daftar menu, urutan, pencarian
// Bergantung pada helper global di main.js: escapeHtml, tambahKeKeranjang

let urutanAktif = "semua";

/* ---------- Muat & tampilkan daftar produk ---------- */

async function muatProdukList() {
    const grid = document.getElementById("produk-grid");
    grid.innerHTML = "<p>Memuat menu...</p>";

    try {
        const res = await fetch(`/produk/?urutan=${urutanAktif}&limit=200`);
        const produkList = await res.json();
        renderProdukGrid(produkList);
    } catch (err) {
        grid.innerHTML = "<p>Gagal memuat menu, coba refresh halaman.</p>";
    }
}

function renderProdukGrid(produkList) {
    const grid = document.getElementById("produk-grid");

    if (!produkList.length) {
        grid.innerHTML = "<p>Belum ada produk.</p>";
        return;
    }

    grid.innerHTML = produkList.map((p) => {
        const cariKey = escapeHtml(`${p.nama} ${p.deskripsi || ""} ${p.kategori || ""}`.toLowerCase());
        const foto = p.gambar_url
            ? `<img src="${escapeHtml(p.gambar_url)}" alt="${escapeHtml(p.nama)}">`
            : `<div class="produk-placeholder">🥣</div>`;
        return `
        <div class="produk-card" data-cari="${cariKey}">
            <a href="/menu/${p.id}" class="produk-link">
                <div class="produk-media">
                    ${foto}
                    <span class="harga-stamp">Rp${p.harga.toLocaleString("id-ID")}</span>
                </div>
                <div class="produk-info">
                    <h3>${escapeHtml(p.nama)}</h3>
                    <p class="deskripsi">${escapeHtml(p.deskripsi || "")}</p>
                    <p class="stok">Stok: ${p.stok}</p>
                </div>
            </a>
            <div class="produk-aksi">
                <button onclick="tambahKeKeranjang(${p.id})" ${p.stok === 0 ? "disabled" : ""}>
                    ${p.stok === 0 ? "Habis" : "+ Keranjang"}
                </button>
            </div>
        </div>`;
    }).join("");

    filterProduk();
}

/* ---------- Tab urutan ---------- */

function gantiUrutan(urutan) {
    urutanAktif = urutan;
    document.querySelectorAll("#tab-urutan button").forEach((btn) => {
        btn.classList.toggle("tab-aktif", btn.dataset.urutan === urutan);
    });
    muatProdukList();
}

/* ---------- Pencarian ---------- */

function filterProduk() {
    const kataKunci = document.getElementById("cari-produk").value.trim().toLowerCase();
    const kartuList = document.querySelectorAll("#produk-grid .produk-card");
    let adaYangTampil = false;

    kartuList.forEach((kartu) => {
        const cocok = kartu.dataset.cari.includes(kataKunci);
        kartu.style.display = cocok ? "" : "none";
        if (cocok) adaYangTampil = true;
    });

    document.getElementById("cari-kosong").style.display = (adaYangTampil || kartuList.length === 0) ? "none" : "block";
}

/* ---------- Init ---------- */

muatProdukList();
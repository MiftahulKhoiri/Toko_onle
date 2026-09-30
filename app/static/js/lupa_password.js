// app/static/js/lupa_password.js — logika halaman /lupa-password
// Bergantung pada helper global di main.js: formatErrorDetail

const form = document.getElementById("lupa-password-form");
const pesan = document.getElementById("pesan");
const tombol = document.getElementById("kirim-btn");

// ---------- Hitung mundur kalau kena rate-limit (sama pola-nya kayak login.js) ----------
let hitungMundurTimer = null;

function mulaiHitungMundur(detik) {
    let sisa = detik;
    tombol.disabled = true;
    clearInterval(hitungMundurTimer);

    const tampilkan = () => {
        pesan.style.color = "";
        pesan.textContent = `Terlalu banyak percobaan. Coba lagi dalam ${sisa} detik.`;
    };
    tampilkan();

    hitungMundurTimer = setInterval(() => {
        sisa -= 1;
        if (sisa <= 0) {
            clearInterval(hitungMundurTimer);
            tombol.disabled = false;
            pesan.textContent = "";
            return;
        }
        tampilkan();
    }, 1000);
}

// ---------- Kirim permintaan link reset ----------
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    pesan.style.color = "";
    pesan.textContent = "";

    try {
        const res = await fetch("/auth/lupa-password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });

        if (res.status === 429) {
            const retryAfter = parseInt(res.headers.get("Retry-After") || "60", 10);
            mulaiHitungMundur(retryAfter);
            return;
        }

        const data = await res.json();
        if (!res.ok) {
            pesan.textContent = formatErrorDetail(data.detail) || "Gagal mengirim link reset";
            return;
        }

        pesan.style.color = "#2e7d32";
        pesan.textContent = data.detail;
        form.reset();
    } catch (err) {
        pesan.textContent = "Tidak bisa terhubung ke server";
    }
});
// app/static/js/login.js — logika halaman /login
// Bergantung pada helper global di main.js: formatErrorDetail
// ID Google/Facebook dibaca dari atribut data-* di #halaman-auth (diisi Jinja di login.html)

const halamanAuth = document.getElementById("halaman-auth");
const GOOGLE_CLIENT_ID = halamanAuth.dataset.googleClientId;
const FACEBOOK_APP_ID = halamanAuth.dataset.facebookAppId;
const errorMsg = document.getElementById("error-msg");

// ---------- Tab "Pakai Email" / "Pakai No. HP" ----------
const tabEmail = document.getElementById("tab-email");
const tabTelepon = document.getElementById("tab-telepon");
const formEmail = document.getElementById("login-form");
const formTelepon = document.getElementById("login-form-telepon");

tabEmail.addEventListener("click", () => {
    tabEmail.classList.add("aktif");
    tabTelepon.classList.remove("aktif");
    formEmail.classList.remove("tersembunyi");
    formTelepon.classList.add("tersembunyi");
    errorMsg.textContent = "";
});
tabTelepon.addEventListener("click", () => {
    tabTelepon.classList.add("aktif");
    tabEmail.classList.remove("aktif");
    formTelepon.classList.remove("tersembunyi");
    formEmail.classList.add("tersembunyi");
    errorMsg.textContent = "";
});

// ---------- Hitung mundur kalau kena rate-limit (dipakai bareng 2 form) ----------
let hitungMundurTimer = null;

function mulaiHitungMundur(detik, tombol) {
    let sisa = detik;
    tombol.disabled = true;
    clearInterval(hitungMundurTimer);

    const tampilkan = () => {
        errorMsg.textContent = `Terlalu banyak percobaan. Coba lagi dalam ${sisa} detik.`;
    };
    tampilkan();

    hitungMundurTimer = setInterval(() => {
        sisa -= 1;
        if (sisa <= 0) {
            clearInterval(hitungMundurTimer);
            tombol.disabled = false;
            errorMsg.textContent = "";
            return;
        }
        tampilkan();
    }, 1000);
}

// ---------- Login pakai Email (form lama) ----------
formEmail.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    errorMsg.textContent = "";

    try {
        const res = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
        });

        if (res.status === 429) {
            const retryAfter = parseInt(res.headers.get("Retry-After") || "60", 10);
            mulaiHitungMundur(retryAfter, document.getElementById("login-btn"));
            return;
        }
        if (!res.ok) {
            const err = await res.json();
            errorMsg.textContent = formatErrorDetail(err.detail) || "Login gagal";
            return;
        }
        const data = await res.json();
        localStorage.setItem("access_token", data.access_token);
        window.location.href = "/";
    } catch (err) {
        errorMsg.textContent = "Tidak bisa terhubung ke server";
    }
});

// ---------- Login pakai No. HP ----------
formTelepon.addEventListener("submit", async (e) => {
    e.preventDefault();
    const telepon = document.getElementById("tp-telepon").value;
    const password = document.getElementById("tp-password").value;
    errorMsg.textContent = "";

    try {
        const res = await fetch("/auth/login-telepon", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ telepon, password }),
        });

        if (res.status === 429) {
            const retryAfter = parseInt(res.headers.get("Retry-After") || "60", 10);
            mulaiHitungMundur(retryAfter, document.getElementById("login-btn-telepon"));
            return;
        }
        if (!res.ok) {
            const err = await res.json();
            errorMsg.textContent = formatErrorDetail(err.detail) || "Login gagal";
            return;
        }
        const data = await res.json();
        localStorage.setItem("access_token", data.access_token);
        window.location.href = "/";
    } catch (err) {
        errorMsg.textContent = "Tidak bisa terhubung ke server";
    }
});

// ---------- Dipakai bareng oleh tombol Google & Facebook ----------
async function masukPakaiSosial(endpoint, body) {
    errorMsg.textContent = "";
    try {
        const res = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        if (!res.ok) {
            const err = await res.json();
            errorMsg.textContent = formatErrorDetail(err.detail) || "Gagal masuk";
            return;
        }
        const data = await res.json();
        localStorage.setItem("access_token", data.access_token);
        window.location.href = "/";
    } catch (err) {
        errorMsg.textContent = "Tidak bisa terhubung ke server";
    }
}

// ---------- Tombol Google ----------
if (GOOGLE_CLIENT_ID) {
    window.addEventListener("load", () => {
        if (!window.google || !window.google.accounts) return;
        google.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: (response) => masukPakaiSosial("/auth/google", { credential: response.credential }),
        });
        google.accounts.id.renderButton(
            document.getElementById("g-btn-login"),
            { theme: "outline", size: "large", width: 260, text: "signin_with", locale: "id_ID" }
        );
    });
} else {
    document.getElementById("g-btn-login").remove();
}

// ---------- Tombol Facebook ----------
const btnFacebook = document.getElementById("btn-facebook-login");
if (FACEBOOK_APP_ID) {
    window.fbAsyncInit = function () {
        FB.init({ appId: FACEBOOK_APP_ID, cookie: true, xfbml: false, version: "v19.0" });
    };
    (function (d, s, id) {
        var js, fjs = d.getElementsByTagName(s)[0];
        if (d.getElementById(id)) return;
        js = d.createElement(s); js.id = id;
        js.src = "https://connect.facebook.net/id_ID/sdk.js";
        fjs.parentNode.insertBefore(js, fjs);
    }(document, "script", "facebook-jssdk"));

    btnFacebook.addEventListener("click", () => {
        if (!window.FB) {
            errorMsg.textContent = "Facebook SDK belum siap, coba lagi sebentar";
            return;
        }
        FB.login((response) => {
            if (response.authResponse) {
                masukPakaiSosial("/auth/facebook", { access_token: response.authResponse.accessToken });
            }
        }, { scope: "public_profile,email" });
    });
} else {
    btnFacebook.remove();
}
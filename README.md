# MyApp — Web App Flask (Login, Upload File, Streaming Video, Email SMTP)

Aplikasi web berbasis **Python (Flask)** dengan fitur:
- Registrasi & Login pengguna (password di-hash, tidak disimpan plain text)
- Upload & download file (dokumen, gambar, arsip, video)
- Streaming video dengan dukungan **HTTP Range Request** (bisa di-seek/maju-mundur)
- Kirim file sebagai lampiran **email via SMTP**
- Database via **SQLAlchemy** (default SQLite, bisa ganti PostgreSQL/MySQL)

---

## 1. Struktur Proyek

```
webapp/
├── app/
│   ├── __init__.py     # Application factory
│   ├── models.py       # Model database: User, FileUpload
│   ├── auth.py         # Blueprint: register/login/logout
│   ├── files.py        # Blueprint: upload/download/hapus/kirim email
│   ├── stream.py       # Blueprint: streaming video (Range request)
│   └── mailer.py        # Fungsi kirim email SMTP
├── templates/           # Template HTML (Jinja2)
├── static/css/          # Stylesheet
├── uploads/              # Folder penyimpanan file upload (jangan di-commit isinya)
├── instance/            # Database SQLite disimpan di sini
├── config.py             # Konfigurasi (baca dari environment variable)
├── run.py                # Entry point aplikasi
├── requirements.txt
├── .env.example           # Contoh file environment — SALIN jadi .env
└── .gitignore
```

---

## 2. Instalasi Lokal

```bash
# 1. Buat virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependency
pip install -r requirements.txt

# 3. Salin file environment
cp .env.example .env
# lalu EDIT file .env, isi SECRET_KEY, SMTP_USERNAME, SMTP_PASSWORD, dll.

# 4. Jalankan aplikasi (mode development)
python run.py
```

Buka `http://127.0.0.1:5000` di browser.

---

## 3. PENTING: Konfigurasi SMTP Email

**Jangan pernah menaruh password email langsung di kode.** Semua kredensial SMTP
dibaca dari file `.env` (yang tidak ikut ke Git, lihat `.gitignore`).

Jika pakai **Gmail**:
1. Aktifkan **2-Step Verification** di akun Google Anda.
2. Buat **App Password** di https://myaccount.google.com/apppasswords
3. Masukkan App Password itu (format `xxxx xxxx xxxx xxxx`) ke `SMTP_PASSWORD` di `.env`.
4. **Jangan** gunakan password akun Gmail biasa — Google akan menolaknya untuk SMTP pihak ketiga.

> ⚠️ Jika App Password Anda pernah ter-share/terlihat orang lain (misalnya tanpa sengaja
> ditempel di chat, dokumen, atau kode), **segera revoke** App Password lama tersebut di
> halaman App Passwords Google, lalu buat yang baru.

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=emailanda@gmail.com
SMTP_PASSWORD=xxxxxxxxxxxxxxxx
SMTP_SENDER_NAME=Nama Aplikasi Anda
```

Provider lain (Outlook, Zoho, SMTP kantor, dll.) juga bisa dipakai — tinggal sesuaikan
`SMTP_SERVER` dan `SMTP_PORT`-nya.

---

## 4. Database (MySQL)

Aplikasi ini menggunakan **MySQL**, terhubung lewat driver **PyMySQL** (sudah termasuk
di `requirements.txt`, tidak perlu compile apapun — cocok untuk Windows).

### 4.1 Install MySQL

Kalau belum punya MySQL server:
- **Windows**: install [MySQL Installer](https://dev.mysql.com/downloads/installer/) (pilih MySQL Server).
- **Alternatif tanpa install**: pakai MySQL dari hosting/cloud (contoh: PlanetScale, Railway,
  Aiven, atau MySQL yang disediakan hosting Anda) — tinggal pakai connection string yang mereka berikan.

### 4.2 Buat Database & User

Masuk ke MySQL (lewat MySQL Workbench, phpMyAdmin, atau command line `mysql -u root -p`),
lalu jalankan:

```sql
DROP USER IF EXISTS 'webapp_user'@'localhost';
CREATE USER 'webapp_user'@'localhost' IDENTIFIED BY 'webapp_pass123';
GRANT ALL PRIVILEGES ON webapp_db.* TO 'webapp_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4.3 Isi `.env`

```env
DATABASE_URL=mysql+pymysql://webapp_user:password_yang_kuat@localhost:3306/webapp_db
```

Format lengkapnya: `mysql+pymysql://USER:PASSWORD@HOST:PORT/NAMA_DATABASE`

Ganti `localhost:3306` kalau MySQL Anda ada di server lain atau pakai port berbeda.

### 4.4 Jalankan Aplikasi

Saat `python run.py` dijalankan, aplikasi **otomatis membuat tabel** (`user`, `file_upload`)
di database `webapp_db` tersebut — tidak perlu bikin tabel manual.

> Catatan: database MySQL-nya sendiri (`webapp_db`) harus sudah ada duluan (lewat langkah 4.2)
> sebelum aplikasi dijalankan — aplikasi hanya membuat tabel, bukan membuat database-nya.

---

## 5. Menjalankan di Produksi (Gunicorn)

Development server bawaan Flask **tidak untuk produksi**. Gunakan Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

Jalankan ini di VPS/server Anda (misalnya Ubuntu di DigitalOcean, AWS EC2, Contabo, dll).
Anda bisa juga membungkusnya jadi service `systemd` agar auto-restart.

---

## 6. Menyambungkan ke Cloudflare

Perlu diketahui: **Cloudflare Pages/Workers tidak menjalankan aplikasi Flask (Python)
secara langsung di edge mereka.** Cara yang umum dan direkomendasikan untuk aplikasi
seperti ini adalah lewat **Cloudflare Tunnel**:

```
[Browser User] → [Cloudflare Edge/DNS/SSL] → [Cloudflare Tunnel] → [Server Flask Anda]
```

Cloudflare berperan sebagai reverse proxy + DNS + SSL gratis + proteksi DDoS di depan
server Anda, sementara aplikasi Python tetap jalan di server/VPS Anda sendiri.

### Langkah-langkah:

1. **Siapkan server** (VPS atau komputer Anda) yang menjalankan aplikasi ini lewat Gunicorn,
   misalnya di port `8000`.

2. **Install `cloudflared`** di server tersebut:
   ```bash
   # Ubuntu/Debian
   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
   sudo dpkg -i cloudflared.deb
   ```

3. **Login ke akun Cloudflare Anda:**
   ```bash
   cloudflared tunnel login
   ```

4. **Buat tunnel:**
   ```bash
   cloudflared tunnel create myapp-tunnel
   ```

5. **Konfigurasi tunnel** — buat file `~/.cloudflared/config.yml`:
   ```yaml
   tunnel: <TUNNEL_ID_dari_langkah_4>
   credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

   ingress:
     - hostname: app.namadomainanda.com
       service: http://localhost:8000
     - service: http_status:404
   ```

6. **Arahkan DNS** domain Anda ke tunnel:
   ```bash
   cloudflared tunnel route dns myapp-tunnel app.namadomainanda.com
   ```

7. **Jalankan tunnel:**
   ```bash
   cloudflared tunnel run myapp-tunnel
   ```
   (Bisa juga dijadikan service: `sudo cloudflared service install`)

8. Aplikasi Anda sekarang bisa diakses di `https://app.namadomainanda.com`,
   dengan SSL otomatis dan proteksi dari Cloudflare, tanpa perlu membuka port
   di firewall server Anda.

---

## 7. Catatan Keamanan

- Ganti `SECRET_KEY` di `.env` dengan string acak yang panjang untuk produksi
  (contoh generate: `python -c "import secrets; print(secrets.token_hex(32))"`).
- File `.env` **tidak boleh** ikut ter-commit ke Git (sudah diatur di `.gitignore`).
- Batas ukuran upload diatur di `config.py` (`MAX_CONTENT_LENGTH`, default 500 MB) — sesuaikan
  dengan kebutuhan dan kapasitas server Anda.
- Untuk produksi nyata, pertimbangkan menambahkan: verifikasi email saat registrasi,
  rate-limiting login (mencegah brute force), dan validasi tipe file lebih ketat
  (bukan hanya berdasarkan ekstensi).

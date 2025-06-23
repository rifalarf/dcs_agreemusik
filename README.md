# Sistem Sertifikat Digital

Aplikasi web Flask untuk manajemen dan verifikasi sertifikat kompetensi digital.

---

## Fitur Utama

* **Manajemen Sertifikat:** Buat, kelola, dan atur sertifikat kompetensi digital.
* **Verifikasi Sertifikat:** Fungsionalitas untuk memverifikasi keaslian sertifikat.
* **Autentikasi Pengguna:** Sistem login untuk admin dan pengguna.
* **Database:** Integrasi dengan SQLAlchemy dan Flask-Migrate untuk manajemen database.
* **Kriptografi:** Penggunaan kunci ECDSA untuk penandatanganan sertifikat yang aman.
* **QR/Barcode:** Integrasi `pyzbar` untuk pembacaan kode.

---

## Prasyarat

Sebelum menjalankan aplikasi, pastikan Anda memiliki:

* **Python 3.11+** (Direkomendasikan Python 3.11 karena kompatibilitas deployment)
* **PIP** (Python package installer)
* **Virtualenv** (Sangat direkomendasikan untuk isolasi dependensi)
* **Git** (Untuk kloning repositori)

---

## Tata Cara Instalasi dan Menjalankan Aplikasi (Lokal)

Ikuti langkah-langkah di bawah ini untuk menyiapkan dan menjalankan aplikasi di lingkungan pengembangan lokal Anda:

1.  **Kloning Repositori:**
    ```bash
    git clone <URL_REPOSITORI_ANDA>
    cd dcs_agreemusik-3 # Sesuaikan dengan nama direktori utama proyek Anda
    ```
    Jika Anda mengunduh sebagai ZIP, ekstrak dan navigasikan ke direktori `dcs_agreemusik-3`.

2.  **Buat dan Aktifkan Virtual Environment:**
    Direkomendasikan untuk menggunakan virtual environment agar dependensi proyek terisolasi.
    ```bash
    python -m venv dcs0
    ```
    * **Windows (CMD):**
        ```bash
        dcs0\Scripts\activate
        ```
    * **Windows (PowerShell):**
        ```powershell
        .\dcs0\Scripts\Activate.ps1
        # Jika ada error eksekusi skrip, jalankan: Set-ExecutionPolicy Unrestricted -Scope Process
        ```
    * **Linux/macOS:**
        ```bash
        source dcs0/bin/activate
        ```
    Anda akan melihat `(dcs0)` di awal prompt terminal Anda, menandakan virtual environment aktif.

3.  **Instal Dependensi:**
    Pastikan Anda berada di direktori utama proyek (`dcs_agreemusik-3`) dan virtual environment aktif.
    ```bash
    pip install -r requirements.txt
    ```
    Ini akan menginstal semua paket yang dibutuhkan seperti Flask, SQLAlchemy, Flask-Migrate, Gunicorn, dll.

4.  **Pengaturan Variabel Lingkungan `FLASK_APP`:**
    Flask perlu tahu file mana yang menjadi *entry point* aplikasi Anda.
    * **Windows (CMD):**
        ```bash
        set FLASK_APP=run.py
        ```
    * **Windows (PowerShell):**
        ```powershell
        $env:FLASK_APP = "run.py"
        ```
    * **Linux/macOS:**
        ```bash
        export FLASK_APP=run.py
        ```
    Anda juga bisa meletakkan `FLASK_APP=run.py` di dalam file `.flaskenv` di root proyek agar dimuat otomatis oleh `python-dotenv`.

5.  **Inisialisasi dan Migrasi Database (Menggunakan Flask-Migrate):**
    Perintah-perintah berikut digunakan untuk membuat dan mengelola skema database Anda. **Ini harus dijalankan secara lokal dan folder `migrations/` yang dihasilkan harus di-komit ke Git.**

    * **Inisialisasi Lingkungan Migrasi (hanya perlu dijalankan sekali per proyek):**
        Perintah ini akan membuat direktori `migrations` di proyek Anda.
        ```bash
        flask db init
        ```
    * **Buat File Migrasi Awal:** Setelah model database Anda didefinisikan (misalnya dalam `app/models.py`), jalankan perintah ini untuk menghasilkan skrip migrasi awal.
        ```bash
        flask db migrate -m "Initial database schema"
        ```
        Anda dapat mengganti pesan `-m` sesuai kebutuhan.
    * **Terapkan Migrasi ke Database Lokal:**
        Perintah ini akan menerapkan perubahan dari skrip migrasi ke database lokal Anda, membuat tabel-tabel yang diperlukan.
        ```bash
        flask db upgrade
        ```
    **PENTING:** Setelah menjalankan `flask db init` dan `flask db migrate` secara lokal, pastikan **folder `migrations/` dan seluruh isinya telah di-komit ke repositori Git Anda** sebelum deployment.

6.  **Buat Kunci Kriptografi:**
    Aplikasi ini menggunakan kunci ECDSA untuk menandatangani sertifikat. Jalankan skrip berikut dari direktori utama proyek (`dcs_agreemusik-3`) untuk menghasilkan kunci:
    ```bash
    python generate_keys.py
    ```
    Ini akan membuat direktori `keys` dengan `private_key.pem` dan `public_key.pem` di dalamnya.

7.  **Buat Akun Admin Awal:**
    Setelah database dan tabel siap, jalankan perintah CLI berikut untuk membuat akun admin default (username: `admin`, password: `admin123`, atau sesuai konfigurasi di `config.py` atau environment variable).
    ```bash
    flask create-admin
    ```

8.  **Jalankan Aplikasi (Development Server):**
    Untuk menjalankan aplikasi di lingkungan pengembangan:
    ```bash
    flask run
    ```
    Aplikasi akan tersedia di `http://127.0.0.1:5000/`.

---

## Deployment ke Railway

Aplikasi ini dikonfigurasi untuk deployment menggunakan **Dockerfile** di Railway, yang memberikan kontrol penuh atas lingkungan build dan runtime.

1.  **Pastikan `Dockerfile` ada di root proyek Anda.**
    Konten `Dockerfile` harus mirip dengan yang direkomendasikan:
    ```dockerfile
    # Gunakan base image Python yang sesuai dan stabil.
    FROM python:3.11-slim-buster

    WORKDIR /app

    # Menginstal build dependencies dan library sistem
    RUN apt-get update && apt-get install -y \
        build-essential \
        libpq-dev \
        zlib1g-dev \
        libjpeg-dev \
        libffi-dev \
        libssl-dev \
        libzbar-dev \
        --no-install-recommends && \
        rm -rf /var/lib/apt/lists/*

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . .

    ENV FLASK_APP=run.py
    ENV PORT=8000

    # Perintah setup yang dijalankan selama build Docker image
    RUN flask db upgrade && \
        python generate_keys.py && \
        flask create-admin

    # Perintah start aplikasi
    CMD gunicorn run:app --bind 0.0.0.0:$PORT
    ```

2.  **Siapkan Repositori Git Anda:**
    * Pastikan `requirements.txt` Anda sudah berisi semua dependensi, termasuk `gunicorn`, `Flask-Login`, `Flask-Migrate`, `pyzbar`, `cryptography`, dll.
    * **Pastikan folder `migrations/` beserta isinya sudah di-komit ke repositori Anda.**
    * **Pastikan `Dockerfile` ada di root repositori Anda dan sudah di-komit.**
    * **Hapus file `.python-version`** jika Anda membuatnya sebelumnya.

3.  **Konfigurasi di Railway:**
    * Di dashboard Railway Anda, hubungkan proyek Anda ke repositori Git ini.
    * Railway akan secara otomatis mendeteksi `Dockerfile` dan menggunakannya.
    * **Pastikan Anda telah menghapus atau tidak mengatur variabel lingkungan Nixpacks sebelumnya** seperti `NIXPACKS_START_CMD`, `NIXPACKS_PKGS`, dan `Build Command` di Railway. Semua konfigurasi build dan start sekarang ada di dalam `Dockerfile`.

4.  **Deployment:**
    * Picu deployment baru di Railway. Railway akan membangun Docker image dan menjalankan aplikasi Anda.

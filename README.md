# Sistem Sertifikat Digital

Aplikasi web Flask untuk manajemen dan verifikasi sertifikat kompetensi digital.

## Prasyarat

* Python 3.7+
* PIP (Python package installer)
* Virtualenv (direkomendasikan)
* Git (opsional, untuk kloning)

## Tata Cara Instalasi dan Menjalankan Aplikasi

1.  **Kloning atau Unduh Repositori (Jika Perlu)**
    ```bash
    git clone <URL_REPOSITORI_ANDA>
    cd nama-direktori-proyek
    ```
    Jika Anda mengunduh sebagai ZIP, ekstrak dan navigasikan ke direktori proyek. Direktori utama proyek ini adalah `dcs_agreemusik-3`.

2.  **Buat dan Aktifkan Virtual Environment**
    Direkomendasikan untuk menggunakan virtual environment agar dependensi proyek terisolasi.
    ```bash
    python -m venv dcs0
    ```
    Aktifkan virtual environment:
    * Windows (CMD):
        ```bash
        dcs0\Scripts\activate
        ```
    * Windows (PowerShell):
        ```powershell
        .\dcs0\Scripts\Activate.ps1
        ```
        (Jika ada error eksekusi skrip di PowerShell, jalankan `Set-ExecutionPolicy Unrestricted -Scope Process` terlebih dahulu, lalu coba aktifkan lagi.)
    * Linux/macOS:
        ```bash
        source dcs0/bin/activate
        ```
    Anda akan melihat `(dcs0)` di awal prompt terminal Anda.

3.  **Instal Dependensi**
    Pastikan Anda berada di direktori utama proyek (`dcs_agreemusik-3`) dan virtual environment aktif.
    ```bash
    pip install -r requirements.txt
    ```
    Ini akan menginstal semua paket yang dibutuhkan seperti Flask, SQLAlchemy, Flask-Migrate, dll.

4.  **Pengaturan Variabel Lingkungan `FLASK_APP`**
    Flask perlu tahu file mana yang menjadi entry point aplikasi Anda untuk menemukan perintah CLI.
    * Windows (CMD):
        ```bash
        set FLASK_APP=run.py
        ```
    * Windows (PowerShell):
        ```powershell
        $env:FLASK_APP = "run.py"
        ```
    * Linux/macOS:
        ```bash
        export FLASK_APP=run.py
        ```
    Anda juga bisa meletakkan `FLASK_APP=run.py` di dalam file `.flaskenv` di root proyek agar dimuat otomatis oleh `python-dotenv`.

5.  **Inisialisasi dan Migrasi Database (Menggunakan Flask-Migrate)**
    Perintah-perintah berikut digunakan untuk membuat dan mengelola skema database Anda.

    * **Inisialisasi Lingkungan Migrasi (hanya perlu dijalankan sekali per proyek)**:
        Perintah ini akan membuat direktori `migrations` di proyek Anda.
        ```bash
        flask db init
        ```

    * **Buat File Migrasi Awal**:
        Setelah model database Anda didefinisikan (dalam `app/models.py`), jalankan perintah ini untuk menghasilkan skrip migrasi awal.
        ```bash
        flask db migrate -m "Initial database schema for new environment"
        ```
        Anda dapat mengganti pesan `-m` sesuai kebutuhan.

    * **Terapkan Migrasi ke Database**:
        Perintah ini akan menerapkan perubahan dari skrip migrasi ke database Anda, membuat tabel-tabel yang diperlukan.
        ```bash
        flask db upgrade
        ```

6.  **Buat Kunci Kriptografi**
    Aplikasi ini menggunakan kunci ECDSA untuk menandatangani sertifikat. Jalankan skrip berikut dari direktori utama proyek (`dcs_agreemusik-3`) untuk menghasilkan kunci:
    ```bash
    python generate_keys.py
    ```
    Ini akan membuat direktori `keys` dengan `private_key.pem` dan `public_key.pem` di dalamnya.

7.  **Buat Akun Admin Awal**
    Setelah database dan tabel siap, jalankan perintah CLI berikut untuk membuat akun admin default (username: `admin`, password: `admin123`, atau sesuai konfigurasi di `config.py` atau environment variable).
    ```bash
    flask create-admin
    ```

8.  **Menjalankan Aplikasi**
    Ada dua cara utama untuk menjalankan server pengembangan Flask:

    * **Menggunakan `python run.py` (Direkomendasikan jika `flask run` bermasalah)**:
        Metode ini terbukti berhasil untuk Anda. Pastikan file `run.py` memiliki bagian:
        ```python
        if __name__ == '__main__':
            app.run(debug=True, port=8080) # atau port lain yang Anda inginkan
        ```
       
        Kemudian jalankan:
        ```bash
        python run.py
        ```

    * **Menggunakan `flask run`**:
        Pastikan `FLASK_APP` sudah diatur seperti pada langkah 4.
        ```bash
        # Opsional, untuk mengatur port jika berbeda dari default (5000)
        # PowerShell: $env:FLASK_RUN_PORT="8080"
        # CMD: set FLASK_RUN_PORT=8080
        # Linux/macOS: export FLASK_RUN_PORT=8080

        flask run
        ```
        Jika Anda mengalami error "access forbidden" dengan `flask run`, gunakan metode `python run.py`.

9.  **Akses Aplikasi**
    Buka browser Anda dan navigasikan ke alamat yang ditampilkan di terminal (biasanya `http://127.0.0.1:PORT_ANDA/`, misalnya `http://127.0.0.1:8080/`).

## Konfigurasi Tambahan (Opsional)

* Anda dapat mengubah konfigurasi default (seperti `SECRET_KEY`, kredensial admin default, path database) di `config.py` atau lebih baik lagi, melalui variabel lingkungan.
* File `.env` atau `.flaskenv` dapat digunakan untuk mengatur variabel lingkungan secara otomatis saat aplikasi dimulai (membutuhkan `python-dotenv` yang sudah ada di `requirements.txt`). Contoh isi `.flaskenv`:
    ```
    FLASK_APP=run.py
    FLASK_DEBUG=1
    # SECRET_KEY=kunci_rahasia_anda_yang_kuat
    # DATABASE_URL=sqlite:///path/lain/ke/database.db
    ```

## Troubleshooting

* **`No such command '...'`**: Pastikan `FLASK_APP` sudah diatur dengan benar ke `run.py`.
* **`Error: Python-dotenv could not parse statement...`**: Periksa file `.env` atau `.flaskenv` Anda untuk kesalahan sintaks pada baris yang disebutkan.
* **`An attempt was made to access a socket in a way forbidden by its access permissions`**:
    * Coba ganti port di `app.run(port=XXXX)` dalam `run.py` atau menggunakan `$env:FLASK_RUN_PORT`.
    * Gunakan metode `python run.py` jika `flask run` terus bermasalah.
    * Jalankan terminal sebagai administrator (untuk diagnosis).
    * Periksa pengaturan firewall/antivirus Anda.

Selamat mencoba!****
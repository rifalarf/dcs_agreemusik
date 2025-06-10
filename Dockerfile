# Gunakan base image Python yang sesuai dan stabil.
# 'slim-buster' adalah image berbasis Debian yang ringan.
FROM python:3.11-slim-buster

# Mengatur direktori kerja di dalam container
# Semua operasi selanjutnya akan dilakukan di direktori ini
WORKDIR /app

# Menginstal build dependencies dan library sistem yang dibutuhkan oleh paket Python Anda.
# Ini termasuk:
# - build-essential: untuk kompilator C (gcc), make, dll., yang dibutuhkan oleh banyak paket Python dengan ekstensi C.
# - libpq-dev: diperlukan jika Anda menggunakan PostgreSQL (Flask-SQLAlchemy mungkin membutuhkannya).
# - zlib1g-dev, libjpeg-dev: untuk Pillow (library pemrosesan gambar).
# - libffi-dev, libssl-dev: untuk Cryptography (library kriptografi).
# - libzbar-dev: untuk pyzbar (membaca barcode/QR code).
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

# Menyalin file requirements.txt ke dalam container
# Ini dilakukan sebelum menyalin seluruh kode aplikasi agar layer ini bisa di-cache
# dan tidak perlu diulang jika hanya kode aplikasi yang berubah
COPY requirements.txt .

# Menginstal semua dependensi Python dari requirements.txt
# --no-cache-dir: menghindari penyimpanan cache pip untuk mengurangi ukuran image
# --break-system-packages: (Opsional) Jika ada masalah dengan virtualenv, terkadang membantu di Docker
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin seluruh kode aplikasi dari direktori lokal ke dalam container
COPY . .

# Mengatur variabel lingkungan FLASK_APP agar Flask tahu entry point aplikasi Anda
ENV FLASK_APP=run.py

# Mengatur PORT default. Railway akan secara otomatis override ini dengan $PORT yang sebenarnya.
# Namun, memiliki nilai default baik untuk pengujian lokal atau lingkungan lain.
ENV PORT=8000

# Menjalankan perintah setup yang hanya perlu dijalankan sekali
# (migrasi database, generate keys, buat akun admin).
# Perintah ini akan dieksekusi selama proses build Docker image.
# Pastikan skrip Anda (generate_keys.py, flask create-admin) bersifat idempotent
# (bisa dijalankan berkali-kali tanpa menyebabkan masalah).
# Pastikan juga file migrasi database dari `flask db migrate` sudah ada di repositori Anda.
RUN flask db upgrade && \
    python generate_keys.py && \
    flask create-admin

# Mendefinisikan perintah yang akan dijalankan saat container dimulai
# Menggunakan Gunicorn sebagai WSGI server yang direkomendasikan untuk production.
# run:app mengacu pada objek aplikasi Flask 'app' yang ada di file 'run.py'.
# --bind 0.0.0.0:$PORT: membuat Gunicorn mendengarkan koneksi dari semua interface pada port yang diberikan oleh Railway.
CMD gunicorn run:app --bind 0.0.0.0:$PORT
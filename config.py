import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ganti-dengan-kunci-rahasia-yang-sangat-aman'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Lokasi kunci ECDSA
    PRIVATE_KEY_PATH = os.path.join(basedir, "keys", "private_key.pem")
    PUBLIC_KEY_PATH = os.path.join(basedir, "keys", "public_key.pem")

    # Admin default credentials (HANYA UNTUK INISIALISASI)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'
    ADMIN_NAMA_LENGKAP = 'Administrator Sistem'
# app/models.py
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from .utils_crypto import generate_certificate_data_string, hash_data, sign_data_ecdsa
import base64

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(256), nullable=False)
    nama_lengkap = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='pelajar')

    # --- TAMBAHKAN KOLOM BARU DI SINI ---
    spesialis = db.Column(db.String(50), nullable=True) # Ganti dari spesialis_instrument
    spesialis_level = db.Column(db.String(50), nullable=True)
    # -----------------------------------

    sertifikats = db.relationship('Sertifikat', backref='pemilik', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def is_admin(self):
        return self.role == 'admin'

# ... (Kode Sertifikat tetap sama) ...
class Sertifikat(db.Model):
    __tablename__ = 'sertifikat'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    id_sertifikat = db.Column(db.String(100), unique=True, nullable=False)
    spesialis = db.Column(db.String(100), nullable=False)
    tanggal_terbit = db.Column(db.Date, nullable=False)
    penandatangan = db.Column(db.String(100), nullable=False)
    data_string_untuk_sign = db.Column(db.Text, nullable=True)
    signature_hash = db.Column(db.String(256), nullable=True)
    tanggal_sign = db.Column(db.DateTime, nullable=True)
    pdf_file_path = db.Column(db.String(300), nullable=True)
    # TAMBAHKAN KOLOM INI UNTUK SIDIK JARI FILE
    pdf_file_hash = db.Column(db.String(64), nullable=True, index=True)

    @property
    def tanggal_terbit_id(self):
        """Properti untuk mendapatkan tanggal terbit dalam format Bahasa Indonesia."""
        if not isinstance(self.tanggal_terbit, date):
            return "Tanggal Tidak Valid"
        
        bulan_map = {
            1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
            7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
        }
        return f"{self.tanggal_terbit.day} {bulan_map.get(self.tanggal_terbit.month, '')} {self.tanggal_terbit.year}"

    @staticmethod
    def generate_next_id():
        """
        Membuat ID sertifikat berikutnya dengan format AGXXX (misal: AG001).
        """
        # Cari sertifikat terakhir dengan format AG...
        last_sertifikat = Sertifikat.query.filter(Sertifikat.id_sertifikat.like('AG%')).order_by(Sertifikat.id_sertifikat.desc()).first()
        
        if not last_sertifikat:
            # Jika ini yang pertama
            next_num = 1
        else:
            # Ambil nomor dari ID terakhir dan increment
            try:
                last_num = int(last_sertifikat.id_sertifikat[2:]) # Ambil bagian angka setelah 'AG'
                next_num = last_num + 1
            except (ValueError, IndexError):
                # Fallback jika format ID lama tidak sesuai
                next_num = (Sertifikat.query.count() or 0) + 1

        # Format dengan 3 digit angka (misal: 1 -> 001, 12 -> 012)
        return f"AG{next_num:03d}"

    def __repr__(self):
        return f"Sertifikat('{self.id_sertifikat}', '{self.pemilik.nama_lengkap}')"

    def prepare_and_sign(self, config, private_key_obj):
        """
        Menyiapkan data, menandatangani, dan menyimpan hasilnya ke instance model.
        """
        # 1. Gabungkan data menjadi satu string
        data_string = generate_certificate_data_string(self)
        self.data_string_untuk_sign = data_string

        # 2. Hash data string
        data_hash = hash_data(data_string)

        # 3. Tanda tangani hash untuk mendapatkan signature bytes
        signature_bytes = sign_data_ecdsa(data_hash, private_key_obj)

        # 4. Encode signature ke Base64 (string) sebelum disimpan
        self.signature_hash = base64.b64encode(signature_bytes).decode('utf-8')

        # 5. Set tanggal penandatanganan
        self.tanggal_sign = datetime.utcnow()
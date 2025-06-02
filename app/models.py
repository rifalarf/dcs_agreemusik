# app/models.py
from . import db
from flask_login import UserMixin
from datetime import datetime

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
    spesialis = db.Column(db.String(200), nullable=False)
    tanggal_terbit = db.Column(db.Date, nullable=False)
    nama_lembaga_penerbit = db.Column(db.String(150), nullable=False)
    data_string_untuk_sign = db.Column(db.Text, nullable=True)
    signature_hash = db.Column(db.Text, nullable=True)
    tanggal_sign = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Sertifikat {self.id_sertifikat}>'

    def prepare_and_sign(self, app_config, private_key_obj):
        from .utils_crypto import generate_certificate_data_string, hash_data, sign_data_ecdsa
        import base64
        self.data_string_untuk_sign = generate_certificate_data_string(self)
        data_hash = hash_data(self.data_string_untuk_sign)
        signature_bytes = sign_data_ecdsa(data_hash, private_key_obj)
        self.signature_hash = base64.b64encode(signature_bytes).decode('utf-8')
        self.tanggal_sign = datetime.utcnow()
# app/models.py
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import datetime
# --- PERBAIKAN: Impor objek 'db' yang dibagikan dari __init__.py ---
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    nama_lengkap = db.Column(db.String(100))
    role = db.Column(db.String(20), default='pelajar')
    spesialis = db.Column(db.String(100), nullable=True)
    sertifikats = db.relationship('Sertifikat', backref='pemilik', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    # --- PERBAIKAN: Tambahkan properti ini ---
    @property
    def is_admin(self):
        return self.role == 'admin'

class Sertifikat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_sertifikat = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    spesialis = db.Column(db.String(100), nullable=False)
    tanggal_terbit = db.Column(db.Date, nullable=False)
    penandatangan = db.Column(db.String(100), nullable=False)
    signature_hash = db.Column(db.String(256), nullable=True)
    qr_code_img = db.Column(db.LargeBinary, nullable=True)
    tanggal_sign = db.Column(db.DateTime, nullable=True)
    data_string_untuk_sign = db.Column(db.Text, nullable=True)
    pdf_file_path = db.Column(db.String(300), nullable=True)
    pdf_file_hash = db.Column(db.String(256), nullable=True)

    def __repr__(self):
        return f'<Sertifikat {self.id_sertifikat}>'

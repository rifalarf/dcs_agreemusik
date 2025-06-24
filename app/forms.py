from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional
from .models import User, Sertifikat
from flask_wtf.file import FileField, FileAllowed
from datetime import date

# Definisikan Pilihan Spesialis dengan Opsi "Isi Sendiri"
SPESIALIS_CHOICES = [('', 'Pilih Spesialis (Opsional)')] + \
                     [("PIANO", "PIANO"), ("GITAR", "GITAR"), ("BIOLA", "BIOLA"),
                      ("DRUM", "DRUM"), ("SEKSOFON", "SEKSOFON"), ("UKULELE", "UKULELE"),
                      ("KENDANG", "KENDANG"),
                      ('ISI_SENDIRI', 'Isi Sendiri...')]

# TAMBAHKAN INI: Konstanta untuk pilihan level
LEVEL_CHOICES = [
    ('', '- Pilih Level -'), ('Dasar', 'Dasar'), ('Menengah', 'Menengah'), 
    ('Lanjutan', 'Lanjutan'), ('Akhir', 'Akhir')
]


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ingat Saya')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    nama_lengkap = StringField('Nama Lengkap', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Konfirmasi Password',
                                     validators=[DataRequired(), EqualTo('password')])

    # --- TAMBAHKAN FIELD BARU DI SINI ---
    spesialis = SelectField('Spesialis', choices=SPESIALIS_CHOICES, validators=[Optional()])
    spesialis_custom = StringField('Spesialis Kustom', validators=[Optional()])
    level = SelectField('Level', choices=LEVEL_CHOICES, validators=[Optional()])
    level_custom = StringField('Level Kustom', validators=[Optional()])
    submit = SubmitField('Daftar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username tersebut sudah digunakan. Silakan pilih yang lain.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email tersebut sudah terdaftar. Silakan gunakan email lain.')

class PelajarForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    nama_lengkap = StringField('Nama Lengkap', validators=[DataRequired()])
    password = PasswordField('Password')
    role = SelectField('Role', choices=[('pelajar', 'Pelajar'), ('admin', 'Admin')], default='pelajar')

    # --- TAMBAHKAN FIELD BARU DI SINI ---
    spesialis = SelectField('Spesialis', choices=SPESIALIS_CHOICES, validators=[Optional()])
    spesialis_custom = StringField('Spesialis Kustom', validators=[Optional()])
    level = SelectField('Level', choices=LEVEL_CHOICES, validators=[Optional()])
    level_custom = StringField('Level Kustom', validators=[Optional()])
    # --------------------------------

    submit = SubmitField('Simpan Pelajar')
    pelajar_id = StringField('ID Pelajar', render_kw={'type': 'hidden'})

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(PelajarForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username sudah digunakan.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email sudah digunakan.')

# ... (SertifikatForm tetap sama) ...
class SertifikatForm(FlaskForm):
    user_id = SelectField('Penerima Sertifikat', coerce=str, validators=[DataRequired()])
    # HAPUS VALIDATOR DARI id_sertifikat KARENA AKAN DI-GENERATE OTOMATIS
    id_sertifikat = StringField('Nomor Sertifikat', validators=[Optional(), Length(min=5, max=100)])
    spesialis = StringField('Spesialis', validators=[DataRequired(), Length(min=3, max=100)])
    tanggal_terbit = DateField('Tanggal Terbit', format='%Y-%m-%d', validators=[DataRequired()], default=date.today)
    penandatangan = StringField('Penandatangan', validators=[DataRequired(), Length(min=3, max=100)], default='Shofia Fauziah')
    submit = SubmitField('Simpan Sertifikat')

    def __init__(self, original_sertifikat=None, *args, **kwargs):
        super(SertifikatForm, self).__init__(*args, **kwargs)
        self.original_sertifikat = original_sertifikat
        # Selalu isi pilihan (choices) untuk dropdown pelajar
        self.user_id.choices = [(str(u.id), u.nama_lengkap) for u in User.query.filter_by(role='pelajar').order_by('nama_lengkap').all()]

    def validate_id_sertifikat(self, id_sertifikat):
        """
        Validator kustom untuk ID Sertifikat.
        Memastikan ID unik, kecuali jika ID tidak berubah saat proses edit.
        """
        # Cari sertifikat dengan ID yang diinput dari form
        sertifikat = Sertifikat.query.filter_by(id_sertifikat=id_sertifikat.data).first()

        if sertifikat:
            # Jika kita dalam mode "edit" (original_sertifikat ada)
            if self.original_sertifikat:
                # Jika ID yang ditemukan BUKAN milik sertifikat yang sedang kita edit, maka itu duplikat.
                if self.original_sertifikat.id != sertifikat.id:
                    raise ValidationError('ID sertifikat ini sudah digunakan oleh sertifikat lain.')
            # Jika kita dalam mode "tambah" (original_sertifikat tidak ada), maka itu duplikat.
            else:
                raise ValidationError('ID sertifikat sudah ada.')

class VerifyCertificateForm(FlaskForm):
    # Opsi 1: Upload PDF
    pdf_file_upload = FileField('Unggah File PDF Sertifikat', validators=[
        FileAllowed(['pdf'], 'Hanya file PDF yang diizinkan!'),
        Optional()
    ])

    # Opsi 2: Input Manual
    id_sertifikat = StringField('Nomor Sertifikat (Manual)', validators=[Optional()])
    nama_penerima = StringField('Nama Penerima (Manual)', validators=[Optional()])
    spesialis = SelectField('Spesialis (Manual)', choices=SPESIALIS_CHOICES, validators=[Optional()])
    # PERBAIKAN: Tambahkan field level_spesialis
    level_spesialis = SelectField('Level Spesialis (Manual)', choices=LEVEL_CHOICES, validators=[Optional()])
    tanggal_terbit = DateField('Tanggal Terbit (Manual)', format='%Y-%m-%d', validators=[Optional()])
    penandatangan = StringField('Penandatangan (Manual)', validators=[Optional()])
    qr_content = TextAreaField('Isi QR Code / Signature (Manual)', validators=[Optional()])

    submit = SubmitField('Verifikasi Sertifikat')
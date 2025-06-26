from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FileField, DateField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional, Length
from flask_wtf.file import FileAllowed
from wtforms_sqlalchemy.fields import QuerySelectField
from .models import User, Sertifikat

# --- PERBAIKAN: Merapikan daftar pilihan ---
SPESIALIS_CHOICES = [
    ('', '- Pilih Spesialis -'),
    ("PIANO", "PIANO"),
    ("GITAR", "GITAR"),
    ("BIOLA", "BIOLA"),
    ("DRUM", "DRUM"),
    ("SEKSOFON", "SEKSOFON"),
    ("UKULELE", "UKULELE"),
    ("KENDANG", "KENDANG")
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
    confirm_password = PasswordField('Konfirmasi Password', validators=[DataRequired(), EqualTo('password')])

    # --- PERBAIKAN: Hapus field _custom yang membingungkan ---
    spesialis = SelectField('Spesialis', choices=SPESIALIS_CHOICES, validators=[Optional()])
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
    password = PasswordField('Password Baru (opsional)')
    role = SelectField('Role', choices=[('pelajar', 'Pelajar'), ('admin', 'Admin')], validators=[DataRequired()])
    spesialis = SelectField('Spesialis', choices=SPESIALIS_CHOICES, validators=[Optional()])
    submit = SubmitField('Simpan')

    # --- PERBAIKAN: Validasi unik yang lebih baik untuk edit ---
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


class SertifikatForm(FlaskForm):
    user_id = QuerySelectField('Nama Pelajar', query_factory=lambda: User.query.filter_by(role='pelajar').all(), get_label='nama_lengkap', allow_blank=False, validators=[DataRequired()])
    spesialis = SelectField('Spesialis', choices=SPESIALIS_CHOICES, validators=[DataRequired(message="Pilih salah satu spesialis.")])
    tanggal_terbit = DateField('Tanggal Terbit', format='%Y-%m-%d', validators=[DataRequired()])
    penandatangan = StringField('Penandatangan', validators=[DataRequired()])
    id_sertifikat = StringField('ID Sertifikat', render_kw={'readonly': True})
    
    # --- PERBAIKAN: Jadikan Nomor Sertifikat opsional di form ---
    # Nomor ini akan digenerate otomatis oleh sistem saat membuat sertifikat baru.
    submit = SubmitField('Simpan Sertifikat')

    def __init__(self, original_sertifikat=None, *args, **kwargs):
        super(SertifikatForm, self).__init__(*args, **kwargs)
        self.original_sertifikat = original_sertifikat

    def validate_id_sertifikat(self, id_sertifikat):
        sertifikat = Sertifikat.query.filter_by(id_sertifikat=id_sertifikat.data).first()
        if sertifikat:
            if self.original_sertifikat:
                if self.original_sertifikat.id != sertifikat.id:
                    raise ValidationError('ID sertifikat ini sudah digunakan oleh sertifikat lain.')
            else:
                raise ValidationError('ID sertifikat sudah ada.')


class VerifyCertificateForm(FlaskForm):
    pdf_file_upload = FileField('Unggah PDF Sertifikat', validators=[
        Optional(),
        FileAllowed(['pdf'], 'Hanya file PDF yang diizinkan!')
    ])
    id_sertifikat = StringField('ID Sertifikat', validators=[Optional()])
    nama_penerima = StringField('Nama Penerima', validators=[Optional()])
    tanggal_terbit = DateField('Tanggal Terbit', format='%Y-%m-%d', validators=[Optional()])
    spesialis = SelectField('Spesialis', choices=SPESIALIS_CHOICES, validators=[Optional()])
    penandatangan = StringField('Penandatangan', validators=[Optional()])
    qr_content = TextAreaField('Konten QR Code', validators=[Optional()])
    submit = SubmitField('Verifikasi Sertifikat')


# --- Form untuk Pelajar Mengedit Profil Mereka Sendiri ---
class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    nama_lengkap = StringField('Nama Lengkap', validators=[DataRequired()])
    password = PasswordField('Password Baru (opsional)')
    spesialis = SelectField('Spesialis', choices=SPESIALIS_CHOICES, validators=[Optional()])
    submit = SubmitField('Simpan Perubahan')

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
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
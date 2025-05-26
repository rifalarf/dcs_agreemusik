from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional
from .models import User
from flask_wtf.file import FileField, FileAllowed

# Definisikan Pilihan Spesialis dengan Opsi "Isi Sendiri"
SPESIALIS_CHOICES = [('', 'Pilih Spesialis (Opsional)')] + \
                     [("PIANO", "PIANO"), ("GITAR", "GITAR"), ("BIOLA", "BIOLA"),
                      ("DRUM", "DRUM"), ("SEKSOFON", "SEKSOFON"), ("UKULELE", "UKULELE"),
                      ("KENDANG", "KENDANG"),
                      ('ISI_SENDIRI', 'Isi Sendiri...')]

LEVEL_CHOICES = [('', 'Pilih Level (Opsional)')] + \
                [("PEMULA", "PEMULA"), ("MENENGAH", "MENENGAH"), ("AKHIR", "AKHIR"),
                 ('ISI_SENDIRI', 'Isi Sendiri...')]


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
    password = PasswordField('Password (kosongkan jika tidak ingin mengubah)')
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

# ... (SertifikatForm dan VerifyCertificateForm tetap sama) ...
class SertifikatForm(FlaskForm):
    user_id = SelectField('Pelajar Penerima', coerce=int, validators=[DataRequired(message="Harap pilih pelajar penerima.")])
    id_sertifikat = StringField('ID Sertifikat', validators=[DataRequired()])
    spesialis = StringField('Spesialis', validators=[DataRequired()])
    tanggal_terbit = DateField('Tanggal Terbit', format='%Y-%m-%d', validators=[DataRequired()])
    nama_lembaga_penerbit = StringField('Nama Lembaga Penerbit', validators=[DataRequired()])
    submit = SubmitField('Simpan & Tanda Tangani Sertifikat')
    sertifikat_id = StringField('ID Internal Sertifikat', render_kw={'type': 'hidden'})
    def __init__(self, original_id_sertifikat=None, *args, **kwargs):
        super(SertifikatForm, self).__init__(*args, **kwargs)
        self.original_id_sertifikat = original_id_sertifikat
        pelajar_choices = [(u.id, u.nama_lengkap) for u in User.query.filter_by(role='pelajar').order_by(User.nama_lengkap).all()]
        self.user_id.choices = pelajar_choices
    def validate_id_sertifikat(self, id_sertifikat):
        from .models import Sertifikat
        if id_sertifikat.data != self.original_id_sertifikat:
            sertifikat = Sertifikat.query.filter_by(id_sertifikat=id_sertifikat.data).first()
            if sertifikat:
                raise ValidationError('ID sertifikat sudah ada.')
    def validate_user_id(self, field):
        if not self.user_id.choices:
             raise ValidationError("Tidak ada pelajar tersedia untuk dipilih.")
class VerifyCertificateForm(FlaskForm):
    id_sertifikat = StringField('ID Sertifikat')
    qr_content = TextAreaField('Isi QR Code (Signature Base64)')
    qr_file_upload = FileField('Atau Unggah Gambar QR Code', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Hanya gambar (JPG, PNG, GIF)!')
    ])
    submit = SubmitField('Verifikasi Sertifikat')
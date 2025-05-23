from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from .models import User

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
    submit = SubmitField('Simpan Pelajar')
    
    # Untuk mode edit, kita perlu id pelajar
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


class SertifikatForm(FlaskForm):
    user_id = SelectField('Pelajar Penerima', coerce=int, validators=[DataRequired()])
    nomor_sertifikat = StringField('Nomor Sertifikat', validators=[DataRequired()])
    nama_kompetensi = StringField('Nama Kompetensi', validators=[DataRequired()])
    tanggal_terbit = DateField('Tanggal Terbit', format='%Y-%m-%d', validators=[DataRequired()])
    nama_lembaga_penerbit = StringField('Nama Lembaga Penerbit', validators=[DataRequired()])
    submit = SubmitField('Simpan & Tanda Tangani Sertifikat')

    # Untuk mode edit
    sertifikat_id = StringField('ID Sertifikat', render_kw={'type': 'hidden'})

    def __init__(self, original_nomor_sertifikat=None, *args, **kwargs):
        super(SertifikatForm, self).__init__(*args, **kwargs)
        self.original_nomor_sertifikat = original_nomor_sertifikat
        # Populate choices untuk user_id
        self.user_id.choices = [(u.id, u.nama_lengkap) for u in User.query.filter_by(role='pelajar').order_by(User.nama_lengkap).all()]


    def validate_nomor_sertifikat(self, nomor_sertifikat):
        from .models import Sertifikat # Local import to avoid circular dependency
        if nomor_sertifikat.data != self.original_nomor_sertifikat:
            sertifikat = Sertifikat.query.filter_by(nomor_sertifikat=nomor_sertifikat.data).first()
            if sertifikat:
                raise ValidationError('Nomor sertifikat sudah ada.')

class VerifyCertificateForm(FlaskForm):
    nomor_sertifikat = StringField('Nomor Sertifikat', validators=[DataRequired()])
    qr_content = TextAreaField('Isi QR Code (Signature Base64)', validators=[DataRequired()])
    submit = SubmitField('Verifikasi Sertifikat')
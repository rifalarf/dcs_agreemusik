from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from .decorators import pelajar_required
from .models import Sertifikat
from .utils_crypto import generate_qr_code_from_signature_text

pelajar_bp = Blueprint('pelajar', __name__)

@pelajar_bp.route('/dashboard')
@login_required
@pelajar_required
def dashboard():
    jumlah_sertifikat = Sertifikat.query.filter_by(user_id=current_user.id).count()
    return render_template('pelajar/dashboard.html', title='Dashboard Pelajar', jumlah_sertifikat=jumlah_sertifikat)

@pelajar_bp.route('/sertifikat')
@login_required
@pelajar_required
def list_sertifikat_pelajar():
    sertifikats = Sertifikat.query.filter_by(user_id=current_user.id).order_by(Sertifikat.tanggal_terbit.desc()).all()
    return render_template('pelajar/list_sertifikat_pelajar.html', title='Sertifikat Saya', sertifikats=sertifikats)

@pelajar_bp.route('/sertifikat/detail/<int:sertifikat_id>')
@login_required
@pelajar_required
def detail_sertifikat_pelajar(sertifikat_id):
    sertifikat = Sertifikat.query.filter_by(id=sertifikat_id, user_id=current_user.id).first_or_404()
    qr_code_img_b64 = None
    if sertifikat.signature_hash:
        qr_code_img_b64 = generate_qr_code_from_signature_text(sertifikat.signature_hash)
    return render_template('pelajar/detail_sertifikat_pelajar.html', title=f'Detail Sertifikat {sertifikat.nomor_sertifikat}', sertifikat=sertifikat, qr_code_img_b64=qr_code_img_b64)
from flask import Blueprint, render_template, current_app, flash, redirect, url_for # Tambah redirect, url_for, flash
from flask_login import login_required, current_user
from .decorators import pelajar_required
from .models import Sertifikat
from .utils_crypto import generate_qr_code_with_details
from flask import send_file
# Hapus utils_certificate jika tidak pakai PNG, atau biarkan jika masih perlu
from .utils_certificate import generate_certificate_image
import io

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
    # --- PERUBAHAN DI SINI ---
    if sertifikat.signature_hash and sertifikat.id_sertifikat:
        qr_code_img_b64 = generate_qr_code_with_details(sertifikat.id_sertifikat, sertifikat.signature_hash)
    # --- PERUBAHAN DI SINI ---
    return render_template('pelajar/detail_sertifikat_pelajar.html', title=f'Detail Sertifikat {sertifikat.id_sertifikat}', sertifikat=sertifikat, qr_code_img_b64=qr_code_img_b64)

@pelajar_bp.route('/sertifikat/cetak/<int:sertifikat_id>')
@login_required
@pelajar_required
def cetak_sertifikat_pelajar(sertifikat_id):
    sertifikat = Sertifikat.query.filter_by(id=sertifikat_id, user_id=current_user.id).first_or_404()

    if not sertifikat.signature_hash:
        flash('Sertifikat ini belum siap atau tidak bisa dicetak saat ini.', 'warning')
        return redirect(url_for('pelajar.detail_sertifikat_pelajar', sertifikat_id=sertifikat.id))

    # --- PERBAIKAN: Gunakan generate_certificate_image (Asumsi masih PNG) ---
    img_pil = generate_certificate_image(sertifikat) # Pastikan utils_certificate sudah diubah
    if img_pil is None:
        flash('Gagal membuat gambar sertifikat. Silakan coba lagi atau hubungi admin.', 'danger')
        return redirect(url_for('pelajar.detail_sertifikat_pelajar', sertifikat_id=sertifikat.id))

    img_io = io.BytesIO()
    img_pil.save(img_io, 'PNG')
    img_io.seek(0)

    # --- PERUBAHAN DI SINI ---
    download_name = f'Sertifikat_{sertifikat.id_sertifikat.replace("/", "-")}_{sertifikat.pemilik.nama_lengkap.replace(" ", "_")}.png'
    return send_file(
        img_io,
        mimetype='image/png',
        as_attachment=True,
        download_name=download_name
    )
    # -------------------------
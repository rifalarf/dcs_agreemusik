from flask import Blueprint, render_template, flash, redirect, url_for, send_file, current_app, request
from flask_login import login_required, current_user
from .models import Sertifikat, User
from .forms import ProfileForm
from . import db
import os

pelajar_bp = Blueprint('pelajar', __name__, url_prefix='/pelajar')

@pelajar_bp.route('/dashboard')
@login_required
def dashboard():
    """Menampilkan dashboard pelajar dengan ringkasan."""
    # PERBAIKAN: Hanya hitung jumlah sertifikat untuk efisiensi
    jumlah_sertifikat = Sertifikat.query.filter_by(user_id=current_user.id).count()
    return render_template('pelajar/dashboard.html', title='Dashboard Pelajar', jumlah_sertifikat=jumlah_sertifikat)

@pelajar_bp.route('/sertifikat')
@login_required
def list_sertifikat_pelajar():
    """Menampilkan daftar semua sertifikat milik pelajar yang sedang login."""
    sertifikats = Sertifikat.query.filter_by(user_id=current_user.id).order_by(Sertifikat.tanggal_terbit.desc()).all()
    return render_template('pelajar/list_sertifikat_pelajar.html', title='Daftar Sertifikat Saya', sertifikats=sertifikats)

@pelajar_bp.route('/sertifikat/detail/<int:sertifikat_id>')
@login_required
def detail_sertifikat_pelajar(sertifikat_id):
    """Menampilkan detail sebuah sertifikat untuk pelajar."""
    sertifikat = Sertifikat.query.filter_by(id=sertifikat_id, user_id=current_user.id).first_or_404()
    
    # PERBAIKAN: Encode gambar QR dari database (binary) ke base64 untuk ditampilkan di HTML
    qr_code_img_b64 = None
    if sertifikat.qr_code_img:
        import base64
        qr_code_img_b64 = base64.b64encode(sertifikat.qr_code_img).decode('utf-8')

    return render_template('pelajar/detail_sertifikat_pelajar.html', title='Detail Sertifikat', sertifikat=sertifikat, qr_code_img_b64=qr_code_img_b64)

# PERBAIKAN: Ganti nama fungsi agar sesuai dengan yang dipanggil oleh template
@pelajar_bp.route('/sertifikat/lihat/<int:sertifikat_id>')
@login_required
def cetak_sertifikat_pelajar(sertifikat_id):
    """
    Menyajikan file PDF sertifikat yang sudah ada untuk pelajar yang bersangkutan.
    """
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)

    # Otorisasi: Pastikan pelajar hanya bisa melihat sertifikat miliknya sendiri
    if sertifikat.user_id != current_user.id:
        flash('Anda tidak memiliki izin untuk mengakses sertifikat ini.', 'danger')
        return redirect(url_for('pelajar.dashboard'))

    # Periksa apakah path file PDF ada dan file-nya benar-benar ada di server
    if sertifikat.pdf_file_path and os.path.exists(sertifikat.pdf_file_path):
        try:
            return send_file(
                sertifikat.pdf_file_path,
                as_attachment=False,  # Tampilkan di browser, jangan langsung download
                download_name=f'Sertifikat_{sertifikat.id_sertifikat.replace("/", "_")}.pdf',
                mimetype='application/pdf'
            )
        except Exception as e:
            current_app.logger.error(f"Gagal mengirim file PDF untuk pelajar: {e}")
            flash('Terjadi kesalahan saat mencoba menampilkan PDF.', 'danger')
            return redirect(url_for('pelajar.dashboard'))
    else:
        flash('File PDF untuk sertifikat ini tidak ditemukan. Silakan hubungi admin.', 'warning')
        return redirect(url_for('pelajar.dashboard'))

@pelajar_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Menampilkan form dan memproses pembaruan profil pelajar."""
    form = ProfileForm(original_username=current_user.username, original_email=current_user.email)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.nama_lengkap = form.nama_lengkap.data
        current_user.spesialis = form.spesialis.data
        if form.password.data:
            current_user.set_password(form.password.data)
        db.session.commit()
        flash('Profil Anda telah berhasil diperbarui.', 'success')
        return redirect(url_for('pelajar.dashboard'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.nama_lengkap.data = current_user.nama_lengkap
        form.spesialis.data = current_user.spesialis
    return render_template('pelajar/edit_profile.html', title='Edit Profil', form=form)
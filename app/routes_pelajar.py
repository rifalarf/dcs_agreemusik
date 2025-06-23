from flask import Blueprint, render_template, flash, redirect, url_for, send_file, current_app
from flask_login import login_required, current_user
from .models import Sertifikat
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

@pelajar_bp.route('/sertifikat/lihat/<int:sertifikat_id>')
@login_required
def lihat_sertifikat(sertifikat_id):
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
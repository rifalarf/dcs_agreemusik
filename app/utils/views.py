from flask import send_file, flash, redirect, url_for, current_app
from functools import wraps
import os

def serve_pdf(sertifikat, user, admin_view=False):
    """
    Menyajikan file PDF sertifikat dengan logika otorisasi.
    """
    if not admin_view and sertifikat.user_id != user.id:
        flash('Anda tidak memiliki izin untuk mengakses sertifikat ini.', 'danger')
        return redirect(url_for('pelajar.dashboard'))

    if sertifikat.pdf_file_path and os.path.exists(sertifikat.pdf_file_path):
        try:
            return send_file(
                sertifikat.pdf_file_path,
                as_attachment=False,
                download_name=f'Sertifikat_{sertifikat.id_sertifikat.replace("/", "_")}.pdf',
                mimetype='application/pdf'
            )
        except Exception as e:
            current_app.logger.error(f"Gagal mengirim file PDF: {e}")
            flash('Terjadi kesalahan saat mencoba menampilkan PDF.', 'danger')
            return redirect(url_for('admin.manage_sertifikat') if admin_view else url_for('pelajar.dashboard'))
    else:
        flash('File PDF untuk sertifikat ini tidak ditemukan. Silakan hubungi admin.', 'warning')
        return redirect(url_for('admin.manage_sertifikat') if admin_view else url_for('pelajar.dashboard'))

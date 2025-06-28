import json
import os
import base64
import datetime
import hashlib
from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for, current_app, send_file, jsonify)
from flask_login import login_required
from datetime import datetime

from . import db
from .decorators import admin_required
from .forms import PelajarForm, SertifikatForm
from .models import Sertifikat, User
from .utils_crypto import create_data_string, sign_data, generate_qr_code_from_signature_text, load_private_key
from .utils_certificate import generate_certificate_pdf
from cryptography.hazmat.primitives import serialization

admin_bp = Blueprint('admin', __name__)

def generate_next_sertifikat_id():
    """Membuat ID sertifikat berikutnya dengan format AGXXX."""
    last_sertifikat = Sertifikat.query.filter(Sertifikat.id_sertifikat.like('AG%')).order_by(Sertifikat.id.desc()).first()
    if last_sertifikat:
        last_num_str = ''.join(filter(str.isdigit, last_sertifikat.id_sertifikat))
        last_num = int(last_num_str) if last_num_str else 0
        new_num = last_num + 1
    else:
        new_num = 1
    return f"AG{new_num:03d}"

# --- PERBAIKAN TOTAL: Logika eksplisit dipindahkan ke sini ---
def process_and_generate_pdf(sertifikat, private_key_obj):
    """Menandatangani sertifikat, membuat QR, dan menghasilkan file PDF secara eksplisit."""
    
    # Langkah 1: Buat string data dari objek sertifikat.
    data_to_sign = create_data_string(sertifikat)
    if not data_to_sign:
        raise ValueError("Data untuk ditandatangani tidak boleh kosong.")
    sertifikat.data_string_untuk_sign = data_to_sign

    # Langkah 2: Buat signature hash dari string data.
    signature = sign_data(data_to_sign, private_key_obj)
    if not signature:
        raise ValueError("Gagal menghasilkan signature hash.")
    sertifikat.signature_hash = signature

    # Langkah 3: Buat QR code dari signature hash.
    qr_image_bytes = generate_qr_code_from_signature_text(signature)
    if not qr_image_bytes:
        raise ValueError("Gagal membuat gambar QR code dari signature.")
    sertifikat.qr_code_img = qr_image_bytes
    
    # Langkah 4: Catat waktu penandatanganan.
    sertifikat.tanggal_sign = datetime.utcnow()

    # Langkah 5: Buat file PDF menggunakan WeasyPrint.
    qr_b64 = base64.b64encode(sertifikat.qr_code_img).decode('utf-8')
    pdf_bytes = generate_certificate_pdf(sertifikat, qr_b64)
    
    # --- PERBAIKAN: Hitung dan simpan hash dari PDF yang di-generate ---
    sertifikat.pdf_file_hash = hashlib.sha256(pdf_bytes).hexdigest()

    pdf_dir = os.path.join(current_app.instance_path, 'sertifikat_pdf')
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f"{sertifikat.id_sertifikat}.pdf")
    with open(pdf_path, 'wb') as f:
        f.write(pdf_bytes)
    
    sertifikat.pdf_file_path = pdf_path

# --- ROUTES (Menggunakan helper di atas) ---
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html', title='Admin Dashboard')

# --- Manajemen Pelajar ---
@admin_bp.route('/pelajar')
@login_required
@admin_required
def manage_pelajar():
    page = request.args.get('page', 1, type=int)
    pelajars = User.query.order_by(User.nama_lengkap).paginate(page=page, per_page=10)
    return render_template('admin/manage_pelajar.html', title='Manajemen Pelajar', pelajars=pelajars)

@admin_bp.route('/pelajar/tambah', methods=['GET', 'POST'])
@login_required
@admin_required
def tambah_pelajar():
    form = PelajarForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            nama_lengkap=form.nama_lengkap.data,
            role=form.role.data,
            spesialis=form.spesialis.data or None
        )
        if form.password.data:
            user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Pelajar {user.nama_lengkap} berhasil ditambahkan.', 'success')
        return redirect(url_for('admin.manage_pelajar'))
    return render_template('admin/form_pelajar.html', title='Tambah Pelajar', form=form, legend='Tambah Pelajar Baru')


@admin_bp.route('/pelajar/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_pelajar(user_id):
    user = User.query.get_or_404(user_id)
    form = PelajarForm(original_username=user.username, original_email=user.email)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.nama_lengkap = form.nama_lengkap.data
        user.role = form.role.data
        user.spesialis = form.spesialis.data or None
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash(f'Data pelajar {user.nama_lengkap} berhasil diperbarui.', 'success')
        return redirect(url_for('admin.manage_pelajar'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.nama_lengkap.data = user.nama_lengkap
        form.role.data = user.role
        form.spesialis.data = user.spesialis
    return render_template('admin/form_pelajar.html', title='Edit Pelajar', form=form, legend=f'Edit Pelajar: {user.nama_lengkap}')

@admin_bp.route('/pelajar/hapus/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def hapus_pelajar(user_id):
    user = User.query.get_or_404(user_id)
    if user.username == current_app.config.get('ADMIN_USERNAME'):
        flash('Tidak dapat menghapus akun admin utama.', 'danger')
        return redirect(url_for('admin.manage_pelajar'))

    db.session.delete(user)
    db.session.commit()
    flash(f'Pelajar {user.nama_lengkap} dan sertifikat terkait berhasil dihapus.', 'success')
    return redirect(url_for('admin.manage_pelajar'))


# --- Manajemen Sertifikat ---
@admin_bp.route('/sertifikat')
@login_required
@admin_required
def manage_sertifikat():
    page = request.args.get('page', 1, type=int)
    sertifikats = Sertifikat.query.order_by(Sertifikat.id.desc()).paginate(page=page, per_page=10)
    return render_template('admin/manage_sertifikat.html', title='Manajemen Sertifikat', sertifikats=sertifikats)

@admin_bp.route('/sertifikat/tambah', methods=['GET', 'POST'])
@login_required
@admin_required
def tambah_sertifikat():
    form = SertifikatForm()
    if form.validate_on_submit():
        new_sertifikat = Sertifikat(
            id_sertifikat=generate_next_sertifikat_id(), user_id=form.user_id.data.id,
            spesialis=form.spesialis.data,
            tanggal_terbit=form.tanggal_terbit.data, penandatangan=form.penandatangan.data
        )
        db.session.add(new_sertifikat)
        db.session.flush()

        try:
            private_key_path = current_app.config.get('PRIVATE_KEY_PATH')
            # --- PERBAIKAN: Gunakan fungsi loader yang konsisten dari utils ---
            private_key_obj = load_private_key(private_key_path)
            
            if not private_key_obj:
                flash('Gagal memuat kunci privat. Operasi tidak dapat dilanjutkan.', 'danger')
                return redirect(url_for('admin.tambah_sertifikat'))

            process_and_generate_pdf(new_sertifikat, private_key_obj)
            
            db.session.commit()
            flash(f'Sertifikat {new_sertifikat.id_sertifikat} berhasil dibuat.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Gagal memproses sertifikat: {e}")
            flash(f"Gagal memproses sertifikat: {e}", "danger")
            return redirect(url_for('admin.tambah_sertifikat'))
        
        return redirect(url_for('admin.manage_sertifikat'))

    pelajar_users = User.query.filter_by(role='pelajar').all()
    pelajar_data = {user.id: {'spesialis': user.spesialis} for user in pelajar_users}
    pelajar_data_json = json.dumps(pelajar_data)
    return render_template('admin/form_sertifikat.html', title='Buat Sertifikat Baru', form=form, pelajar_data_json=pelajar_data_json)


@admin_bp.route('/sertifikat/edit/<int:sertifikat_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_sertifikat(sertifikat_id):
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)
    form = SertifikatForm(original_sertifikat=sertifikat)
    if form.validate_on_submit():
        sertifikat.user_id = form.user_id.data.id
        sertifikat.spesialis = form.spesialis.data
        sertifikat.tanggal_terbit = form.tanggal_terbit.data
        sertifikat.penandatangan = form.penandatangan.data
        
        try:
            private_key_path = current_app.config.get('PRIVATE_KEY_PATH')
            with open(private_key_path, "rb") as key_file:
                private_key_obj = serialization.load_pem_private_key(key_file.read(), password=None)
            
            process_and_generate_pdf(sertifikat, private_key_obj)
            
            db.session.commit()
            flash(f'Sertifikat {sertifikat.id_sertifikat} berhasil diperbarui.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Gagal memperbarui sertifikat: {e}")
            flash(f"Gagal memperbarui sertifikat: {e}", "danger")
            return redirect(url_for('admin.edit_sertifikat', sertifikat_id=sertifikat_id))

        return redirect(url_for('admin.manage_sertifikat'))
    elif request.method == 'GET':
        form.user_id.data = sertifikat.pemilik
        form.spesialis.data = sertifikat.spesialis
        form.tanggal_terbit.data = sertifikat.tanggal_terbit
        form.penandatangan.data = sertifikat.penandatangan
        form.id_sertifikat.data = sertifikat.id_sertifikat

    pelajar_users = User.query.filter_by(role='pelajar').all()
    pelajar_data = {user.id: {'spesialis': user.spesialis} for user in pelajar_users}
    pelajar_data_json = json.dumps(pelajar_data)
    return render_template('admin/form_sertifikat.html', title='Edit Sertifikat', form=form, pelajar_data_json=pelajar_data_json)

@admin_bp.route('/sertifikat/detail/<int:sertifikat_id>')
@login_required
@admin_required
def detail_sertifikat_admin(sertifikat_id):
    """Menampilkan detail sebuah sertifikat, termasuk QR code-nya."""
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)
    qr_code_img_b64 = None
    if sertifikat.signature_hash:
        # PERBAIKAN: Generate bytes dan encode ke base64 untuk ditampilkan di HTML
        qr_bytes = generate_qr_code_from_signature_text(sertifikat.signature_hash)
        if qr_bytes:
            qr_code_img_b64 = base64.b64encode(qr_bytes).decode('utf-8')
    
    return render_template('admin/detail_sertifikat.html', title='Detail Sertifikat', sertifikat=sertifikat, qr_code_img_b64=qr_code_img_b64)


@admin_bp.route('/sertifikat/cetak/<int:sertifikat_id>')
@login_required
@admin_required
def cetak_sertifikat_admin(sertifikat_id):
    """
    Menyajikan file PDF sertifikat yang sudah ada.
    """
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)

    # Periksa apakah path file PDF ada di database dan file-nya benar-benar ada di server
    if sertifikat.pdf_file_path and os.path.exists(sertifikat.pdf_file_path):
        try:
            return send_file(
                sertifikat.pdf_file_path,
                as_attachment=False,  # Tampilkan di browser, jangan langsung download
                download_name=f'Sertifikat_{sertifikat.id_sertifikat.replace("/", "_")}.pdf',
                mimetype='application/pdf'
            )
        except Exception as e:
            current_app.logger.error(f"Gagal mengirim file PDF: {e}")
            flash('Terjadi kesalahan saat mencoba menampilkan PDF.', 'danger')
            return redirect(url_for('admin.manage_sertifikat'))
    else:
        flash('File PDF untuk sertifikat ini tidak ditemukan. Silakan buat ulang sertifikat jika perlu.', 'warning')
        return redirect(url_for('admin.manage_sertifikat'))


@admin_bp.route('/sertifikat/hapus/<int:sertifikat_id>', methods=['POST'])
@login_required
@admin_required
def hapus_sertifikat(sertifikat_id):
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)
    if sertifikat.pdf_file_path and os.path.exists(sertifikat.pdf_file_path):
        os.remove(sertifikat.pdf_file_path)
    db.session.delete(sertifikat)
    db.session.commit()
    flash(f'Sertifikat {sertifikat.id_sertifikat} berhasil dihapus.', 'success')
    return redirect(url_for('admin.manage_sertifikat'))

@admin_bp.route('/pelajar/<int:user_id>/get_spesialis', methods=['GET'])
@login_required
@admin_required
def get_pelajar_spesialis(user_id):
    """Endpoint API untuk mendapatkan data spesialis pelajar."""
    user = User.query.get(user_id)
    if user:
        return jsonify({'spesialis': user.spesialis or ''})
    else:
        return jsonify({'error': 'User not found'}), 404

@admin_bp.route('/sertifikat/ocr', methods=['POST'])
@login_required
@admin_required
def ocr_sertifikat():
    """
    Mengolah hasil OCR untuk sertifikat dan memperbarui data sertifikat.
    """
    data = request.get_json()
    if not data or 'ocr_result' not in data:
        return jsonify({'error': 'Data OCR tidak ditemukan.'}), 400

    ocr_result = data['ocr_result']
    # Simulasi: Buat objek sertifikat baru dari hasil OCR
    mock_sertifikat_obj = Sertifikat()

    # Normalisasi tanggal terbit hasil OCR ke YYYY-MM-DD
    tgl_ocr = ocr_result.get('tanggal_terbit')
    if tgl_ocr:
        try:
            # Coba parsing dari format "28 June 2025" ke "2025-06-28"
            tgl_obj = datetime.strptime(tgl_ocr.strip(), '%d %B %Y')
            mock_sertifikat_obj.tanggal_terbit = tgl_obj.strftime('%Y-%m-%d')
        except Exception:
            # Jika gagal, gunakan apa adanya
            mock_sertifikat_obj.tanggal_terbit = tgl_ocr
    else:
        mock_sertifikat_obj.tanggal_terbit = tgl_ocr

    # Untuk keperluan debug, simpan hasil OCR dan objek sertifikat sementara
    current_app.logger.debug(f"Hasil OCR: {ocr_result}")
    current_app.logger.debug(f"Objek Sertifikat (sementara): {mock_sertifikat_obj.to_dict()}")

    return jsonify({'message': 'Data sertifikat berhasil diproses.', 'sertifikat': mock_sertifikat_obj.to_dict()}), 200
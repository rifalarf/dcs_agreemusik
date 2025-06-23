from flask import (Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, jsonify)
from flask_login import login_required, current_user
from .decorators import admin_required
# --- PASTIKAN BARIS IMPOR INI ADA DAN BENAR ---
from .forms import PelajarForm, SertifikatForm, SPESIALIS_CHOICES, LEVEL_CHOICES
# ----------------------------------------------
from .models import User, Sertifikat
from . import db
from .utils_crypto import load_private_key, generate_qr_code_from_signature_text
# PERBAIKAN: Impor fungsi yang benar
from .utils_certificate import generate_certificate_pdf
import os
import hashlib # Pastikan hashlib diimpor

admin_bp = Blueprint('admin', __name__)

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
        existing_user_by_username = User.query.filter_by(username=form.username.data).first()
        existing_user_by_email = User.query.filter_by(email=form.email.data).first()
        if existing_user_by_username:
            flash('Username sudah digunakan.', 'danger')
        elif existing_user_by_email:
            flash('Email sudah digunakan.', 'danger')
        else:
            if not form.password.data: # Jika password tidak diisi untuk user baru
                flash('Password wajib diisi untuk pengguna baru.', 'warning')
                return render_template('admin/form_pelajar.html', title='Tambah Pelajar', form=form, legend='Tambah Pelajar Baru')

            # Ambil nilai spesialis
            spesialis_value = form.spesialis.data
            if spesialis_value == 'ISI_SENDIRI':
                spesialis_value = form.spesialis_custom.data or None
            elif not spesialis_value:
                spesialis_value = None

            # Ambil nilai level
            level_value = form.level.data
            if level_value == 'ISI_SENDIRI':
                level_value = form.level_custom.data or None
            elif not level_value:
                level_value = None

            user = User(
                username=form.username.data,
                email=form.email.data,
                nama_lengkap=form.nama_lengkap.data,
                role=form.role.data,
                password=form.password.data, # Password sudah tidak di-hash
                spesialis=spesialis_value,
                spesialis_level=level_value
            )
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
        # Ambil nilai spesialis
        spesialis_value = form.spesialis.data
        if spesialis_value == 'ISI_SENDIRI':
            spesialis_value = form.spesialis_custom.data or None
        elif not spesialis_value:
            spesialis_value = None

        # Ambil nilai level
        level_value = form.level.data
        if level_value == 'ISI_SENDIRI':
            level_value = form.level_custom.data or None
        elif not level_value:
            level_value = None

        user.username = form.username.data
        user.email = form.email.data
        user.nama_lengkap = form.nama_lengkap.data
        user.role = form.role.data
        user.spesialis = spesialis_value
        user.spesialis_level = level_value
        if form.password.data: # Jika admin mengisi password baru
            user.password = form.password.data
        db.session.commit()
        flash(f'Data pelajar {user.nama_lengkap} berhasil diperbarui.', 'success')
        return redirect(url_for('admin.manage_pelajar'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.nama_lengkap.data = user.nama_lengkap
        form.role.data = user.role

        # Logika untuk mengisi form.spesialis dan form.spesialis_custom
        standard_spesialis = [choice[0] for choice in SPESIALIS_CHOICES if choice[0] and choice[0] != 'ISI_SENDIRI']
        if user.spesialis and user.spesialis not in standard_spesialis:
            form.spesialis.data = 'ISI_SENDIRI'
            form.spesialis_custom.data = user.spesialis
        else:
            form.spesialis.data = user.spesialis or ''

        # Logika untuk mengisi form.level dan form.level_custom
        standard_levels = [choice[0] for choice in LEVEL_CHOICES if choice[0] and choice[0] != 'ISI_SENDIRI']
        if user.spesialis_level and user.spesialis_level not in standard_levels:
            form.level.data = 'ISI_SENDIRI'
            form.level_custom.data = user.spesialis_level
        else:
            form.level.data = user.spesialis_level or ''

        form.pelajar_id.data = user.id

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
    sertifikats = Sertifikat.query.order_by(Sertifikat.tanggal_terbit.desc()).paginate(page=page, per_page=10)
    return render_template('admin/manage_sertifikat.html', title='Manajemen Sertifikat', sertifikats=sertifikats)

@admin_bp.route('/sertifikat/tambah', methods=['GET', 'POST'])
@login_required
@admin_required
def tambah_sertifikat():
    form = SertifikatForm()
    if form.validate_on_submit():
        private_key_obj = load_private_key(current_app.config['PRIVATE_KEY_PATH'])
        if not private_key_obj:
            flash('Gagal memuat kunci privat...', 'danger')
            return redirect(url_for('admin.manage_sertifikat'))

        user_penerima = User.query.get(int(form.user_id.data))
        if not user_penerima or user_penerima.role != 'pelajar':
            flash('Pelajar tidak valid.', 'danger')
            return redirect(url_for('admin.tambah_sertifikat'))

        # PANGGIL FUNGSI GENERATE ID DI SINI
        new_id = Sertifikat.generate_next_id()

        sertifikat = Sertifikat(
            id_sertifikat=new_id, # Gunakan ID yang baru dibuat
            pemilik=user_penerima,
            spesialis=form.spesialis.data,
            tanggal_terbit=form.tanggal_terbit.data,
            penandatangan=form.penandatangan.data
        )
        
        sertifikat.prepare_and_sign(current_app.config, private_key_obj)
        
        # PERBAIKAN: Gunakan alur baru yang berbasis HTML/weasyprint
        qr_code_b64 = generate_qr_code_from_signature_text(sertifikat.signature_hash)
        pdf_bytes = generate_certificate_pdf(sertifikat, qr_code_b64)
        
        sertifikat.pdf_file_hash = hashlib.sha3_256(pdf_bytes).hexdigest()
        
        # Simpan file PDF yang baru
        pdf_dir = os.path.join(current_app.instance_path, 'sertifikat_pdf')
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_filename = f"{sertifikat.id_sertifikat}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        sertifikat.pdf_file_path = pdf_path
        db.session.add(sertifikat)
        db.session.commit()
        flash('Sertifikat berhasil ditambahkan.', 'success')
        # PERBAIKAN: Ganti 'dashboard_admin' menjadi 'dashboard'
        return redirect(url_for('admin.dashboard'))
    
    # PERBAIKAN: Gunakan template 'form_sertifikat.html' yang sudah ada.
    return render_template('admin/form_sertifikat.html', title='Tambah Sertifikat', form=form, legend='Buat Sertifikat Baru')

@admin_bp.route('/sertifikat/edit/<int:sertifikat_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_sertifikat(sertifikat_id):
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)
    # PERUBAHAN: Berikan 'original_sertifikat' ke form
    form = SertifikatForm(original_sertifikat=sertifikat, obj=sertifikat)

    if form.validate_on_submit():
        # Hapus file PDF lama jika ada, sebelum membuat yang baru
        if sertifikat.pdf_file_path and os.path.exists(sertifikat.pdf_file_path):
            try:
                os.remove(sertifikat.pdf_file_path)
            except OSError as e:
                current_app.logger.error(f"Gagal menghapus PDF lama ({sertifikat.pdf_file_path}): {e}")
                flash('Gagal menghapus file PDF lama, proses pembaruan dihentikan.', 'danger')
                return redirect(url_for('admin.edit_sertifikat', sertifikat_id=sertifikat.id))

        # Update data sertifikat dari form
        sertifikat.user_id = int(form.user_id.data)
        # JANGAN UPDATE ID SERTIFIKAT, BIARKAN TETAP
        # sertifikat.id_sertifikat = form.id_sertifikat.data 
        sertifikat.spesialis = form.spesialis.data
        sertifikat.tanggal_terbit = form.tanggal_terbit.data
        sertifikat.penandatangan = form.penandatangan.data

        # Lakukan proses penandatanganan ulang
        private_key_obj = load_private_key(current_app.config['PRIVATE_KEY_PATH'])
        if not private_key_obj:
            flash('Gagal memuat kunci privat untuk penandatanganan ulang.', 'danger')
            return redirect(url_for('admin.edit_sertifikat', sertifikat_id=sertifikat.id))
        
        sertifikat.prepare_and_sign(current_app.config, private_key_obj)

        # Buat ulang QR code dengan signature baru
        qr_code_b64 = generate_qr_code_from_signature_text(sertifikat.signature_hash)

        # Buat ulang file PDF
        pdf_bytes = generate_certificate_pdf(sertifikat, qr_code_b64)

        # HITUNG DAN SIMPAN HASH BARU DARI FILE PDF
        sertifikat.pdf_file_hash = hashlib.sha3_256(pdf_bytes).hexdigest()

        # Simpan file PDF yang baru
        pdf_dir = os.path.join(current_app.instance_path, 'sertifikat_pdf')
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_filename = f'{sertifikat.id_sertifikat.replace("/", "_")}.pdf'
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)

        # Update path PDF di database
        sertifikat.pdf_file_path = pdf_path

        db.session.commit()
        flash(f'Sertifikat {sertifikat.id_sertifikat} berhasil diperbarui dan PDF telah dibuat ulang.', 'success')
        return redirect(url_for('admin.detail_sertifikat_admin', sertifikat_id=sertifikat.id))

    elif request.method == 'GET':
        # ... (logika untuk mengisi form saat GET tetap sama) ...
        pass

    return render_template('admin/form_sertifikat.html', title='Edit Sertifikat', form=form, legend=f'Edit Sertifikat: {sertifikat.id_sertifikat}')

@admin_bp.route('/sertifikat/detail/<int:sertifikat_id>')
@login_required
@admin_required
def detail_sertifikat_admin(sertifikat_id):
    """Menampilkan detail sebuah sertifikat, termasuk QR code-nya."""
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)
    qr_code_img_b64 = None
    if sertifikat.signature_hash:
        # PERBAIKAN: Gunakan fungsi baru yang hanya memerlukan signature hash
        qr_code_img_b64 = generate_qr_code_from_signature_text(sertifikat.signature_hash)
    
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
    id_sert_hapus = sertifikat.id_sertifikat
    db.session.delete(sertifikat)
    db.session.commit()
    flash(f'Sertifikat {id_sert_hapus} berhasil dihapus.', 'success')
    return redirect(url_for('admin.manage_sertifikat'))

@admin_bp.route('/pelajar/<int:user_id>/get_spesialis', methods=['GET'])
@login_required
@admin_required
def get_pelajar_spesialis(user_id):
    """Endpoint API untuk mendapatkan data spesialis pelajar."""
    user = User.query.get(user_id)
    if user:
        spesialis_text = ""
        if user.spesialis and user.spesialis_level:
            spesialis_text = f"{user.spesialis} - {user.spesialis_level}"
        elif user.spesialis:
            spesialis_text = user.spesialis
        elif user.spesialis_level:
            spesialis_text = user.spesialis_level
        return jsonify({'spesialis': spesialis_text})
    else:
        return jsonify({'error': 'User not found'}), 404
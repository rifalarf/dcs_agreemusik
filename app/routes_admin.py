from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app, send_file, jsonify)
from flask_login import login_required, current_user
from .decorators import admin_required
# --- PASTIKAN BARIS IMPOR INI ADA DAN BENAR ---
from .forms import PelajarForm, SertifikatForm, SPESIALIS_CHOICES, LEVEL_CHOICES
# ----------------------------------------------
from .models import User, Sertifikat
from . import db
from .utils_crypto import load_private_key, generate_qr_code_with_details
from .utils_certificate import generate_certificate_image # Atau utils_docx jika sudah implementasi
import io

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
            flash('Gagal memuat kunci privat. Proses signing tidak dapat dilanjutkan.', 'danger')
            return render_template('admin/form_sertifikat.html', title='Tambah Sertifikat', form=form, legend='Tambah Sertifikat Baru')

        user_penerima = User.query.get(int(form.user_id.data))
        if not user_penerima:
            flash(f"Pelajar dengan ID {form.user_id.data} tidak ditemukan.", 'danger')
            return render_template('admin/form_sertifikat.html', title='Tambah Sertifikat', form=form, legend='Tambah Sertifikat Baru')

        sertifikat = Sertifikat(
            pemilik=user_penerima,
            id_sertifikat=form.id_sertifikat.data,
            spesialis=form.spesialis.data,
            tanggal_terbit=form.tanggal_terbit.data,
            nama_lembaga_penerbit=form.nama_lembaga_penerbit.data
        )
        sertifikat.prepare_and_sign(current_app.config, private_key_obj)
        db.session.add(sertifikat)
        db.session.commit()
        flash(f'Sertifikat {sertifikat.id_sertifikat} berhasil ditambahkan dan ditandatangani.', 'success')
        return redirect(url_for('admin.manage_sertifikat'))
    return render_template('admin/form_sertifikat.html', title='Tambah Sertifikat', form=form, legend='Tambah Sertifikat Baru')

@admin_bp.route('/sertifikat/edit/<int:sertifikat_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_sertifikat(sertifikat_id):
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)
    form = SertifikatForm(original_id_sertifikat=sertifikat.id_sertifikat)

    if form.validate_on_submit():
        private_key_obj = load_private_key(current_app.config['PRIVATE_KEY_PATH'])
        if not private_key_obj:
            flash('Gagal memuat kunci privat. Proses re-signing tidak dapat dilanjutkan.', 'danger')
            return render_template('admin/form_sertifikat.html', title='Edit Sertifikat', form=form, legend=f'Edit Sertifikat: {sertifikat.id_sertifikat}', sertifikat=sertifikat)

        sertifikat.user_id = form.user_id.data
        sertifikat.id_sertifikat = form.id_sertifikat.data
        sertifikat.spesialis = form.spesialis.data
        sertifikat.tanggal_terbit = form.tanggal_terbit.data
        sertifikat.nama_lembaga_penerbit = form.nama_lembaga_penerbit.data
        sertifikat.prepare_and_sign(current_app.config, private_key_obj)
        db.session.commit()
        flash(f'Sertifikat {sertifikat.id_sertifikat} berhasil diperbarui dan ditandatangani ulang.', 'success')
        return redirect(url_for('admin.manage_sertifikat'))
    elif request.method == 'GET':
        form.user_id.data = sertifikat.user_id
        form.id_sertifikat.data = sertifikat.id_sertifikat
        form.spesialis.data = sertifikat.spesialis
        form.tanggal_terbit.data = sertifikat.tanggal_terbit
        form.nama_lembaga_penerbit.data = sertifikat.nama_lembaga_penerbit
        form.sertifikat_id.data = sertifikat.id # ID internal untuk form
    return render_template('admin/form_sertifikat.html', title='Edit Sertifikat', form=form, legend=f'Edit Sertifikat: {sertifikat.id_sertifikat}', sertifikat=sertifikat)

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

@admin_bp.route('/sertifikat/detail/<int:sertifikat_id>')
@login_required
@admin_required
def detail_sertifikat_admin(sertifikat_id):
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)
    qr_code_img_b64 = None
    if sertifikat.signature_hash and sertifikat.id_sertifikat:
        qr_code_img_b64 = generate_qr_code_with_details(sertifikat.id_sertifikat, sertifikat.signature_hash)
    return render_template('admin/detail_sertifikat_admin.html', title=f'Detail Sertifikat {sertifikat.id_sertifikat}', sertifikat=sertifikat, qr_code_img_b64=qr_code_img_b64)

@admin_bp.route('/sertifikat/cetak/<int:sertifikat_id>')
@login_required
@admin_required
def cetak_sertifikat_admin(sertifikat_id):
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)
    if not sertifikat.signature_hash:
        flash('Sertifikat ini belum ditandatangani sepenuhnya dan tidak bisa dicetak.', 'warning')
        return redirect(url_for('admin.detail_sertifikat_admin', sertifikat_id=sertifikat.id))

    # Asumsi masih menggunakan PNG via utils_certificate
    img_pil = generate_certificate_image(sertifikat)
    if img_pil is None:
        flash('Gagal membuat gambar sertifikat. Periksa log server.', 'danger')
        return redirect(url_for('admin.detail_sertifikat_admin', sertifikat_id=sertifikat.id))

    img_io = io.BytesIO()
    img_pil.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(
        img_io,
        mimetype='image/png',
        as_attachment=True,
        download_name=f'Sertifikat_{sertifikat.id_sertifikat.replace("/", "-")}_{sertifikat.pemilik.nama_lengkap.replace(" ", "_")}.png'
    )

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
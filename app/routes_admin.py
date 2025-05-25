from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from .decorators import admin_required
from .forms import PelajarForm, SertifikatForm
from .models import User, Sertifikat
from . import db
from .utils_crypto import load_private_key, generate_qr_code_with_details # Ubah import
from werkzeug.security import generate_password_hash
from flask import send_file # Tambahkan ini
from .utils_certificate import generate_certificate_image # Tambahkan ini
import io # Tambahkan ini

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
    # Ambil semua user, bisa juga difilter hanya role pelajar jika mau
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
            user = User(
                username=form.username.data,
                email=form.email.data,
                nama_lengkap=form.nama_lengkap.data,
                role=form.role.data
            )
            if form.password.data:
                user.set_password(form.password.data)
            else:
                # Generate random password jika tidak diisi, atau minta diisi
                flash('Password wajib diisi untuk pengguna baru.', 'warning')
                return render_template('admin/form_pelajar.html', title='Tambah Pelajar', form=form, legend='Tambah Pelajar Baru')

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
        form.pelajar_id.data = user.id
    return render_template('admin/form_pelajar.html', title='Edit Pelajar', form=form, legend=f'Edit Pelajar: {user.nama_lengkap}')

@admin_bp.route('/pelajar/hapus/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def hapus_pelajar(user_id):
    user = User.query.get_or_404(user_id)
    # Hati-hati jika user punya sertifikat, cascade delete akan menghapusnya juga
    # Atau berikan warning
    if user.username == current_app.config.get('ADMIN_USERNAME'): # Jangan hapus admin utama
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
    form = SertifikatForm() # Form akan menginisialisasi choices-nya sendiri

    if form.validate_on_submit():
        # ... (logika POST tetap sama) ...
        private_key_obj = load_private_key(current_app.config['PRIVATE_KEY_PATH'])
        if not private_key_obj:
            flash('Gagal memuat kunci privat. Proses signing tidak dapat dilanjutkan.', 'danger')
            # Penting: Saat render ulang, form sudah memiliki choices yang benar
            return render_template('admin/form_sertifikat.html', title='Tambah Sertifikat', form=form, legend='Tambah Sertifikat Baru')

        user_penerima = User.query.get(int(form.user_id.data))
        if not user_penerima:
            flash(f"Pelajar dengan ID {form.user_id.data} tidak ditemukan.", 'danger')
            return render_template('admin/form_sertifikat.html', title='Tambah Sertifikat', form=form, legend='Tambah Sertifikat Baru')

        sertifikat = Sertifikat(
            pemilik=user_penerima,
            nomor_sertifikat=form.nomor_sertifikat.data,
            nama_kompetensi=form.nama_kompetensi.data,
            tanggal_terbit=form.tanggal_terbit.data,
            nama_lembaga_penerbit=form.nama_lembaga_penerbit.data
        )
        
        sertifikat.prepare_and_sign(current_app.config, private_key_obj)
        
        db.session.add(sertifikat)
        db.session.commit()
        flash(f'Sertifikat {sertifikat.nomor_sertifikat} berhasil ditambahkan dan ditandatangani.', 'success')
        return redirect(url_for('admin.manage_sertifikat'))
    
    # Bagian ini tidak lagi diperlukan jika __init__ form sudah benar:
    # elif request.method == 'GET' or not form.validate(): # Atau jika validasi gagal
    #     # Pastikan choices di-populate untuk render awal atau render ulang
    #     pelajar_choices_init = [(u.id, u.nama_lengkap) for u in User.query.filter_by(role='pelajar').order_by(User.nama_lengkap).all()]
    #     if not pelajar_choices_init:
    #         form.user_id.choices = [(0, "Tidak ada pelajar tersedia")] # Ini masih akan error jika DataRequired
    #     else:
    #         form.user_id.choices = pelajar_choices_init


    return render_template('admin/form_sertifikat.html', title='Tambah Sertifikat', form=form, legend='Tambah Sertifikat Baru')

@admin_bp.route('/sertifikat/edit/<int:sertifikat_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_sertifikat(sertifikat_id):
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)
    form = SertifikatForm(original_nomor_sertifikat=sertifikat.nomor_sertifikat)

    if form.validate_on_submit():
        private_key_obj = load_private_key(current_app.config['PRIVATE_KEY_PATH'])
        if not private_key_obj:
            flash('Gagal memuat kunci privat. Proses re-signing tidak dapat dilanjutkan.', 'danger')
            return render_template('admin/form_sertifikat.html', title='Edit Sertifikat', form=form, legend=f'Edit Sertifikat: {sertifikat.nomor_sertifikat}', sertifikat=sertifikat)

        sertifikat.user_id = form.user_id.data
        sertifikat.nomor_sertifikat = form.nomor_sertifikat.data
        sertifikat.nama_kompetensi = form.nama_kompetensi.data
        sertifikat.tanggal_terbit = form.tanggal_terbit.data
        sertifikat.nama_lembaga_penerbit = form.nama_lembaga_penerbit.data
        
        # Proses re-signing
        sertifikat.prepare_and_sign(current_app.config, private_key_obj)
        
        db.session.commit()
        flash(f'Sertifikat {sertifikat.nomor_sertifikat} berhasil diperbarui dan ditandatangani ulang.', 'success')
        return redirect(url_for('admin.manage_sertifikat'))
    elif request.method == 'GET':
        form.user_id.data = sertifikat.user_id
        form.nomor_sertifikat.data = sertifikat.nomor_sertifikat
        form.nama_kompetensi.data = sertifikat.nama_kompetensi
        form.tanggal_terbit.data = sertifikat.tanggal_terbit
        form.nama_lembaga_penerbit.data = sertifikat.nama_lembaga_penerbit
        form.sertifikat_id.data = sertifikat.id
        
    return render_template('admin/form_sertifikat.html', title='Edit Sertifikat', form=form, legend=f'Edit Sertifikat: {sertifikat.nomor_sertifikat}', sertifikat=sertifikat)

@admin_bp.route('/sertifikat/hapus/<int:sertifikat_id>', methods=['POST'])
@login_required
@admin_required
def hapus_sertifikat(sertifikat_id):
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)
    nomor_sertifikat = sertifikat.nomor_sertifikat
    db.session.delete(sertifikat)
    db.session.commit()
    flash(f'Sertifikat {nomor_sertifikat} berhasil dihapus.', 'success')
    return redirect(url_for('admin.manage_sertifikat'))

@admin_bp.route('/sertifikat/detail/<int:sertifikat_id>')
@login_required
@admin_required
def detail_sertifikat_admin(sertifikat_id):
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)
    qr_code_img_b64 = None
    if sertifikat.signature_hash and sertifikat.nomor_sertifikat:
        # Gunakan fungsi baru
        qr_code_img_b64 = generate_qr_code_with_details(sertifikat.nomor_sertifikat, sertifikat.signature_hash)
    return render_template('admin/detail_sertifikat_admin.html', title=f'Detail Sertifikat {sertifikat.nomor_sertifikat}', sertifikat=sertifikat, qr_code_img_b64=qr_code_img_b64)

@admin_bp.route('/sertifikat/cetak/<int:sertifikat_id>')
@login_required
@admin_required
def cetak_sertifikat_admin(sertifikat_id):
    sertifikat = Sertifikat.query.get_or_404(sertifikat_id)
    
    if not sertifikat.signature_hash: # Atau kondisi lain jika sertifikat belum siap dicetak
        flash('Sertifikat ini belum ditandatangani sepenuhnya dan tidak bisa dicetak.', 'warning')
        return redirect(url_for('admin.detail_sertifikat_admin', sertifikat_id=sertifikat.id))

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
        download_name=f'Sertifikat_{sertifikat.nomor_sertifikat.replace("/", "-")}_{sertifikat.pemilik.nama_lengkap.replace(" ", "_")}.png'
    )
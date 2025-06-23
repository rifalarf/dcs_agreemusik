from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from .forms import LoginForm, RegistrationForm
from .models import User
from . import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
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

        user = User(
            username=form.username.data,
            email=form.email.data,
            nama_lengkap=form.nama_lengkap.data,
            role='pelajar',
            password=form.password.data,
            spesialis=spesialis_value, # <-- Gunakan nama baru
            spesialis_level=level_value
        )
        db.session.add(user)
        db.session.commit()
        flash('Selamat! Anda berhasil terdaftar. Silakan login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Registrasi Pelajar', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index')) # Arahkan ke Home
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # Ubah pengecekan password
        if user and user.password == form.password.data:
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash(f'Login berhasil. Selamat datang, {user.nama_lengkap}!', 'success')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Login gagal. Periksa kembali username dan password Anda.', 'danger')
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('main.index')) # Arahkan ke Home
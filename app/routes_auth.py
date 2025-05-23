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
        user = User(
            username=form.username.data, 
            email=form.email.data,
            nama_lengkap=form.nama_lengkap.data,
            role='pelajar' # Default role untuk registrasi publik
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Selamat! Anda berhasil terdaftar. Silakan login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Registrasi Pelajar', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash(f'Login berhasil. Selamat datang, {user.nama_lengkap}!', 'success')
            if user.is_admin:
                return redirect(next_page or url_for('admin.dashboard'))
            else: # Pelajar
                return redirect(next_page or url_for('pelajar.dashboard'))
        else:
            flash('Login gagal. Periksa kembali username dan password Anda.', 'danger')
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('main.index'))
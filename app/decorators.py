from functools import wraps
from flask_login import current_user
from flask import abort, flash, redirect, url_for

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Akses ditolak. Anda harus menjadi admin untuk mengakses halaman ini.', 'danger')
            return redirect(url_for('auth.login')) # atau halaman lain
        return f(*args, **kwargs)
    return decorated_function

def pelajar_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'pelajar':
            flash('Akses ditolak. Anda harus login sebagai pelajar.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
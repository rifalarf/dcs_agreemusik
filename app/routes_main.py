from flask import Blueprint, render_template
from flask_login import current_user
from .models import Sertifikat

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return render_template('admin/dashboard.html', title='Admin Dashboard')
        elif current_user.role == 'pelajar':
            jumlah_sertifikat = Sertifikat.query.filter_by(user_id=current_user.id).count()
            return render_template('pelajar/dashboard.html', title='Pelajar Dashboard', jumlah_sertifikat=jumlah_sertifikat)
    return render_template('index.html', title='Selamat Datang')
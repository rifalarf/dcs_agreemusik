from flask import Blueprint, render_template
from flask_login import current_user
from .models import Sertifikat

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    return render_template('index.html', title='Selamat Datang')
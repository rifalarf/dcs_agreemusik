from flask import Flask
from config import Config, TestingConfig # <-- Impor TestingConfig
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os

# --- PERBAIKAN: Inisialisasi ekstensi di sini, tanpa aplikasi ---
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'main.login' # Arahkan ke halaman login
login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
login_manager.login_message_category = 'info'

# --- Tambahkan dictionary untuk memetakan nama konfigurasi ke kelas ---
config_by_name = dict(
    default=Config,
    testing=TestingConfig
)

def create_app(config_name='default'): # <-- Ubah parameter menjadi nama config
    """Application Factory Function"""
    app = Flask(__name__)
    
    # --- Gunakan nama untuk memilih objek konfigurasi ---
    config_object = config_by_name.get(config_name, Config)
    app.config.from_object(config_object)

    # --- PERBAIKAN: Aktifkan ekstensi 'do' untuk Jinja2 ---
    app.jinja_env.add_extension('jinja2.ext.do')

    # --- PERBAIKAN: Hubungkan ekstensi dengan aplikasi di sini ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Import model di sini agar user_loader dapat menemukannya
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # Sekarang ini akan bekerja karena 'db' sudah terhubung dengan 'app'
        return User.query.get(int(user_id))

    # --- Registrasi Blueprint ---
    from .routes_main import main_bp
    app.register_blueprint(main_bp)

    from .routes_auth import auth_bp
    app.register_blueprint(auth_bp)

    from .routes_admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from .routes_pelajar import pelajar_bp
    app.register_blueprint(pelajar_bp)

    from .routes_public import public_bp
    app.register_blueprint(public_bp)

    # Pastikan folder instance ada
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    return app
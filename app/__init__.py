from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager # Pastikan LoginManager diimpor
from flask_wtf.csrf import CSRFProtect
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager() # Inisialisasi LoginManager
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect()

# Tambahkan Flask-Migrate jika digunakan
from flask_migrate import Migrate

# ---- TAMBAHKAN FUNGSI USER LOADER DI SINI ----
@login_manager.user_loader
def load_user(user_id):
    from .models import User # Impor User model di sini untuk menghindari circular import
    return User.query.get(int(user_id))
# ---------------------------------------------

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    instance_path = os.path.join(app.root_path, '..', 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        # print(f"Created instance folder at {instance_path}") # Komentari jika sudah ada

    db.init_app(app)
    login_manager.init_app(app) # Pastikan ini dipanggil SETELAH login_manager didefinisikan
    csrf.init_app(app)
    
    migrate = Migrate(app, db) # Inisialisasi Migrate di sini jika digunakan

    # Import dan daftarkan Blueprints
    from .routes_auth import auth_bp
    from .routes_admin import admin_bp
    from .routes_pelajar import pelajar_bp
    from .routes_public import public_bp
    from . import routes_main # Rute utama seperti index

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(pelajar_bp, url_prefix='/pelajar')
    app.register_blueprint(public_bp, url_prefix='/public')
    app.register_blueprint(routes_main.main_bp)

    return app
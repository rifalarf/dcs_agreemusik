from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
import os
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect()

from flask_migrate import Migrate

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- TAMBAHKAN BARIS INI UNTUK MENGAKTIFKAN {% do %} ---
    app.jinja_env.add_extension('jinja2.ext.do')
    # --------------------------------------------------------

    instance_path = os.path.join(app.root_path, '..', 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate = Migrate(app, db)

    @app.context_processor
    def inject_now():
        return {'current_year': datetime.utcnow().year}

    # Import dan daftarkan Blueprints
    from .routes_auth import auth_bp
    from .routes_admin import admin_bp
    from .routes_pelajar import pelajar_bp
    from .routes_public import public_bp
    from . import routes_main

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(pelajar_bp, url_prefix='/pelajar')
    app.register_blueprint(public_bp, url_prefix='/public')
    app.register_blueprint(routes_main.main_bp)

    return app
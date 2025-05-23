from app import create_app, db
from app.models import User # Perlu diimport agar create_all tahu modelnya
from config import Config
from werkzeug.security import generate_password_hash
import click

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Sertifikat': app.models.Sertifikat}

@app.cli.command("init-db")
def init_db_command():
    """Membuat tabel database baru."""
    db.create_all()
    click.echo("Database telah diinisialisasi.")

@app.cli.command("create-admin")
def create_admin_command():
    """Membuat akun admin default."""
    admin_username = app.config.get('ADMIN_USERNAME', 'admin')
    admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
    admin_email = app.config.get('ADMIN_EMAIL', 'admin@example.com')
    admin_nama = app.config.get('ADMIN_NAMA_LENGKAP', 'Administrator')

    if User.query.filter_by(username=admin_username).first():
        click.echo(f"Admin user '{admin_username}' sudah ada.")
        return

    admin_user = User(
        username=admin_username,
        email=admin_email, # Sesuaikan jika perlu
        nama_lengkap=admin_nama,
        role='admin'
    )
    admin_user.set_password(admin_password)
    db.session.add(admin_user)
    db.session.commit()
    click.echo(f"Admin user '{admin_username}' berhasil dibuat.")


if __name__ == '__main__':
    app.run(debug=True)
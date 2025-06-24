import hashlib
from flask import Blueprint, render_template, request, flash, current_app
from .forms import VerifyCertificateForm
from .models import Sertifikat
from .utils_pdf import extract_data_from_pdf
from .utils_crypto import load_public_key, generate_certificate_data_string, _verify

public_bp = Blueprint('public', __name__)

@public_bp.route('/verify', methods=['GET', 'POST'])
def verify_certificate():
    form = VerifyCertificateForm()
    verification_result = None
    verified_data = None

    if form.validate_on_submit():
        # --- PERBAIKAN: Pindahkan pemuatan kunci ke sini ---
        # Muat kunci publik satu kali, agar tersedia untuk kedua alur verifikasi.
        public_key_obj = load_public_key(current_app.config['PUBLIC_KEY_PATH'])
        if not public_key_obj:
            flash('Kunci publik tidak dapat dimuat. Verifikasi tidak dapat dilanjutkan.', 'danger')
            return render_template('public/verify_certificate.html', title='Verifikasi Sertifikat', form=form)

        # Alur A: Verifikasi via PDF (DUAL-ANCHOR)
        if form.pdf_file_upload.data:
            try:
                pdf_bytes = request.files[form.pdf_file_upload.name].read()
                is_valid = False

                # 1. Hitung Jangkar File
                uploaded_file_hash = hashlib.sha3_256(pdf_bytes).hexdigest()

                # 2. Ekstrak Jangkar Data dari QR
                signature_from_qr = extract_data_from_pdf(pdf_bytes)
                if not signature_from_qr:
                    raise ValueError("QR Code tidak dapat dibaca dari file PDF.")

                # 3. Cari berdasarkan kedua jangkar
                sertifikat_by_file = Sertifikat.query.filter_by(pdf_file_hash=uploaded_file_hash).first()
                sertifikat_by_sig = Sertifikat.query.filter_by(signature_hash=signature_from_qr).first()

                # 4. Verifikasi: Keduanya harus ada dan menunjuk ke record yang sama
                if sertifikat_by_file and sertifikat_by_sig and (sertifikat_by_file.id == sertifikat_by_sig.id):
                    is_valid = True
                    verified_data = sertifikat_by_file
                else:
                    raise ValueError("Integritas file atau tanda tangan digital tidak valid.")

            except ValueError as e:
                flash(f'Verifikasi Gagal: {e}', 'danger')
            except Exception as e:
                flash(f'Error saat memproses PDF: {e}', 'danger')
            
            verification_result = "VALID" if is_valid else "TIDAK VALID"
            if is_valid:
                flash('Verifikasi Berhasil: Integritas file dan tanda tangan digital keduanya VALID.', 'success')

        # Alur B: Verifikasi Manual
        elif form.id_sertifikat.data and form.qr_content.data:
            try:
                # Buat objek sertifikat tiruan dari data form
                class MockSertifikat:
                    pass
                mock_sertifikat_obj = MockSertifikat()
                
                mock_sertifikat_obj.id_sertifikat = form.id_sertifikat.data.strip()
                
                # --- PERBAIKAN KRUSIAL DI SINI ---
                # Gabungkan spesialis dan level menjadi satu string, sama seperti saat sertifikat dibuat.
                spesialis_val = form.spesialis.data.strip()
                level_val = form.level_spesialis.data.strip()
                
                if spesialis_val and level_val:
                    # Format gabungan harus sama persis dengan saat sertifikat dibuat
                    mock_sertifikat_obj.spesialis = f"{spesialis_val} - {level_val}"
                elif spesialis_val:
                    mock_sertifikat_obj.spesialis = spesialis_val
                else:
                    mock_sertifikat_obj.spesialis = ""
                # ------------------------------------

                mock_sertifikat_obj.tanggal_terbit = form.tanggal_terbit.data
                mock_sertifikat_obj.penandatangan = form.penandatangan.data.strip()
                
                # Buat objek user tiruan untuk nama lengkap
                nama_penerima_cleaned = form.nama_penerima.data.strip()
                mock_sertifikat_obj.pemilik = type('MockUser', (object,), {'nama_lengkap': nama_penerima_cleaned})()

                # Buat ulang string data dari objek tiruan
                data_string = generate_certificate_data_string(mock_sertifikat_obj)
                
                # Verifikasi signature dari form (juga di-strip) dengan data dari form
                signature_cleaned = form.qr_content.data.strip()
                is_valid = _verify(data_string, signature_cleaned, public_key_obj)
                
                verification_result = "VALID" if is_valid else "TIDAK VALID"
                flash(f'Hasil verifikasi manual: Sertifikat {verification_result}.', 'success' if is_valid else 'danger')
                
                # Jika valid, coba cari data asli untuk ditampilkan
                if is_valid:
                    # Gunakan ID yang sudah dibersihkan untuk mencari di DB
                    real_sertifikat = Sertifikat.query.filter_by(id_sertifikat=form.id_sertifikat.data.strip()).first()
                    if real_sertifikat:
                        verified_data = real_sertifikat

            except Exception as e:
                flash(f'Error verifikasi manual: {e}', 'danger')
                verification_result = "MANUAL_ERROR"
        else:
            flash('Harap unggah file PDF atau isi semua field manual dengan lengkap.', 'warning')

    return render_template('public/verify_certificate.html', title='Verifikasi Sertifikat', form=form, result=verification_result, verified_data=verified_data)
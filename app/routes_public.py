# app/routes_public.py
from flask import Blueprint, render_template, request, flash, current_app
from .forms import VerifyCertificateForm
from .models import Sertifikat
from .utils_crypto import hash_data, verify_signature_ecdsa, load_public_key
import base64
from PIL import Image # Untuk memproses gambar QR
from pyzbar.pyzbar import decode as qr_decode # Untuk membaca QR dari gambar
import io

public_bp = Blueprint('public', __name__)

ALLOWED_EXTENSIONS_QR = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file_qr(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_QR


@public_bp.route('/verify', methods=['GET', 'POST'])
def verify_certificate():
    form = VerifyCertificateForm()
    verification_result = None
    sertifikat_data_display = None # Untuk menampilkan detail jika valid

    # Untuk mengisi ulang form jika ada error atau setelah upload
    nomor_sertifikat_value = ""
    qr_content_value = ""

    if request.method == 'POST':
        nomor_sertifikat_input = form.nomor_sertifikat.data
        qr_content_text_input = form.qr_content.data
        qr_file = request.files.get('qr_file_upload')

        parsed_nomor_sertifikat = None
        parsed_qr_signature = None

        if qr_file and qr_file.filename != '':
            if allowed_file_qr(qr_file.filename):
                try:
                    img_bytes = qr_file.read()
                    img = Image.open(io.BytesIO(img_bytes))
                    decoded_qr_list = qr_decode(img)
                    if decoded_qr_list:
                        qr_full_data = decoded_qr_list[0].data.decode('utf-8')
                        # Coba parsing: NOMOR_SERTIFIKAT|SIGNATURE_HASH_BASE64
                        parts = qr_full_data.split('|', 1)
                        if len(parts) == 2:
                            parsed_nomor_sertifikat = parts[0]
                            parsed_qr_signature = parts[1]
                            nomor_sertifikat_value = parsed_nomor_sertifikat # Untuk isi ulang form
                            qr_content_value = parsed_qr_signature         # Untuk isi ulang form
                            flash("QR Code dari file berhasil dibaca dan diparsing.", "info")
                        else: # Jika format tidak sesuai, anggap seluruh isi QR adalah signature
                            parsed_qr_signature = qr_full_data
                            qr_content_value = parsed_qr_signature
                            flash("QR Code dari file berhasil dibaca, namun format tidak mengandung Nomor Sertifikat. Silakan masukkan Nomor Sertifikat manual.", "warning")
                    else:
                        flash("Tidak dapat membaca QR Code dari gambar yang diunggah.", "error")
                except Exception as e:
                    flash(f"Error memproses file gambar QR: {str(e)}.", "error")
            else:
                flash("Format file QR Code tidak didukung.", "error")
        
        # Gunakan input teks jika parsing dari file tidak menghasilkan data atau tidak ada file
        if not parsed_nomor_sertifikat and nomor_sertifikat_input:
            parsed_nomor_sertifikat = nomor_sertifikat_input
            nomor_sertifikat_value = nomor_sertifikat_input
        
        if not parsed_qr_signature and qr_content_text_input:
            parsed_qr_signature = qr_content_text_input
            qr_content_value = qr_content_text_input

        # Setelah mendapatkan parsed_nomor_sertifikat dan parsed_qr_signature, lanjutkan verifikasi
        if not parsed_nomor_sertifikat:
            flash('Nomor Sertifikat harus diisi (baik manual atau dari QR Code).', 'danger')
        elif not parsed_qr_signature:
            flash('Isi QR Code (Signature) harus diisi (baik manual atau dari QR Code).', 'danger')
        else:
            sertifikat = Sertifikat.query.filter_by(nomor_sertifikat=parsed_nomor_sertifikat).first()

            if not sertifikat:
                flash(f'Sertifikat dengan nomor "{parsed_nomor_sertifikat}" tidak ditemukan.', 'warning')
                verification_result = "TIDAK DITEMUKAN"
            elif not sertifikat.data_string_untuk_sign or not sertifikat.signature_hash:
                flash(f'Sertifikat "{parsed_nomor_sertifikat}" belum ditandatangani atau data tidak lengkap.', 'warning')
                verification_result = "BELUM DITANDATANGANI"
            else:
                sertifikat_data_display = {
                    'nomor_sertifikat': sertifikat.nomor_sertifikat,
                    'nama_kompetensi': sertifikat.nama_kompetensi,
                    'nama_pemilik': sertifikat.pemilik.nama_lengkap,
                    'tanggal_terbit': sertifikat.tanggal_terbit.strftime('%d %B %Y'),
                    'nama_lembaga': sertifikat.nama_lembaga_penerbit
                }
                public_key_obj = load_public_key(current_app.config['PUBLIC_KEY_PATH'])
                if not public_key_obj:
                    flash('Gagal memuat kunci publik. Verifikasi tidak dapat dilanjutkan.', 'danger')
                    verification_result = "ERROR KONFIGURASI"
                else:
                    try:
                        data_hash_from_db = hash_data(sertifikat.data_string_untuk_sign)
                        signature_bytes_from_qr = base64.b64decode(parsed_qr_signature)
                        
                        if verify_signature_ecdsa(data_hash_from_db, signature_bytes_from_qr, public_key_obj):
                            verification_result = "VALID"
                            flash('Sertifikat ASLI dan VALID.', 'success')
                        else:
                            verification_result = "TIDAK VALID"
                            flash('Sertifikat TIDAK VALID. Signature QR tidak cocok.', 'danger')
                    except base64.binascii.Error:
                        flash('Isi QR Code (signature) tidak dalam format Base64 yang valid.', 'danger')
                        verification_result = "QR INVALID FORMAT"
                    except Exception as e:
                        flash(f'Terjadi kesalahan saat verifikasi: {str(e)}', 'danger')
                        verification_result = "ERROR VERIFIKASI"
    
    # Isi ulang nilai form
    if request.method != 'POST' or (parsed_nomor_sertifikat or parsed_qr_signature):
        form.nomor_sertifikat.data = nomor_sertifikat_value
        form.qr_content.data = qr_content_value
                        
    return render_template('public/verify_certificate.html', title='Verifikasi Sertifikat', form=form, result=verification_result, sertifikat_data=sertifikat_data_display)
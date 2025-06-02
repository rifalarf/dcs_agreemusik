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
    sertifikat_data_display = None

    # --- PERBAIKAN: Inisialisasi variabel di sini ---
    id_sertifikat_value = ""
    qr_content_value = ""
    parsed_id_sertifikat = None
    parsed_qr_signature = None
    # -----------------------------------------------

    if request.method == 'POST':
        id_sertifikat_input = form.id_sertifikat.data
        qr_content_text_input = form.qr_content.data
        qr_file = request.files.get('qr_file_upload')

        if qr_file and qr_file.filename != '':
            if allowed_file_qr(qr_file.filename):
                try:
                    img_bytes = qr_file.read()
                    img = Image.open(io.BytesIO(img_bytes))
                    decoded_qr_list = qr_decode(img)
                    if decoded_qr_list:
                        qr_full_data = decoded_qr_list[0].data.decode('utf-8')
                        parts = qr_full_data.split('|', 1)
                        if len(parts) == 2:
                            parsed_id_sertifikat = parts[0]
                            parsed_qr_signature = parts[1]
                            id_sertifikat_value = parsed_id_sertifikat # Isi ulang form
                            qr_content_value = parsed_qr_signature     # Isi ulang form
                            flash("QR Code dari file berhasil dibaca dan diparsing.", "info")
                        else:
                            parsed_qr_signature = qr_full_data
                            qr_content_value = parsed_qr_signature
                            flash("QR Code dari file berhasil dibaca, namun format tidak mengandung ID Sertifikat. Silakan masukkan ID Sertifikat manual.", "warning")
                    else:
                        flash("Tidak dapat membaca QR Code dari gambar yang diunggah.", "danger") # Ganti dari error
                except Exception as e:
                    flash(f"Error memproses file gambar QR: {str(e)}.", "danger") # Ganti dari error
            else:
                flash("Format file QR Code tidak didukung.", "danger") # Ganti dari error

        if not parsed_id_sertifikat and id_sertifikat_input:
            parsed_id_sertifikat = id_sertifikat_input
            id_sertifikat_value = id_sertifikat_input

        if not parsed_qr_signature and qr_content_text_input:
            parsed_qr_signature = qr_content_text_input
            qr_content_value = qr_content_text_input

        if not parsed_id_sertifikat:
            flash('ID Sertifikat harus diisi (baik manual atau dari QR Code).', 'danger')
        elif not parsed_qr_signature:
            flash('Isi QR Code (Signature) harus diisi (baik manual atau dari QR Code).', 'danger')
        else:
            # Gunakan filter_by(id_sertifikat=...)
            sertifikat = Sertifikat.query.filter_by(id_sertifikat=parsed_id_sertifikat).first()

            if not sertifikat:
                flash(f'Sertifikat dengan ID "{parsed_id_sertifikat}" tidak ditemukan.', 'warning')
                verification_result = "TIDAK DITEMUKAN"
            elif not sertifikat.data_string_untuk_sign or not sertifikat.signature_hash:
                flash(f'Sertifikat "{parsed_id_sertifikat}" belum ditandatangani atau data tidak lengkap.', 'warning')
                verification_result = "BELUM DITANDATANGANI"
            else:
                sertifikat_data_display = {
                    'id_sertifikat': sertifikat.id_sertifikat,
                    'spesialis': sertifikat.spesialis, # Ganti nama
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

    # --- PERBAIKAN: Selalu isi ulang form di luar blok POST ---
    # Ini akan mengisi form dengan nilai kosong saat GET,
    # atau dengan nilai yang didapat dari POST.
    form.id_sertifikat.data = id_sertifikat_value
    form.qr_content.data = qr_content_value
    # --------------------------------------------------------

    return render_template('public/verify_certificate.html', title='Verifikasi Sertifikat', form=form, result=verification_result, sertifikat_data=sertifikat_data_display)
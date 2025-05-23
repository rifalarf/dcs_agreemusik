from flask import Blueprint, render_template, request, flash, current_app
from .forms import VerifyCertificateForm
from .models import Sertifikat
from .utils_crypto import hash_data, verify_signature_ecdsa, load_public_key
import base64

public_bp = Blueprint('public', __name__)

@public_bp.route('/verify', methods=['GET', 'POST'])
def verify_certificate():
    form = VerifyCertificateForm()
    verification_result = None
    sertifikat_data = None

    if form.validate_on_submit():
        nomor_sertifikat = form.nomor_sertifikat.data
        qr_content_b64 = form.qr_content.data # Ini adalah signature_hash (Base64) dari QR

        sertifikat = Sertifikat.query.filter_by(nomor_sertifikat=nomor_sertifikat).first()

        if not sertifikat:
            flash(f'Sertifikat dengan nomor "{nomor_sertifikat}" tidak ditemukan.', 'warning')
            verification_result = "TIDAK DITEMUKAN"
        elif not sertifikat.data_string_untuk_sign or not sertifikat.signature_hash:
            flash(f'Sertifikat dengan nomor "{nomor_sertifikat}" belum ditandatangani atau data tidak lengkap.', 'warning')
            verification_result = "BELUM DITANDATANGANI"
        else:
            sertifikat_data = {
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
                    # Hash data_string_untuk_sign yang tersimpan di DB
                    data_hash_from_db = hash_data(sertifikat.data_string_untuk_sign)
                    
                    # Decode signature dari QR (input pengguna)
                    signature_bytes_from_qr = base64.b64decode(qr_content_b64)

                    # Bandingkan juga apakah signature dari QR sama dengan yang di DB (opsional, tapi bagus untuk konsistensi)
                    # if qr_content_b64 != sertifikat.signature_hash:
                    #     flash('Isi QR Code tidak cocok dengan signature yang tersimpan di sistem untuk nomor sertifikat ini.', 'warning')
                    #     verification_result = "QR MISMATCH"
                    # else:
                    if verify_signature_ecdsa(data_hash_from_db, signature_bytes_from_qr, public_key_obj):
                        verification_result = "VALID"
                        flash('Sertifikat ASLI dan VALID berdasarkan data sistem dan signature QR.', 'success')
                    else:
                        verification_result = "TIDAK VALID"
                        flash('Sertifikat TIDAK VALID. Signature QR tidak cocok dengan data sertifikat di sistem.', 'danger')
                
                except base64.binascii.Error:
                    flash('Isi QR Code (signature) tidak dalam format Base64 yang valid.', 'danger')
                    verification_result = "QR INVALID FORMAT"
                except Exception as e:
                    flash(f'Terjadi kesalahan saat verifikasi: {str(e)}', 'danger')
                    verification_result = "ERROR VERIFIKASI"
                    
    return render_template('public/verify_certificate.html', title='Verifikasi Sertifikat', form=form, result=verification_result, sertifikat_data=sertifikat_data)
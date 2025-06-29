import hashlib
from flask import Blueprint, render_template, request, flash, current_app
from .forms import VerifyCertificateForm
from .models import Sertifikat
from .utils_pdf import extract_images_from_pdf
from .utils_crypto import load_public_key, create_data_string, verify_data
from pyzbar.pyzbar import decode as qr_decode
from PIL import Image
import io
import base64
import tempfile
import requests
import re
import os
from datetime import datetime

public_bp = Blueprint('public', __name__)

def compress_image_pil(img, output_path, max_size_kb=1024, min_quality=10, resize_step=0.9):
    img = img.convert("RGB")
    quality = 90
    width, height = img.size
    # Turunkan kualitas dulu
    while True:
        img.save(output_path, 'JPEG', quality=quality, optimize=True)
        size_kb = os.path.getsize(output_path) // 1024
        if size_kb <= max_size_kb or quality <= min_quality:
            break
        quality -= 5
    # Jika kualitas minimal tapi size masih >1MB, resize gambar
    while os.path.getsize(output_path) > max_size_kb * 1024:
        width = int(width * resize_step)
        height = int(height * resize_step)
        img = img.resize((width, height), Image.LANCZOS)
        quality = 85
        img.save(output_path, 'JPEG', quality=quality, optimize=True)
        if width < 200 or height < 200:
            break
    return output_path

def ocr_and_parse(file_path, api_key):
    with open(file_path, 'rb') as f:
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'filename': f},
            data={'apikey': api_key, 'isOverlayRequired': 'false'}
        )
        result = response.json()
    if not result.get('IsErroredOnProcessing'):
        ocr_text = result['ParsedResults'][0]['ParsedText']
        print("=== HASIL OCR RAW ===")
        print(ocr_text)
        def regex_extract(pattern, text):
            m = re.search(pattern, text, re.IGNORECASE)
            return m.group(1).strip() if m else None
        fields = {}
        fields['nama']           = regex_extract(r'Nama:\s*(.+)', ocr_text)
        fields['spesialis']      = regex_extract(r'Spesialis:\s*(.+)', ocr_text)
        fields['tanggal_terbit'] = regex_extract(r'Tanggal Terbit:\s*(.+)', ocr_text)
        fields['id_sertifikat']  = regex_extract(r'ID Sertifikat:\s*(.+)', ocr_text)
        def extract_penandatangan(ocr_text):
            # Cari baris sebelum baris yang mengandung "DIREKTUR AGREE MUSIK" (abaikan spasi/kapital)
            pattern = r'^(.*)\n.*DIREKTUR\s*AGREE\s*MUSIK.*$'
            match = re.search(pattern, ocr_text.replace('\r', ''), re.IGNORECASE | re.MULTILINE)
            if match:
                nama = match.group(1).strip().split('\n')[-1].strip()
                return nama
            return None
        fields['penandatangan'] = extract_penandatangan(ocr_text)
        return fields
    else:
        return None

def read_qr_signature(img_path):
    img = Image.open(img_path)
    qr_data = qr_decode(img)
    if qr_data:
        return qr_data[0].data.decode()
    else:
        return None

def normalize_id_sertifikat(id_sertifikat):
    if id_sertifikat and id_sertifikat.upper().startswith("AG"):
        prefix = id_sertifikat[:2]
        # Ganti O/o dengan 0 dan I/i dengan 1
        suffix = id_sertifikat[2:].replace('O', '0').replace('o', '0').replace('I', '1').replace('i', '1')
        return prefix + suffix
    return id_sertifikat

@public_bp.route('/verify', methods=['GET', 'POST'])
def verify_certificate():
    form = VerifyCertificateForm()
    verification_result = None
    verified_data = None

    if form.validate_on_submit():
        public_key_obj = load_public_key(current_app.config['PUBLIC_KEY_PATH'])
        if not public_key_obj:
            flash('Kunci publik tidak dapat dimuat. Verifikasi tidak dapat dilanjutkan.', 'danger')
            return render_template('public/verify_certificate.html', title='Verifikasi Sertifikat', form=form)

        # --- WORKFLOW OCR/QR ---
        if form.pdf_file_upload.data:
            try:
                file_storage = request.files[form.pdf_file_upload.name]
                filename = file_storage.filename.lower()
                file_bytes = file_storage.read()

                if filename.endswith('.pdf'):
                    images = extract_images_from_pdf(file_bytes)
                    if not images:
                        raise ValueError("Gagal mengekstrak gambar dari PDF.")
                    pil_img = images[0]
                elif filename.endswith(('.jpg', '.jpeg', '.png')):
                    from PIL import Image
                    import io
                    pil_img = Image.open(io.BytesIO(file_bytes))
                else:
                    raise ValueError("Format file tidak didukung.")

                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_img:
                    compress_image_pil(pil_img, tmp_img.name)
                    compressed_path = tmp_img.name

                # OCR & parsing field
                api_key = current_app.config.get('OCR_SPACE_API_KEY', None)
                if not api_key:
                    raise ValueError("API key OCR belum diatur.")
                ocr_fields = ocr_and_parse(compressed_path, api_key)
                if not ocr_fields:
                    raise ValueError("Gagal membaca field sertifikat dari gambar (OCR).")

                # QR code signature
                signature_from_qr = read_qr_signature(compressed_path)
                if not signature_from_qr:
                    raise ValueError("QR Code tidak ditemukan pada gambar sertifikat.")

                # Bangun objek sertifikat tiruan dari hasil OCR
                class MockSertifikat: pass
                mock_sertifikat_obj = MockSertifikat()
                mock_sertifikat_obj.id_sertifikat = normalize_id_sertifikat(ocr_fields.get('id_sertifikat'))
                mock_sertifikat_obj.spesialis = ocr_fields.get('spesialis')
                
                # Normalisasi tanggal terbit hasil OCR ke YYYY-MM-DD
                tgl_ocr = ocr_fields.get('tanggal_terbit')
                if tgl_ocr:
                    try:
                        tgl_obj = datetime.strptime(tgl_ocr.strip(), '%d %B %Y')
                        mock_sertifikat_obj.tanggal_terbit = tgl_obj.strftime('%Y-%m-%d')
                    except Exception:
                        mock_sertifikat_obj.tanggal_terbit = tgl_ocr
                else:
                    mock_sertifikat_obj.tanggal_terbit = tgl_ocr
                
                mock_sertifikat_obj.penandatangan = ocr_fields.get('penandatangan')
                mock_sertifikat_obj.pemilik = type('MockUser', (object,), {'nama_lengkap': ocr_fields.get('nama')})()

                # Verifikasi signature
                data_string = create_data_string(mock_sertifikat_obj)
                print("=== DEBUG DATA STRING OCR ===")
                print(repr(data_string))
                print("=== DEBUG SIGNATURE QR ===")
                print(repr(signature_from_qr))
                is_valid = verify_data(data_string, signature_from_qr, public_key_obj)
                verification_result = "VALID" if is_valid else "TIDAK VALID"
                if is_valid:
                    flash('Verifikasi Berhasil: Data OCR dan tanda tangan digital VALID.', 'success')
                    real_sertifikat = Sertifikat.query.filter_by(signature_hash=signature_from_qr).first()
                    if real_sertifikat:
                        verified_data = real_sertifikat
                    else:
                        flash('PERINGATAN: Tanda tangan digital valid, tetapi tidak terdaftar di sistem kami.', 'warning')
                else:
                    flash('Verifikasi Gagal: Data OCR dan signature tidak cocok.', 'danger')
            except Exception as e:
                flash(f'Error saat memproses PDF/OCR: {e}', 'danger')
                verification_result = "TIDAK VALID"

        # Alur B: Verifikasi Manual
        elif form.id_sertifikat.data and form.qr_content.data:
            try:
                class MockSertifikat:
                    pass
                mock_sertifikat_obj = MockSertifikat()
                mock_sertifikat_obj.id_sertifikat = form.id_sertifikat.data
                mock_sertifikat_obj.spesialis = form.spesialis.data
                mock_sertifikat_obj.tanggal_terbit = form.tanggal_terbit.data
                mock_sertifikat_obj.penandatangan = form.penandatangan.data
                mock_sertifikat_obj.pemilik = type('MockUser', (object,), {'nama_lengkap': form.nama_penerima.data})()

                data_string = create_data_string(mock_sertifikat_obj)
                signature_from_form = form.qr_content.data
                is_valid = verify_data(data_string, signature_from_form, public_key_obj)

                verification_result = "VALID" if is_valid else "TIDAK VALID"
                flash(f'Hasil verifikasi manual: Sertifikat {verification_result}.', 'success' if is_valid else 'danger')

                if is_valid:
                    real_sertifikat = Sertifikat.query.filter_by(signature_hash=signature_from_form).first()
                    if real_sertifikat:
                        verified_data = real_sertifikat
                    else:
                        flash('PERINGATAN: Tanda tangan digital valid, tetapi tidak terdaftar di sistem kami.', 'warning')
            except Exception as e:
                flash(f'Error verifikasi manual: {e}', 'danger')
                verification_result = "MANUAL_ERROR"
        else:
            flash('Harap unggah file PDF atau isi semua field manual dengan lengkap.', 'warning')

    return render_template('public/verify_certificate.html', title='Verifikasi Sertifikat', form=form, result=verification_result, verified_data=verified_data)
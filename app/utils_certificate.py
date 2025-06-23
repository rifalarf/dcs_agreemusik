from flask import render_template, current_app
from weasyprint import HTML
import os
import pathlib # <-- Import pathlib

def generate_certificate_pdf(sertifikat_obj, qr_code_img_b64):
    """
    Menerima objek Sertifikat dan QR code base64, lalu mengembalikan
    objek PDF dalam bentuk bytes menggunakan template HTML.
    """
    with current_app.app_context():
        # PERBAIKAN: Buat path absolut ke file gambar dan ubah menjadi URI.
        # Ini adalah cara paling andal untuk memastikan WeasyPrint menemukan file di produksi.
        static_folder = os.path.join(current_app.root_path, 'static')
        
        bg_path = os.path.join(static_folder, 'images', 'background.png')
        bg_uri = pathlib.Path(bg_path).as_uri() if os.path.exists(bg_path) else ''

        sign_path = os.path.join(static_folder, 'images', 'tandatangan', 'direktur', 'shofia.png')
        sign_uri = pathlib.Path(sign_path).as_uri() if os.path.exists(sign_path) else ''

        html_string = render_template(
            'sertifikat/pdf_template.html',
            sertifikat=sertifikat_obj,
            qr_code_img_b64=qr_code_img_b64,
            background_image_uri=bg_uri,
            signature_image_uri=sign_uri
        )
    
    # base_url tidak lagi diperlukan karena kita menggunakan path absolut
    pdf_bytes = HTML(string=html_string).write_pdf()
    
    return pdf_bytes
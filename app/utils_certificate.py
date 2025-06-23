from flask import render_template, current_app
from weasyprint import HTML

def generate_certificate_pdf(sertifikat_obj, qr_code_img_b64):
    """
    Menerima objek Sertifikat dan QR code base64, lalu mengembalikan
    objek PDF dalam bentuk bytes menggunakan template HTML.
    """
    # 'with current_app.app_context()' memastikan kita bisa mengakses 'current_app'
    # Ini adalah praktik yang baik saat bekerja di luar konteks request utama.
    with current_app.app_context():
        html_string = render_template(
            'sertifikat/pdf_template.html',
            sertifikat=sertifikat_obj,
            qr_code_img_b64=qr_code_img_b64
        )
    
    # Berikan base_url agar weasyprint dapat menemukan file statis di lingkungan produksi.
    base_url = current_app.root_path
    pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf()
    
    return pdf_bytes
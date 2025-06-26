import qrcode
import io

def generate_qr_code_from_signature_text(signature_text: str) -> bytes:
    """
    Menghasilkan gambar QR code dari teks yang diberikan.

    Args:
        signature_text: Teks yang akan di-encode ke dalam QR code.

    Returns:
        Gambar QR code dalam format PNG sebagai bytes.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4, # Ukuran box lebih kecil agar QR code tidak terlalu besar
        border=4,
    )
    qr.add_data(signature_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Simpan gambar ke buffer bytes di memori
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return img_byte_arr
import fitz  # PyMuPDF
import io
from PIL import Image
from pyzbar.pyzbar import decode as qr_decode

def extract_data_from_pdf(pdf_bytes):
    """
    Mengekstrak HANYA konten dari QR code dalam file PDF.
    Mengabaikan semua data teks lain untuk keamanan dan kecepatan.
    """
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                for img in page.get_images(full=True):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    try:
                        pil_img = Image.open(io.BytesIO(image_bytes))
                        decoded_qr = qr_decode(pil_img)
                        if decoded_qr:
                            # Kembalikan konten dari QR code pertama yang ditemukan
                            return decoded_qr[0].data.decode('utf-8')
                    except Exception:
                        continue # Abaikan gambar yang tidak bisa diproses
    except Exception as e:
        print(f"ERROR: Terjadi kesalahan saat memproses PDF untuk QR code: {e}")
    
    return None # Kembalikan None jika tidak ada QR code yang ditemukan
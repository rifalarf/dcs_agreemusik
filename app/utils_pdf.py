import fitz  # PyMuPDF
from PIL import Image
import io

def extract_images_from_pdf(pdf_bytes, dpi=200):
    """
    Render seluruh halaman pertama PDF menjadi gambar (PIL.Image).
    Return: list of PIL.Image (biasanya hanya satu, halaman pertama).
    """
    images = []
    pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
    if pdf.page_count == 0:
        return images
    page = pdf[0]
    # Render halaman ke pixmap (gambar)
    zoom = dpi / 72  # 72 dpi adalah default PDF
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_pil = Image.open(io.BytesIO(pix.tobytes("png")))
    images.append(img_pil)
    return images
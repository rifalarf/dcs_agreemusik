from PIL import Image, ImageDraw, ImageFont
import qrcode
import os
import io
from flask import current_app # Untuk mengakses config

# --- Konfigurasi Font, Ukuran, Posisi, Warna ---
# Ini bisa juga dimuat dari file JSON atau database jika ingin lebih dinamis
# Untuk saat ini, kita hardcode sesuai input Anda.

def get_font_path(font_name):
    font_paths_relative = {
        "nama": "AlexBrush-Regular.ttf",
        "kompetensi": "Belleza-Regular.ttf",
        "tanggal": "Belleza-Regular.ttf",
        "nomor": "OpenSans-Regular.ttf"
    }
    return os.path.join(current_app.config['FONT_BASE_PATH'], font_paths_relative.get(font_name))

FONT_SIZES = {
    "nama": 130,
    "spesialis": 90, # Ganti dari kompetensi
    "tanggal": 38,
    "nomor": 28
}

POSITIONS = {
    "nama_y": 500,
    "spesialis_y": 770, # Ganti dari kompetensi_y
    "tanggal_y": 900,
    "nomor": (85, 950),
    "qr": (85, 1000)
}

COLORS = {
    "nama": "#f7da92",
    "spesialis": "#f7da92", # Ganti dari kompetensi
    "tanggal": "white",
    "nomor": "white"
}

QR_SIZE = (284, 284) # Ukuran QR code pada sertifikat
QR_CORNER_RADIUS = 10

# --- Fungsi Helper untuk Gambar ---
def round_corners(im, radius):
    circle = Image.new('L', (radius * 2, radius * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size

    alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
    alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, h - radius))
    alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (w - radius, 0))
    alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (w - radius, h - radius))

    im.putalpha(alpha)
    return im

def draw_centered_text(drw_obj, text, font, color, y_position, img_width):
    try:
        # textbbox lebih akurat daripada getsize/getbbox di versi Pillow tertentu
        bbox = drw_obj.textbbox((0, 0), text, font=font) 
        text_width = bbox[2] - bbox[0]
    except AttributeError: # Fallback untuk Pillow versi lama
        text_width, _ = drw_obj.textsize(text, font=font)
        
    center_x = (img_width - text_width) / 2
    drw_obj.text((center_x, y_position), text, font=font, fill=color)

# --- Fungsi Utama Generate Sertifikat ---
def generate_certificate_image(sertifikat_obj):
    """
    Menerima objek model Sertifikat dan mengembalikan objek gambar PIL.
    """
    template_path = current_app.config['CERTIFICATE_TEMPLATE_PATH']
    try:
        img = Image.open(template_path).convert("RGB")
    except FileNotFoundError:
        print(f"ERROR: Template sertifikat tidak ditemukan di {template_path}")
        return None

    draw = ImageDraw.Draw(img)

    try:
        fonts = {
            "nama": ImageFont.truetype(get_font_path("nama"), FONT_SIZES["nama"]),
            # Ganti dari kompetensi
            "spesialis": ImageFont.truetype(get_font_path("kompetensi"), FONT_SIZES["spesialis"]),
            "tanggal": ImageFont.truetype(get_font_path("tanggal"), FONT_SIZES["tanggal"]),
            "nomor": ImageFont.truetype(get_font_path("nomor"), FONT_SIZES["nomor"])
        }
    except IOError as e:
        print(f"ERROR: Gagal memuat font: {e}.")
        return None

    if sertifikat_obj.pemilik and sertifikat_obj.pemilik.nama_lengkap:
        nama_peserta_cetak = sertifikat_obj.pemilik.nama_lengkap
    elif sertifikat_obj.pemilik:
        nama_peserta_cetak = sertifikat_obj.pemilik.username
        print(f"Warning: Nama lengkap untuk {sertifikat_obj.pemilik.username} kosong, menggunakan username.")
    else:
        nama_peserta_cetak = "Nama Tidak Tersedia"
        # Ganti nama
        print(f"Error: Pemilik tidak ditemukan untuk sertifikat {sertifikat_obj.id_sertifikat}.")

    # Ganti nama field
    spesialis = sertifikat_obj.spesialis
    tanggal_obj = sertifikat_obj.tanggal_terbit
    id_sertifikat = sertifikat_obj.id_sertifikat
    signature_hash = sertifikat_obj.signature_hash

    if not signature_hash:
        # Ganti nama field
        qr_data = f"{id_sertifikat}|NOT_SIGNED"
    else:
        # Ganti nama field
        qr_data = f"{id_sertifikat}|{signature_hash}"

    draw_centered_text(draw, nama_peserta_cetak, fonts["nama"], COLORS["nama"], POSITIONS["nama_y"], img.width)

    # Ganti nama field dan font
    draw_centered_text(draw, spesialis, fonts["spesialis"], COLORS["spesialis"], POSITIONS["spesialis_y"], img.width)

    try:
        bulan_map = { 1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
                      7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember" }
        tanggal_display = f"{tanggal_obj.day} {bulan_map[tanggal_obj.month]} {tanggal_obj.year}"
    except AttributeError:
        tanggal_display = "Tanggal Tidak Valid"

    draw_centered_text(draw, f"Diterbitkan pada tanggal {tanggal_display}", fonts["tanggal"], COLORS["tanggal"], POSITIONS["tanggal_y"], img.width)

    # Ganti nama field
    draw.text(POSITIONS["nomor"], f"ID : {id_sertifikat}", font=fonts["nomor"], fill=COLORS["nomor"])

    if qr_data:
        qr_img_pil = qrcode.make(qr_data)
        qr_img_pil = qr_img_pil.resize(QR_SIZE).convert("RGBA")
        qr_rounded = round_corners(qr_img_pil, radius=QR_CORNER_RADIUS)
        img.paste(qr_rounded, POSITIONS["qr"], qr_rounded)

    return img
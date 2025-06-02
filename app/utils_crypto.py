import hashlib
import qrcode
import io
import base64
from cryptography.hazmat.primitives import hashes as crypto_hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
from datetime import datetime
from datetime import date # Impor 'date' dari datetime


# --- Kunci ECDSA ---
# Kunci akan dimuat oleh fungsi yang memanggilnya dari Config
def load_private_key(private_key_path):
    try:
        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
            )
        return private_key
    except FileNotFoundError:
        print(f"ERROR: File kunci privat tidak ditemukan di {private_key_path}")
        return None
    except Exception as e:
        print(f"Error memuat kunci privat: {e}")
        return None

def load_public_key(public_key_path):
    try:
        with open(public_key_path, "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read()
            )
        return public_key
    except FileNotFoundError:
        print(f"ERROR: File kunci publik tidak ditemukan di {public_key_path}")
        return None
    except Exception as e:
        print(f"Error memuat kunci publik: {e}")
        return None

# --- Fungsi Helper Kriptografi ---
def generate_certificate_data_string(sertifikat_obj):
    """
    Menggabungkan data sertifikat menjadi satu string standar untuk di-sign.
    PENTING: Urutan dan format field harus konsisten!
    """
    nama_pemilik = sertifikat_obj.pemilik.nama_lengkap if sertifikat_obj.pemilik else "N/A"

    tanggal_terbit_str = "N/A"
    if isinstance(sertifikat_obj.tanggal_terbit, date):
        tanggal_terbit_str = sertifikat_obj.tanggal_terbit.strftime('%Y-%m-%d')
    elif sertifikat_obj.tanggal_terbit is not None:
        tanggal_terbit_str = str(sertifikat_obj.tanggal_terbit)

    # Mengganti nama field
    return (f"{sertifikat_obj.id_sertifikat}|"
            f"{nama_pemilik}|"
            f"{sertifikat_obj.spesialis}|"
            f"{tanggal_terbit_str}|"
            f"{sertifikat_obj.nama_lembaga_penerbit}")

def hash_data(data_string):
    """Melakukan hashing data dengan SHA3-256."""
    return hashlib.sha3_256(data_string.encode('utf-8')).digest()

def sign_data_ecdsa(data_hash, private_key_obj):
    """Menandatangani hash data menggunakan kunci privat ECDSA."""
    if not private_key_obj:
        raise ValueError("Kunci privat tidak valid atau tidak dimuat.")
    signature = private_key_obj.sign(
        data_hash,
        ec.ECDSA(crypto_hashes.SHA256())
    )
    return signature

def verify_signature_ecdsa(data_hash, signature_bytes, public_key_obj):
    """Memverifikasi signature menggunakan kunci publik ECDSA."""
    if not public_key_obj:
        raise ValueError("Kunci publik tidak valid atau tidak dimuat.")
    try:
        public_key_obj.verify(
            signature_bytes,
            data_hash,
            ec.ECDSA(crypto_hashes.SHA256())
        )
        return True
    except InvalidSignature:
        return False
    except Exception as e:
        print(f"Error during ECDSA verification: {e}")
        return False

def generate_qr_code_from_signature_text(b64_signature_text):
    """Membuat QR code dari signature (Base64 text). Mengembalikan image base64."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6, # Ukuran lebih kecil untuk detail
        border=4,
    )
    qr.add_data(b64_signature_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str

def generate_qr_code_with_details(id_sertifikat, b64_signature_text):
    """
    Membuat QR code yang berisi ID Sertifikat dan Signature (Base64 text).
    Mengembalikan image base64.
    """
    # Mengganti nama parameter
    qr_data_string = f"{id_sertifikat}|{b64_signature_text}" # Format baru

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=4,
    )
    qr.add_data(qr_data_string)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str
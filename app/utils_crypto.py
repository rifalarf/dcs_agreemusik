import base64
import hashlib
import io
from datetime import date, datetime

import qrcode
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils


# --- Kunci ECDSA ---
def load_private_key(private_key_path):
    """Memuat kunci privat dari file PEM."""
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
    """Memuat kunci publik dari file PEM."""
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

# --- Fungsi Helper Kriptografi (MODERN API) ---

def create_data_string(sertifikat_obj):
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

    return (f"{sertifikat_obj.id_sertifikat}|"
            f"{nama_pemilik}|"
            f"{sertifikat_obj.spesialis}|"
            f"{tanggal_terbit_str}|"
            f"{sertifikat_obj.penandatangan}")

def hash_data(data_string):
    """Melakukan hashing data dengan SHA256."""
    return hashlib.sha256(data_string.encode('utf-8')).digest()

def sign_data_ecdsa(data_hash, private_key_obj):
    """Menandatangani HASH data menggunakan kunci privat ECDSA (Modern API)."""
    if not private_key_obj:
        raise ValueError("Kunci privat tidak valid atau tidak dimuat.")
    
    # Tandatangani hash, bukan data mentah, dan beri tahu fungsi bahwa data sudah di-hash
    signature = private_key_obj.sign(
        data_hash,
        ec.ECDSA(utils.Prehashed(hashes.SHA256()))
    )
    return signature

def verify_signature_ecdsa(data_hash, signature_bytes, public_key_obj):
    """Memverifikasi signature terhadap HASH data menggunakan kunci publik ECDSA (Modern API)."""
    if not public_key_obj:
        raise ValueError("Kunci publik tidak valid atau tidak dimuat.")
    try:
        # Verifikasi signature terhadap hash
        public_key_obj.verify(
            signature_bytes,
            data_hash,
            ec.ECDSA(utils.Prehashed(hashes.SHA256()))
        )
        return True
    except InvalidSignature:
        return False
    except Exception as e:
        print(f"Error during ECDSA verification: {e}")
        return False

# --- Wrapper Functions ---

def sign_data(data_to_sign, private_key_obj):
    """Wrapper untuk hashing dan penandatanganan data."""
    if not data_to_sign or not isinstance(data_to_sign, str):
        raise ValueError("Data untuk ditandatangani harus berupa string yang tidak kosong.")
    
    data_hash = hash_data(data_to_sign)
    signature_bytes = sign_data_ecdsa(data_hash, private_key_obj)
    
    return base64.b64encode(signature_bytes).decode('utf-8')

def verify_data(data_string, signature_b64, public_key_obj):
    """Wrapper untuk verifikasi signature."""
    if not data_string or not signature_b64:
        raise ValueError("Data dan signature tidak boleh kosong.")

    try:
        signature_bytes = base64.b64decode(signature_b64)
    except (TypeError, ValueError):
        raise ValueError("Format signature Base64 tidak valid.")

    data_hash = hash_data(data_string)
    return verify_signature_ecdsa(data_hash, signature_bytes, public_key_obj)


# --- QR Code ---

def generate_qr_code_from_signature_text(b64_signature_text):
    """Membuat QR code dari signature (Base64 text). Mengembalikan bytes gambar PNG."""
    if not b64_signature_text:
        return None
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=4,
        )
        qr.add_data(b64_signature_text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None
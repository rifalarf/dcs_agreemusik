# generate_keys.py (letakkan di root digital_certificate_signer_v2)
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import os

KEYS_DIR = "keys"
PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, "private_key.pem")
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "public_key.pem")

if not os.path.exists(KEYS_DIR):
    os.makedirs(KEYS_DIR)

# Generate private key
private_key = ec.generate_private_key(
    ec.SECP256R1()
)
# Generate public key
public_key = private_key.public_key()

# Serialize private key to PEM format
pem_private_key = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
# Serialize public key to PEM format
pem_public_key = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

with open(PRIVATE_KEY_PATH, "wb") as f:
    f.write(pem_private_key)
print(f"Private key saved to {PRIVATE_KEY_PATH}")

with open(PUBLIC_KEY_PATH, "wb") as f:
    f.write(pem_public_key)
print(f"Public key saved to {PUBLIC_KEY_PATH}")
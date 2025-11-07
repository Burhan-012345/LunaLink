import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import random
import string

def generate_encryption_key(password: str, salt: bytes = None) -> tuple:
    """Generate encryption key from password"""
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_message(message: str, key: bytes = None) -> str:
    """Encrypt a message"""
    if key is None:
        key = os.environ.get('ENCRYPTION_KEY').encode()
    
    fernet = Fernet(key)
    encrypted = fernet.encrypt(message.encode())
    return base64.urlsafe_b64encode(encrypted).decode()

def decrypt_message(encrypted_message: str, key: bytes = None) -> str:
    """Decrypt a message"""
    if key is None:
        key = os.environ.get('ENCRYPTION_KEY').encode()
    
    fernet = Fernet(key)
    decrypted = fernet.decrypt(base64.urlsafe_b64decode(encrypted_message))
    return decrypted.decode()

def generate_otp(length=6) -> str:
    """Generate OTP code"""
    return ''.join(random.choices(string.digits, k=length))

def hash_file(file_path: str) -> str:
    """Generate hash for file integrity check"""
    import hashlib
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()
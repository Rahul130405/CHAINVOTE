
from cryptography.fernet import Fernet
import base64
import os

# Use fixed key (store in env in production)
SECRET_KEY = b'b9VDVWUOr3QA_93Ax1-hQe04CN2Tj5oGpshMtlAxqcA='  # base64 key

cipher = Fernet(SECRET_KEY)

def encrypt_vote(candidate_id):
    return cipher.encrypt(str(candidate_id).encode()).decode()

def decrypt_vote(encrypted_vote):
    return int(cipher.decrypt(encrypted_vote.encode()).decode())
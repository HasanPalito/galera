from cryptography.fernet import Fernet
import base64

def encrypt_file(key,path):
    fernet = Fernet(key)

    with open(path, 'rb') as file:
        image_data = file.read()
        encrypted = fernet.encrypt(image_data)

    with open(path, 'wb') as file:
        file.write(encrypted)

def decrypt_file(key,path):
    fernet = Fernet(key)

    with open(path, 'rb') as file:
        encrypted = file.read()
        decrypted = fernet.decrypt(encrypted)

    with open(path, 'wb') as file:
        file.write(decrypted)

def generate_key():
    key = Fernet.generate_key()
    return key
from base64 import b64decode, b64encode

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

BLOCK_SIZE = 16


class AESCipher:
    def __init__(self, key):
        self.key = key

    def pad(self, text):
        """
        Pads the text to be encrypted to a multiple of 16 bytes (AES block size).
        """
        padding_length = BLOCK_SIZE - len(text) % BLOCK_SIZE
        return text + (padding_length * chr(padding_length))

    def unpad(self, text):
        """
        Removes the padding from the decrypted text.
        """
        padding_length = text[-1]
        return text[:-padding_length]

    def encrypt(self, plaintext):
        """
        Encrypts plaintext using AES-256 encryption.
        """
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plaintext = self.pad(plaintext)
        ciphertext = cipher.encrypt(plaintext.encode("utf-8"))
        return b64encode(iv + ciphertext).decode("utf-8")

    def decrypt(self, ciphertext):
        """
        Decrypts AES-encrypted ciphertext.
        """
        ciphertext = b64decode(ciphertext)
        iv = ciphertext[: AES.block_size]
        ciphertext = ciphertext[AES.block_size :]  # noqa: E203
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ciphertext)
        return self.unpad(decrypted).decode("utf-8")


def encrypt_private_key(private_key):
    aes_encryption_key = get_random_bytes(32)
    cipher = AESCipher(aes_encryption_key)
    encrypted_private_key = cipher.encrypt(private_key)
    return aes_encryption_key, encrypted_private_key


def encrypt_private_key_as_string(private_key):
    encryption_key, encrypted_private_key = encrypt_private_key(private_key)
    return f'{b64encode(encryption_key).decode("utf-8")}::{encrypted_private_key}'


def decrypt_from_cipher_string(key_string):
    try:
        key_string = key_string.decode("utf-8")
        encryption_key, encrypted_private_key = key_string.split("::")
    except ValueError:
        return None

    cipher = AESCipher(b64decode(encryption_key))
    private_key = cipher.decrypt(encrypted_private_key)
    return private_key

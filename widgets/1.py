from Crypto.Cipher.AES import new, MODE_CBC, block_size
from Crypto.Util.Padding import pad, unpad
from Crypto.Protocol.KDF import PBKDF2
from base64 import b64encode, b64decode


def encrypt(data, key_):
    cipher = new(key_, MODE_CBC)
    encrypted_data = cipher.encrypt(pad(data.encode(), block_size))
    return b64encode(cipher.iv + encrypted_data).decode()


def decrypt(encrypted, key_):
    cipher = new(key_, MODE_CBC, b64decode(encrypted)[:16])
    return unpad(cipher.decrypt(b64decode(encrypted)[16:]), block_size).decode()


# key = PBKDF2(self.password, b'', dkLen=32, count=100000)
from cryptography.fernet import Fernet

with open("key.key", "wb") as key_f, open("token.crypt", "wb") as token_f:
    key = Fernet.generate_key()
    token = Fernet(key).encrypt(input("Insert token: ").encode())
    key_f.write(key)
    token_f.write(token)

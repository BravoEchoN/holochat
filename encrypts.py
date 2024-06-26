from cryptography.fernet import Fernet

def generate_and_store_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)
    print("Encryption key generated and saved to secret.key")

def load_encryption_key():
    with open("secret.key", "rb") as key_file:
        return Fernet(key_file.read())

def encrypt_data(data, fernet):
    return fernet.encrypt(data.encode()).decode()

if __name__ == "__main__":
    # Step 1: Generate and store encryption key
    generate_and_store_key()

    # Step 2: Load encryption key
    fernet = load_encryption_key()

    # Step 3: Encrypt API key
    api_key = "QplK9H3lWZxRv0iM7wF2KbnS5Rl4yjPzGxZNAuD6V2ntbph9U1"  # Replace with your actual API key
    encrypted_api_key = encrypt_data(api_key, fernet)
    with open("api_key.txt", "w") as key_file:
        key_file.write(encrypted_api_key)
    print("API key encrypted and saved to api_key.txt")

    # Step 4: Encrypt password
    password = "123456"  # Replace with your actual password
    encrypted_password = encrypt_data(password, fernet)
    with open("password.txt", "w") as key_file:
        key_file.write(encrypted_password)
    print("Password encrypted and saved to password.txt")

import os
import json
import hashlib
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIVATE_KEY_PATH = "private_key.pem"
PUBLIC_KEY_PATH = os.path.join(APP_ROOT, "public_key.pem")

def generate_keys():
    """Generates RSA Private/Public keys."""
    print("Generating RSA Keys...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Save Private Key
    with open(PRIVATE_KEY_PATH, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Save Public Key to App Root
    public_key = private_key.public_key()
    with open(PUBLIC_KEY_PATH, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    print(f"Keys generated!\nPrivate: {PRIVATE_KEY_PATH}\nPublic: {PUBLIC_KEY_PATH}")

def generate_license(client_name, hwid, days_valid=None):
    """Generates a signed license.lic file for a client."""
    if not os.path.exists(PRIVATE_KEY_PATH):
        print("Error: private_key.pem not found. Run key generation first.")
        return

    payload_dict = {
        "client": client_name,
        "hwid": hwid,
        "type": "standard"
    }

    if days_valid:
        from datetime import datetime, timedelta
        exp_date = datetime.now() + timedelta(days=int(days_valid))
        payload_dict["expiration"] = exp_date.strftime("%Y-%m-%d")
        print(f"-> Expiração definida para: {payload_dict['expiration']}")
    payload_str = json.dumps(payload_dict)
    payload_bytes = payload_str.encode('utf-8')

    # Load Private Key
    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

    # Sign data
    signature = private_key.sign(
        payload_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    license_data = {
        "payload": payload_str,
        "signature": signature.hex()
    }

    output_file = os.path.join(APP_ROOT, "license.lic")
    with open(output_file, "w") as f:
        json.dump(license_data, f, indent=4)

    print(f"License generated: {output_file}")
    print(f"HWID Bound: {hwid}")

def main():
    while True:
        print("\n--- ADMIN TOOLS ---")
        print("1. Generate RSA Keys (Overwrite if exists)")
        print("2. Generate Client License")
        print("3. Exit")
        choice = input("Select: ")

        if choice == '1':
            generate_keys()
        elif choice == '2':
            name = input("Client Name: ")
            hwid = input("Client Machine HWID: ")
            days = input("Validade em dias (Enter para perpétuo): ")
            generate_license(name, hwid, days if days.strip() else None)
        elif choice == '3':
            break

if __name__ == "__main__":
    main()

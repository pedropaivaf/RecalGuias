import os
import json
import sqlite3
import hashlib
import uuid
import uuid
import platform
import subprocess
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import bcrypt
import requests

# --- CONFIG ---
import sys
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LICENSE_FILE = os.path.join(BASE_DIR, 'license.lic')
PUBLIC_KEY_FILE = os.path.join(BASE_DIR, 'public_key.pem')
DB_FILE = os.path.join(BASE_DIR, 'local_data.db')

# COLE O LINK DO CSV DO GOOGLE SHEETS AQUI (ARQUIVO -> COMPARTILHAR -> PUBLICAR NA WEB -> CSV)
ONLINE_CHECK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTmw-4oKRFF8L7oeKeGCRxRa92gwR3ivZoObM94OkZtqgsmSafQwRVVzmZ_QKJRHMKrua380Dn9_8ZB/pub?output=csv" 

def check_online_status(hwid):
    """
    Verifica status em planilha online.
    Retorna: (bool_permissao, str_motivo)
    """
    if not ONLINE_CHECK_URL:
        return True, "Online check disabled"

    try:
        print(f"DEBUG: Checking online status for {hwid}...")
        response = requests.get(ONLINE_CHECK_URL, timeout=5)
        response.raise_for_status()
        
        # Parse CSV simples (HWID,STATUS)
        lines = response.text.splitlines()
        for line in lines:
            parts = line.split(',')
            if len(parts) >= 2:
                row_hwid = parts[0].strip()
                row_status = parts[1].strip().upper()
                
                if row_hwid == hwid:
                    if row_status == 'BLOQUEADO':
                        return False, "Acesso BLOQUEADO pelo administrador."
                    elif row_status == 'INATIVO':
                         return False, "Sua licença está INATIVA."
                    # Se achar e estiver ATIVO (ou qualquer outra coisa), libera (ou ajusta conforme regra)
                    return True, "Client Found active"
                    
        # Se não achar o HWID na lista?
        # Política: Se não está na lista, libera (padrão) ou bloqueia?
        # Para sistemas distribuídos, melhor liberar se não explicitamente bloqueado, ou bloquear se for strict whitelist.
        # Vou assumir BLOQUEIO se não achar, para segurança total? Não, o usuário pediu "se verificar que não esta ativo bloqueia".
        # Isso pode significar: Se achar e status != ativo -> Bloqueia.
        # Se não achar, assume OK (para não quebrar clientes novos antes de atualizar planilha).
        return True, "HWID not in list (Default Allow)"
        
    except Exception as e:
        print(f"DEBUG: Online Check Failed: {e}")
        # Se falhar internet, PERMITE (Fail Open) para não travar uso legítimo offline?
        # O usuário queria "Bloquear acesso". Se o cliente cortar a net, ele burla.
        # Mas se for "Fully Online Requisite", trava se der erro.
        # Vou deixar Fail Open (True) com aviso, pois o sistema era originalmente offline.
        return True, "Offline/Error (Allowing access)"

def get_machine_id():
    """Generates a unique machine ID based on hardware traits."""
    try:
        # Combination of node name, system, release, and machine type
        # plus the MAC address (uuid.getnode)
        # This is simple but reasonably effective for offline binding
        details = [
            platform.node(),
            platform.system(),
            platform.machine(),
            str(uuid.getnode())
        ]
        unique_str = "_".join(details)
        return hashlib.sha256(unique_str.encode()).hexdigest()
    except Exception:
        # Fallback
        return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()

def validate_license():
    """
    Validates the license.lic file against the public_key.pem and current HWID.
    Returns: (bool, message, payload_dict)
    """
    if not os.path.exists(PUBLIC_KEY_FILE):
        return False, "Public Key not found.", None
    
    if not os.path.exists(LICENSE_FILE):
        return False, "License file not found.", None

    try:
        # Load Public Key
        with open(PUBLIC_KEY_FILE, "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read()
            )

        # Load License
        with open(LICENSE_FILE, "rb") as f:
            license_data = json.load(f)

        signature_hex = license_data.get('signature')
        payload_str = license_data.get('payload')

        if not signature_hex or not payload_str:
            return False, "Invalid license format.", None

        signature = bytes.fromhex(signature_hex)
        payload_bytes = payload_str.encode('utf-8')

        # Verify Signature
        public_key.verify(
            signature,
            payload_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Decode Payload
        payload = json.loads(payload_str)
        
        # 1. Check HWID
        current_hwid = get_machine_id()
        if payload.get('hwid') != current_hwid:
            return False, f"Hardware Mismatch. License HWID: {payload.get('hwid')[:8]}... Current: {current_hwid[:8]}...", None

        # 2. Check Expiration
        expiration = payload.get('expiration')
        if expiration:
            from datetime import datetime
            try:
                exp_date = datetime.strptime(expiration, "%Y-%m-%d")
                if datetime.now() > exp_date:
                    return False, f"Licença Expirada em {expiration}.", None
            except ValueError:
                pass

        # 3. Online Check (Google Sheets)
        is_allowed, msg = check_online_status(current_hwid)
        if not is_allowed:
             return False, f"Verificação Online: {msg}", None

        return True, "License Valid", payload

    except Exception as e:
        return False, f"Validation Error: {str(e)}", None

def init_db():
    """Initializes the local authentication database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    ''')
    # Default admin user if empty
    c.execute('SELECT count(*) FROM users')
    if c.fetchone()[0] == 0:
        # Create default user 'pessoal'
        password = "1234".encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('pessoal', hashed.decode('utf-8')))
        print("Default user 'pessoal' created.")
    
    conn.commit()
    conn.close()

def login(username, password):
    """
    Verifies username and password against local_data.db.
    Returns: bool
    """
    if not os.path.exists(DB_FILE):
        init_db()

    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        row = c.fetchone()
        conn.close()

        if row:
            stored_hash = row[0].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                return True
    except Exception as e:
        print(f"Login Error: {e}")
        
    return False

# Initialize DB on import if it doesn't exist
if not os.path.exists(DB_FILE):
    init_db()

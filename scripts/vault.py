"""
Vault — Notas privadas encriptadas para el desarrollador.

Uso:
  python scripts/vault.py init          # Crear el vault por primera vez
  python scripts/vault.py read          # Leer el contenido
  python scripts/vault.py edit          # Editar el contenido
  python scripts/vault.py change-pass   # Cambiar la contraseña maestra

El archivo encriptado se guarda en: .vault
No subir .vault al repositorio (ya está en .gitignore).
"""
import sys
import os
import getpass
import tempfile
import subprocess

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken
import base64

VAULT_FILE = ".vault"
ITERATIONS = 480_000  # PBKDF2 iterations (OWASP 2023)


def _getpass(prompt: str) -> str:
    """getpass con fallback visible si falla en PowerShell."""
    try:
        pwd = getpass.getpass(prompt)
        if pwd:
            return pwd
        # Si devuelve vacío, puede ser un problema de terminal — usar input visible
        print("  (contraseña no detectada, cambiando a modo visible)")
        return input(prompt)
    except Exception:
        return input(prompt)


# ── Derivar clave Fernet desde contraseña + salt ─────────────────
def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def _encrypt(plaintext: str, password: str) -> bytes:
    salt = os.urandom(16)
    key = _derive_key(password, salt)
    token = Fernet(key).encrypt(plaintext.encode())
    # Formato: salt(16) + token
    return salt + token


def _decrypt(data: bytes, password: str) -> str:
    salt = data[:16]
    token = data[16:]
    key = _derive_key(password, salt)
    try:
        return Fernet(key).decrypt(token).decode()
    except InvalidToken:
        raise ValueError("Contraseña incorrecta o archivo corrupto.")


# ── Comandos ─────────────────────────────────────────────────────
def cmd_init():
    if os.path.exists(VAULT_FILE):
        print(f"El vault ya existe en '{VAULT_FILE}'.")
        print("Usá 'python scripts/vault.py read' para leerlo.")
        return

    print("Creando vault nuevo...")
    password = _getpass("Contraseña maestra: ")
    confirm = _getpass("Confirmar contraseña: ")
    if password != confirm:
        print("Las contraseñas no coinciden.")
        sys.exit(1)

    content = _default_content()
    data = _encrypt(content, password)
    with open(VAULT_FILE, "wb") as f:
        f.write(data)
    print(f"Vault creado en '{VAULT_FILE}'.")
    print("IMPORTANTE: No subas este archivo al repositorio.")


def cmd_read():
    _check_exists()
    password = _getpass("Contraseña maestra: ")
    content = _load_and_decrypt(password)
    print("\n" + "─" * 60)
    print(content)
    print("─" * 60)


def cmd_edit():
    _check_exists()
    password = _getpass("Contraseña maestra: ")
    content = _load_and_decrypt(password)

    # Abrir en editor de texto temporal
    editor = os.environ.get("EDITOR", "notepad" if os.name == "nt" else "nano")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        subprocess.call([editor, tmp_path])
        with open(tmp_path, "r", encoding="utf-8") as f:
            new_content = f.read()
    finally:
        os.unlink(tmp_path)

    if new_content == content:
        print("Sin cambios.")
        return

    data = _encrypt(new_content, password)
    with open(VAULT_FILE, "wb") as f:
        f.write(data)
    print("Vault actualizado.")


def cmd_change_pass():
    _check_exists()
    old_password = _getpass("Contraseña actual: ")
    content = _load_and_decrypt(old_password)

    new_password = _getpass("Nueva contraseña: ")
    confirm = _getpass("Confirmar nueva contraseña: ")
    if new_password != confirm:
        print("Las contraseñas no coinciden.")
        sys.exit(1)

    data = _encrypt(content, new_password)
    with open(VAULT_FILE, "wb") as f:
        f.write(data)
    print("Contraseña cambiada correctamente.")


# ── Helpers ──────────────────────────────────────────────────────
def _check_exists():
    if not os.path.exists(VAULT_FILE):
        print(f"No existe el vault. Crealo con: python scripts/vault.py init")
        sys.exit(1)


def _load_and_decrypt(password: str) -> str:
    with open(VAULT_FILE, "rb") as f:
        data = f.read()
    try:
        return _decrypt(data, password)
    except ValueError as e:
        print(str(e))
        sys.exit(1)


def _default_content() -> str:
    return """\
# ═══════════════════════════════════════════════════════════
#  HEYDEMIN — NOTAS PRIVADAS DEL DESARROLLADOR
#  Este archivo está encriptado con AES-256 (Fernet + PBKDF2)
# ═══════════════════════════════════════════════════════════

## SUMUP — CREDENCIALES
API Key:         sup_sk_...
Merchant Code:   M5VRRRFX
Pay to Email:    admin@heydemin.com
Dashboard:       https://me.sumup.com

## BASE DE DATOS — PRODUCCIÓN
Host:     ...
Puerto:   5432
DB:       heydemin_db
Usuario:  ...
Password: ...
URL:      postgresql://usuario:password@host:5432/heydemin_db

## ADMIN — USUARIOS
# Para agregar/quitar usuarios:
#   python scripts/manage_admins.py list
#   python scripts/manage_admins.py add email@ejemplo.com password
#   python scripts/manage_admins.py delete email@ejemplo.com
#   python scripts/manage_admins.py password email@ejemplo.com nueva_pass

Usuario 1:  admin@heydemin.com
Password:   (la que configuraste)

## SESSION_SECRET
(guardá acá el valor del .env)

## SERVIDOR / HOSTING
Proveedor:  ...
IP:         ...
SSH:        ssh usuario@ip
Panel:      ...

## NOTAS
- Renovar API key de SumUp si se compromete
- Backup de DB: ...
"""


COMMANDS = {
    "init": cmd_init,
    "read": cmd_read,
    "edit": cmd_edit,
    "change-pass": cmd_change_pass,
}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[args[0]]()

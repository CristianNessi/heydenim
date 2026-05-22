"""
Gestión de usuarios admin.

Uso:
  python scripts/manage_admins.py list
  python scripts/manage_admins.py add <email> <password>
  python scripts/manage_admins.py delete <email>
  python scripts/manage_admins.py disable <email>
  python scripts/manage_admins.py enable <email>
  python scripts/manage_admins.py password <email> <nueva_password>
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from app.db.database import SessionLocal
from app.db.models.admin_user import AdminUser


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def cmd_list():
    db = SessionLocal()
    users = db.query(AdminUser).order_by(AdminUser.id).all()
    db.close()
    if not users:
        print("No hay usuarios admin.")
        return
    print(f"{'ID':<5} {'Email':<35} {'Activo':<8} {'Creado'}")
    print("-" * 70)
    for u in users:
        estado = "✓" if u.is_active else "✗"
        fecha = u.created_at.strftime("%d/%m/%Y %H:%M") if u.created_at else "—"
        print(f"{u.id:<5} {u.email:<35} {estado:<8} {fecha}")


def cmd_add(email: str, password: str):
    db = SessionLocal()
    exists = db.query(AdminUser).filter(AdminUser.email == email.lower()).first()
    if exists:
        print(f"Ya existe un usuario con el email: {email}")
        db.close()
        return
    user = AdminUser(email=email.lower(), password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.close()
    print(f"Usuario creado: {email}")


def cmd_delete(email: str):
    db = SessionLocal()
    user = db.query(AdminUser).filter(AdminUser.email == email.lower()).first()
    if not user:
        print(f"No se encontró el usuario: {email}")
        db.close()
        return
    confirm = input(f"¿Eliminar '{email}' permanentemente? (s/n): ")
    if confirm.lower() != "s":
        print("Cancelado.")
        db.close()
        return
    db.delete(user)
    db.commit()
    db.close()
    print(f"Usuario eliminado: {email}")


def cmd_disable(email: str):
    _set_active(email, False)


def cmd_enable(email: str):
    _set_active(email, True)


def _set_active(email: str, active: bool):
    db = SessionLocal()
    user = db.query(AdminUser).filter(AdminUser.email == email.lower()).first()
    if not user:
        print(f"No se encontró el usuario: {email}")
        db.close()
        return
    user.is_active = active
    db.commit()
    db.close()
    estado = "activado" if active else "desactivado"
    print(f"Usuario {estado}: {email}")


def cmd_password(email: str, new_password: str):
    db = SessionLocal()
    user = db.query(AdminUser).filter(AdminUser.email == email.lower()).first()
    if not user:
        print(f"No se encontró el usuario: {email}")
        db.close()
        return
    user.password_hash = hash_password(new_password)
    db.commit()
    db.close()
    print(f"Contraseña actualizada: {email}")


COMMANDS = {
    "list": (cmd_list, 0),
    "add": (cmd_add, 2),
    "delete": (cmd_delete, 1),
    "disable": (cmd_disable, 1),
    "enable": (cmd_enable, 1),
    "password": (cmd_password, 2),
}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in COMMANDS:
        print(__doc__)
        sys.exit(1)

    cmd = args[0]
    fn, n_args = COMMANDS[cmd]
    if len(args) - 1 != n_args:
        print(f"Uso incorrecto para '{cmd}'. Ver ayuda:\n{__doc__}")
        sys.exit(1)

    fn(*args[1:])

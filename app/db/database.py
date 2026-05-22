from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env", override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def ensure_schema():
    """Añade columnas nuevas en bases de datos ya existentes."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)

    # Columnas de products
    if "products" in inspector.get_table_names():
        columns = {col["name"] for col in inspector.get_columns("products")}
        if "size_stock" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE products ADD COLUMN size_stock TEXT"))
        if "images" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE products ADD COLUMN images TEXT"))
        if "discount" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE products ADD COLUMN discount INTEGER DEFAULT 0"))
        if "is_featured" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE products ADD COLUMN is_featured BOOLEAN DEFAULT FALSE"))

    # Tablas de analytics, ventas y contenido
    tables = inspector.get_table_names()
    if "page_views" not in tables or "click_events" not in tables or "sales" not in tables:
        Base.metadata.create_all(bind=engine)
    if "site_content" not in tables:
        Base.metadata.create_all(bind=engine)
    if "notifications" not in tables:
        Base.metadata.create_all(bind=engine)
    if "admin_users" not in tables:
        Base.metadata.create_all(bind=engine)
        # Migrar usuario del .env a la tabla si existe
        _migrate_env_admin()
    else:
        # Agregar columnas nuevas si no existen
        sc_cols = {col["name"] for col in inspector.get_columns("site_content")}
        new_cols = {
            "reviews_images": "TEXT",
            "topbar_items": "TEXT",
            "social_links": "TEXT",
            "whatsapp_number": "TEXT",
            "whatsapp_display": "TEXT",
            "contact_email": "TEXT",
        }
        for col_name, col_type in new_cols.items():
            if col_name not in sc_cols:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE site_content ADD COLUMN {col_name} {col_type}"))


def _migrate_env_admin():
    """Crea el usuario admin del .env en la tabla admin_users si no existe."""
    email = os.getenv("ADMIN_EMAIL", "").strip()
    password_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip()
    if not email or not password_hash:
        return
    from app.db.models.admin_user import AdminUser
    db = SessionLocal()
    try:
        exists = db.query(AdminUser).filter(AdminUser.email == email).first()
        if not exists:
            db.add(AdminUser(email=email, password_hash=password_hash))
            db.commit()
    finally:
        db.close()


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
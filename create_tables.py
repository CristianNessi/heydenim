from app.db.database import Base, engine

# IMPORTA TODOS LOS MODELOS (IMPORTANTE)
from app.db.models.product import Product
# si tienes más modelos, agrégalos aquí:
# from app.db.models.cart import Cart

print("Creando tablas...")

Base.metadata.create_all(bind=engine)

print("✅ Tablas creadas correctamente")
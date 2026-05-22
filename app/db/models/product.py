from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import Text

from app.db.database import Base


class Product(Base):

    __tablename__ = "products"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    description = Column(
        Text,
        nullable=False
    )

    price = Column(
        Float,
        nullable=False
    )

    image = Column(
        String,
        nullable=True
    )

    stock = Column(
        Integer,
        default=0
    )

    # NUEVO
    colors = Column(
        String,
        nullable=True
    )

    # NUEVO
    sizes = Column(
        String,
        nullable=True
    )

    size_stock = Column(
        Text,
        nullable=True
    )

    images = Column(
        Text,
        nullable=True
    )

    # Descuento en porcentaje (0 = sin descuento)
    discount = Column(
        Integer,
        default=0,
        nullable=False
    )

    # Producto destacado (recuadro especial en la tienda)
    is_featured = Column(
        Boolean,
        default=False
    )
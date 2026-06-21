from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.db.database import Base


class Sale(Base):
    """Registro de cada venta completada."""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=True)       # puede ser None si se borró el producto
    product_name = Column(String, nullable=False)
    product_price = Column(Float, nullable=False)     # precio al momento de la venta
    discount = Column(Integer, default=0)             # % de descuento aplicado
    final_price = Column(Float, nullable=False)       # precio real cobrado
    quantity = Column(Integer, default=1)
    size = Column(String, nullable=True)
    color = Column(String, nullable=True)
    total = Column(Float, nullable=False)             # final_price * quantity
    checkout_reference = Column(String, nullable=True)
    transaction_id = Column(String, nullable=True)
    is_refunded = Column(Boolean, default=False)
    refund_amount = Column(Float, default=0.0)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

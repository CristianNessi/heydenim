from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.database import Base


class Notification(Base):
    """Notificaciones del panel admin."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    # Tipos: "sale" | "low_stock" | "out_of_stock" | "no_activity" | "new_visit_milestone"
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    # Referencia opcional al producto o venta relacionada
    ref_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

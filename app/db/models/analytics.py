from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.db.database import Base


class PageView(Base):
    __tablename__ = "page_views"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, nullable=False, default="/")
    referrer = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    ip_hash = Column(String, nullable=True)   # hashed, no PII
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ClickEvent(Base):
    __tablename__ = "click_events"

    id = Column(Integer, primary_key=True, index=True)
    element = Column(String, nullable=False)   # e.g. "product-card", "add-to-cart"
    label = Column(String, nullable=True)      # e.g. product name
    product_id = Column(Integer, nullable=True)
    x_pct = Column(Integer, nullable=True)     # % horizontal en la página
    y_pct = Column(Integer, nullable=True)     # % vertical en la página
    created_at = Column(DateTime(timezone=True), server_default=func.now())

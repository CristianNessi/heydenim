from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class SiteContent(Base):
    __tablename__ = "site_content"

    id = Column(Integer, primary_key=True)
    # "hero" | "about" | "reviews" | "topbar" | "social"
    section = Column(String, unique=True, nullable=False)
    # Hero
    hero_title = Column(String, nullable=True)
    hero_subtitle = Column(String, nullable=True)
    hero_image = Column(String, nullable=True)
    # About / Nosotras
    about_text = Column(Text, nullable=True)
    about_extra = Column(String, nullable=True)
    about_image = Column(String, nullable=True)
    # Reviews — JSON array de URLs: ["url1","url2","url3"]
    reviews_images = Column(Text, nullable=True)
    # Topbar — JSON array de mensajes: ["🏷️ 15% OFF...", "🚚 Envío gratis..."]
    topbar_items = Column(Text, nullable=True)
    # Social — JSON object: {"instagram":"url","tiktok":"url","facebook":"url","pinterest":"url","youtube":"url","twitter":"url"}
    social_links = Column(Text, nullable=True)
    # Contacto
    whatsapp_number = Column(String, nullable=True)   # número para wa.me
    whatsapp_display = Column(String, nullable=True)  # texto visible
    contact_email = Column(String, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import json

# ROUTERS
from app.api.routes import products, cart, checkout, admin, analytics, seo

# CONFIG
from app.core.config import settings

# DATABASE
from app.db.database import engine, Base, ensure_schema, SessionLocal

# MODELS
from app.db.models.product import Product
from app.db.models.analytics import PageView, ClickEvent
from app.db.models.sale import Sale
from app.db.models.site_content import SiteContent
from app.db.models.notification import Notification
from app.db.models.admin_user import AdminUser


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate()
    print("✅ Configuración correcta")
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    yield


app = FastAPI(
    title="Heydemin",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(admin.router)
app.include_router(analytics.router)
app.include_router(seo.router)


def _load_site_content() -> dict:
    """Carga el contenido editable del landing desde la DB."""
    def _json(val, fallback):
        if not val:
            return fallback
        try:
            return json.loads(val)
        except Exception:
            return fallback

    db = SessionLocal()
    try:
        hero    = db.query(SiteContent).filter(SiteContent.section == "hero").first()
        about   = db.query(SiteContent).filter(SiteContent.section == "about").first()
        topbar  = db.query(SiteContent).filter(SiteContent.section == "topbar").first()
        social  = db.query(SiteContent).filter(SiteContent.section == "social").first()
        reviews = db.query(SiteContent).filter(SiteContent.section == "reviews").first()
        return {
            "hero_title":    hero.hero_title    if hero and hero.hero_title    else None,
            "hero_subtitle": hero.hero_subtitle if hero and hero.hero_subtitle else None,
            "hero_image":    hero.hero_image    if hero and hero.hero_image    else None,
            "about_text":    about.about_text   if about and about.about_text  else None,
            "about_extra":   about.about_extra  if about and about.about_extra else None,
            "about_image":   about.about_image  if about and about.about_image else None,
            "topbar_items":  _json(topbar.topbar_items   if topbar  else None, []),
            "social_links":  _json(social.social_links   if social  else None, {}),
            "reviews_images":_json(reviews.reviews_images if reviews else None, []),
            "whatsapp_number":  topbar.whatsapp_number  if topbar and topbar.whatsapp_number  else None,
            "whatsapp_display": topbar.whatsapp_display if topbar and topbar.whatsapp_display else None,
            "contact_email":    topbar.contact_email    if topbar and topbar.contact_email    else None,
        }
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    content = _load_site_content()
    return templates.TemplateResponse(
        request,
        "index.html",
        {"request": request, **content},
    )
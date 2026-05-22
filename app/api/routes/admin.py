from fastapi import APIRouter
from fastapi import Request
from fastapi import Form
from fastapi import UploadFile
from fastapi import File
from fastapi import Depends
from fastapi import HTTPException

from fastapi.responses import RedirectResponse

from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.product import Product
from app.db.models.site_content import SiteContent
from app.db.models.admin_user import AdminUser

import uuid
import time
import bcrypt
import imghdr


def _get_any_admin_hash(db: Session) -> str:
    """Devuelve el hash del primer admin activo para verificar confirmaciones."""
    user = db.query(AdminUser).filter(AdminUser.is_active == True).first()
    return user.password_hash if user else ""

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

templates = Jinja2Templates(
    directory="app/templates"
)

# ── Rate limiting simple en memoria ──────────────────────────────
_login_attempts: dict[str, list[float]] = {}
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 300  # 5 minutos

ALLOWED_IMAGE_TYPES = {"jpeg", "png", "gif", "webp"}
MAX_IMAGE_SIZE = 8 * 1024 * 1024  # 8 MB


def _check_rate_limit(ip: str) -> bool:
    """Devuelve True si el IP puede intentar login, False si está bloqueado."""
    now = time.time()
    attempts = _login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < _WINDOW_SECONDS]
    _login_attempts[ip] = attempts
    return len(attempts) < _MAX_ATTEMPTS


def _record_attempt(ip: str):
    now = time.time()
    _login_attempts.setdefault(ip, []).append(now)


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def _is_authenticated(request: Request) -> bool:
    return request.cookies.get("admin_auth") == "true"


def _save_image(upload: UploadFile) -> str | None:
    """Valida y guarda una imagen. Devuelve la URL o None si es inválida."""
    data = upload.file.read()
    if len(data) > MAX_IMAGE_SIZE:
        return None
    img_type = imghdr.what(None, h=data)
    if img_type not in ALLOWED_IMAGE_TYPES:
        return None
    ext = "jpg" if img_type == "jpeg" else img_type
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = f"app/static/uploads/{filename}"
    with open(filepath, "wb") as f:
        f.write(data)
    return f"/static/uploads/{filename}"


# =====================================
# LOGIN PAGE
# =====================================
@router.get("/login")
def admin_login_page(request: Request):

    return templates.TemplateResponse(
        request,
        "admin/login.html",
        {
            "request": request
        }
    )


# =====================================
# LOGIN ACTION
# =====================================
@router.post("/login")
def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"

    if not _check_rate_limit(ip):
        return RedirectResponse(url="/admin/login?error=blocked", status_code=302)

    user = db.query(AdminUser).filter(
        AdminUser.email == email.strip().lower(),
        AdminUser.is_active == True,
    ).first()

    if user and _verify_password(password, user.password_hash):
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(
            key="admin_auth",
            value="true",
            httponly=True,
            samesite="lax",
            secure=True,         # HTTPS en producción
            max_age=60 * 60 * 8,
        )
        _login_attempts.pop(ip, None)
        return response

    _record_attempt(ip)
    return RedirectResponse(url="/admin/login?error=1", status_code=302)


# =====================================
# LOGOUT
# =====================================
@router.get("/logout")
def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_auth")
    return response
@router.get("/dashboard")
def dashboard(request: Request):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {"request": request}
    )


# =====================================
# PRODUCTS LIST
# =====================================
@router.get("/products")
def admin_products(request: Request, db: Session = Depends(get_db)):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    products = db.query(Product).all()
    return templates.TemplateResponse(
        request,
        "admin/products.html",
        {"request": request, "products": products}
    )


# =====================================
# NEW PRODUCT PAGE
# =====================================
@router.get("/products/new")
def new_product_page(request: Request):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    return templates.TemplateResponse(
        request,
        "admin/product_form.html",
        {"request": request}
    )


# =====================================
# CREATE PRODUCT
# =====================================
@router.post("/products/new")
def create_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    colors: str = Form(None),
    sizes: str = Form(None),
    size_stock: str = Form(None),
    discount: int = Form(0),
    is_featured: bool = Form(False),
    image: UploadFile = File(...),
    extra_images: list[UploadFile] = File(default=[]),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):

    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    if not _verify_password(confirm_password, _get_any_admin_hash(db)):
        return RedirectResponse(url="/admin/products/new?error=password", status_code=302)

    image_urls = []
    url = _save_image(image)
    if not url:
        return RedirectResponse(url="/admin/products/new?error=imagen", status_code=302)
    image_urls.append(url)

    for extra in extra_images:
        if extra and extra.filename:
            extra_url = _save_image(extra)
            if extra_url:
                image_urls.append(extra_url)

    image_url = image_urls[0]
    images_str = ",".join(image_urls)

    product = Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        colors=colors,
        sizes=sizes,
        size_stock=size_stock,
        discount=max(0, min(100, discount)),
        is_featured=is_featured,
        image=image_url,
        images=images_str
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return RedirectResponse(url="/admin/dashboard?ok=producto_creado", status_code=302)
# =====================================
@router.post("/products/delete/{product_id}")
def delete_product(
    request: Request,
    product_id: int,
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    if not _verify_password(confirm_password, _get_any_admin_hash(db)):
        return RedirectResponse(url=f"/admin/products?error=password", status_code=302)

    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse(url="/admin/dashboard?ok=producto_eliminado", status_code=302)
def edit_product_page(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db)
):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/admin/products", status_code=302)

    return templates.TemplateResponse(
        request,
        "admin/product_form.html",
        {"request": request, "product": product, "title": "Editar producto"}
    )


# =====================================
# UPDATE PRODUCT
# =====================================
@router.post("/products/edit/{product_id}")
def update_product(
    request: Request,
    product_id: int,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    colors: str = Form(None),
    sizes: str = Form(None),
    size_stock: str = Form(None),
    discount: int = Form(0),
    is_featured: bool = Form(False),
    image: UploadFile = File(None),
    extra_images: list[UploadFile] = File(default=[]),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    if not _verify_password(confirm_password, _get_any_admin_hash(db)):
        return RedirectResponse(url=f"/admin/products/edit/{product_id}?error=password", status_code=302)

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:

        return RedirectResponse(
            url="/admin/products",
            status_code=302
        )

    product.name = name
    product.description = description
    product.price = price
    product.stock = stock
    product.colors = colors
    product.sizes = sizes
    product.size_stock = size_stock
    product.discount = max(0, min(100, discount))
    product.is_featured = is_featured

    # =========================
    # NEW IMAGE(S)
    # =========================

    new_urls = []

    if image and image.filename:
        url = _save_image(image)
        if url:
            new_urls.append(url)

    for extra in extra_images:
        if extra and extra.filename:
            extra_url = _save_image(extra)
            if extra_url:
                new_urls.append(extra_url)

    if new_urls:
        product.image = new_urls[0]
        product.images = ",".join(new_urls)
    elif not product.images and product.image:
        product.images = product.image

    db.commit()

    return RedirectResponse(
        url="/admin/dashboard?ok=producto_editado",
        status_code=302
    )


# =====================================
# CONTENT – GET (público, para el frontend)
# =====================================
from fastapi.responses import JSONResponse

@router.get("/content/data", include_in_schema=False)
def get_content_public(db: Session = Depends(get_db)):
    """Endpoint público que devuelve el contenido editable del landing."""
    import json

    def _json(val, fallback):
        if not val:
            return fallback
        try:
            return json.loads(val)
        except Exception:
            return fallback

    hero    = db.query(SiteContent).filter(SiteContent.section == "hero").first()
    about   = db.query(SiteContent).filter(SiteContent.section == "about").first()
    reviews = db.query(SiteContent).filter(SiteContent.section == "reviews").first()
    topbar  = db.query(SiteContent).filter(SiteContent.section == "topbar").first()
    social  = db.query(SiteContent).filter(SiteContent.section == "social").first()

    return JSONResponse({
        "hero": {
            "title":    hero.hero_title    if hero else None,
            "subtitle": hero.hero_subtitle if hero else None,
            "image":    hero.hero_image    if hero else None,
        },
        "about": {
            "text":  about.about_text  if about else None,
            "extra": about.about_extra if about else None,
            "image": about.about_image if about else None,
        },
        "reviews": {
            "images": _json(reviews.reviews_images if reviews else None, []),
        },
        "topbar": {
            "items":            _json(topbar.topbar_items if topbar else None, []),
            "whatsapp_number":  topbar.whatsapp_number  if topbar else None,
            "whatsapp_display": topbar.whatsapp_display if topbar else None,
            "contact_email":    topbar.contact_email    if topbar else None,
        },
        "social": _json(social.social_links if social else None, {}),
    })


# =====================================
# CONTENT – SAVE HERO
# =====================================
@router.post("/content/hero")
def save_hero(
    request: Request,
    hero_title: str = Form(...),
    hero_subtitle: str = Form(""),
    hero_image: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    row = db.query(SiteContent).filter(SiteContent.section == "hero").first()
    if not row:
        row = SiteContent(section="hero")
        db.add(row)

    row.hero_title = hero_title.strip()
    row.hero_subtitle = hero_subtitle.strip()

    if hero_image and hero_image.filename:
        url = _save_image(hero_image)
        if url:
            row.hero_image = url

    db.commit()
    return RedirectResponse(url="/admin/content?ok=hero", status_code=302)


# =====================================
# CONTENT – SAVE ABOUT
# =====================================
@router.post("/content/about")
def save_about(
    request: Request,
    about_text: str = Form(...),
    about_extra: str = Form(""),
    about_image: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    row = db.query(SiteContent).filter(SiteContent.section == "about").first()
    if not row:
        row = SiteContent(section="about")
        db.add(row)

    row.about_text = about_text.strip()
    row.about_extra = about_extra.strip()

    if about_image and about_image.filename:
        url = _save_image(about_image)
        if url:
            row.about_image = url

    db.commit()
    return RedirectResponse(url="/admin/content?ok=about", status_code=302)


# =====================================
# CONTENT – SAVE TOPBAR
# =====================================
@router.post("/content/topbar")
def save_topbar(
    request: Request,
    topbar_items: str = Form(...),   # JSON string del array
    whatsapp_number: str = Form(""),
    whatsapp_display: str = Form(""),
    contact_email: str = Form(""),
    db: Session = Depends(get_db),
):
    import json
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    row = db.query(SiteContent).filter(SiteContent.section == "topbar").first()
    if not row:
        row = SiteContent(section="topbar")
        db.add(row)

    # Validar que sea JSON válido
    try:
        parsed = json.loads(topbar_items)
        if not isinstance(parsed, list):
            parsed = []
        row.topbar_items = json.dumps([str(i).strip() for i in parsed if str(i).strip()])
    except Exception:
        row.topbar_items = json.dumps([])

    row.whatsapp_number = whatsapp_number.strip()
    row.whatsapp_display = whatsapp_display.strip()
    row.contact_email = contact_email.strip()
    db.commit()
    return RedirectResponse(url="/admin/content?ok=topbar", status_code=302)


# =====================================
# CONTENT – SAVE SOCIAL
# =====================================
@router.post("/content/social")
def save_social(
    request: Request,
    instagram: str = Form(""),
    tiktok: str = Form(""),
    facebook: str = Form(""),
    pinterest: str = Form(""),
    youtube: str = Form(""),
    twitter: str = Form(""),
    db: Session = Depends(get_db),
):
    import json
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    row = db.query(SiteContent).filter(SiteContent.section == "social").first()
    if not row:
        row = SiteContent(section="social")
        db.add(row)

    links = {
        "instagram": instagram.strip(),
        "tiktok": tiktok.strip(),
        "facebook": facebook.strip(),
        "pinterest": pinterest.strip(),
        "youtube": youtube.strip(),
        "twitter": twitter.strip(),
    }
    # Solo guardar las que tienen valor
    row.social_links = json.dumps({k: v for k, v in links.items() if v})
    db.commit()
    return RedirectResponse(url="/admin/content?ok=social", status_code=302)


# =====================================
# CONTENT – SAVE REVIEWS
# =====================================
@router.post("/content/reviews")
def save_reviews(
    request: Request,
    review_images: list[UploadFile] = File(default=[]),
    keep_images: list[str] = Form(default=[]),
    db: Session = Depends(get_db),
):
    import json
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    row = db.query(SiteContent).filter(SiteContent.section == "reviews").first()
    if not row:
        row = SiteContent(section="reviews")
        db.add(row)

    # Imágenes existentes que se quieren conservar
    existing = [u for u in keep_images if u.strip()]

    # Nuevas imágenes subidas
    new_urls = []
    for upload in review_images:
        if upload and upload.filename:
            url = _save_image(upload)
            if url:
                new_urls.append(url)

    all_images = existing + new_urls
    row.reviews_images = json.dumps(all_images)
    db.commit()
    return RedirectResponse(url="/admin/content?ok=reviews", status_code=302)


# =====================================
# CONTENT – PAGE
# =====================================
@router.get("/content")
def content_page(request: Request, db: Session = Depends(get_db)):
    import json

    def _json(val, fallback):
        if not val:
            return fallback
        try:
            return json.loads(val)
        except Exception:
            return fallback

    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    hero         = db.query(SiteContent).filter(SiteContent.section == "hero").first()
    about        = db.query(SiteContent).filter(SiteContent.section == "about").first()
    reviews_row  = db.query(SiteContent).filter(SiteContent.section == "reviews").first()
    topbar_row   = db.query(SiteContent).filter(SiteContent.section == "topbar").first()
    social_row   = db.query(SiteContent).filter(SiteContent.section == "social").first()

    return templates.TemplateResponse(
        request,
        "admin/content.html",
        {
            "request":        request,
            "hero":           hero,
            "about":          about,
            "reviews_images": _json(reviews_row.reviews_images if reviews_row else None, []),
            "topbar_items":   _json(topbar_row.topbar_items    if topbar_row  else None, []),
            "topbar":         topbar_row,
            "social":         _json(social_row.social_links    if social_row  else None, {}),
        },
    )

# =====================================
# NOTIFICATIONS PAGE
# =====================================
@router.get("/notifications")
def notifications_page(request: Request):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    return templates.TemplateResponse(
        request,
        "admin/notifications.html",
        {"request": request},
    )

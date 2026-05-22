from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import hashlib

from app.db.database import get_db
from app.db.models.analytics import PageView, ClickEvent
from app.db.models.sale import Sale
from app.db.models.product import Product
from app.db.models.notification import Notification
from app.services.notifications import notify

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ── Schemas de entrada ──────────────────────────────────────────
class PageViewIn(BaseModel):
    path: str = "/"
    referrer: Optional[str] = None

class ClickEventIn(BaseModel):
    element: str
    label: Optional[str] = None
    product_id: Optional[int] = None
    x_pct: Optional[int] = None
    y_pct: Optional[int] = None


class DiscountIn(BaseModel):
    product_id: int
    discount: int        # 0-100
    is_featured: bool = False


# ── Tracking endpoints (públicos, llamados desde la tienda) ──────
@router.post("/pageview")
def track_pageview(data: PageViewIn, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
    ua = request.headers.get("user-agent", "")[:200]

    view = PageView(
        path=data.path,
        referrer=data.referrer,
        user_agent=ua,
        ip_hash=ip_hash,
    )
    db.add(view)
    db.commit()
    return {"ok": True}


@router.post("/click")
def track_click(data: ClickEventIn, db: Session = Depends(get_db)):
    event = ClickEvent(
        element=data.element,
        label=data.label,
        product_id=data.product_id,
        x_pct=data.x_pct,
        y_pct=data.y_pct,
    )
    db.add(event)
    db.commit()
    return {"ok": True}


# ── Dashboard metrics endpoint (protegido por cookie) ────────────
@router.get("/metrics")
def get_metrics(request: Request, db: Session = Depends(get_db)):
    auth = request.cookies.get("admin_auth")
    if auth != "true":
        from fastapi import HTTPException
        raise HTTPException(status_code=401)

    now = datetime.utcnow()
    last_30 = now - timedelta(days=30)
    last_7  = now - timedelta(days=7)
    today   = now.date()

    # ── Totales ──────────────────────────────────────────────────
    total_views   = db.query(func.count(PageView.id)).scalar() or 0
    views_today   = db.query(func.count(PageView.id)).filter(
        func.date(PageView.created_at) == today
    ).scalar() or 0
    views_7d      = db.query(func.count(PageView.id)).filter(
        PageView.created_at >= last_7
    ).scalar() or 0

    unique_today  = db.query(func.count(func.distinct(PageView.ip_hash))).filter(
        func.date(PageView.created_at) == today
    ).scalar() or 0

    total_clicks  = db.query(func.count(ClickEvent.id)).scalar() or 0

    # ── Visitas por día (últimos 30 días) ─────────────────────────
    daily_raw = (
        db.query(
            func.date(PageView.created_at).label("day"),
            func.count(PageView.id).label("views"),
        )
        .filter(PageView.created_at >= last_30)
        .group_by(func.date(PageView.created_at))
        .order_by(func.date(PageView.created_at))
        .all()
    )
    daily_views = [{"day": str(r.day), "views": r.views} for r in daily_raw]

    # ── Top páginas ───────────────────────────────────────────────
    top_pages_raw = (
        db.query(PageView.path, func.count(PageView.id).label("cnt"))
        .group_by(PageView.path)
        .order_by(func.count(PageView.id).desc())
        .limit(8)
        .all()
    )
    top_pages = [{"path": r.path, "count": r.cnt} for r in top_pages_raw]

    # ── Top productos clickeados ──────────────────────────────────
    top_products_raw = (
        db.query(ClickEvent.label, func.count(ClickEvent.id).label("cnt"))
        .filter(ClickEvent.element == "product-card")
        .group_by(ClickEvent.label)
        .order_by(func.count(ClickEvent.id).desc())
        .limit(6)
        .all()
    )
    top_products = [{"name": r.label or "—", "clicks": r.cnt} for r in top_products_raw]

    # ── Clics por elemento ────────────────────────────────────────
    click_elements_raw = (
        db.query(ClickEvent.element, func.count(ClickEvent.id).label("cnt"))
        .group_by(ClickEvent.element)
        .order_by(func.count(ClickEvent.id).desc())
        .limit(8)
        .all()
    )
    click_elements = [{"element": r.element, "count": r.cnt} for r in click_elements_raw]

    # ── Heatmap: distribución de clics por zona (5x5 grid) ────────
    heatmap_raw = (
        db.query(ClickEvent.x_pct, ClickEvent.y_pct, func.count(ClickEvent.id).label("cnt"))
        .filter(ClickEvent.x_pct.isnot(None))
        .group_by(ClickEvent.x_pct, ClickEvent.y_pct)
        .all()
    )
    heatmap = [{"x": r.x_pct, "y": r.y_pct, "count": r.cnt} for r in heatmap_raw]

    # ── Referrers ─────────────────────────────────────────────────
    referrers_raw = (
        db.query(PageView.referrer, func.count(PageView.id).label("cnt"))
        .filter(PageView.referrer.isnot(None), PageView.referrer != "")
        .group_by(PageView.referrer)
        .order_by(func.count(PageView.id).desc())
        .limit(6)
        .all()
    )
    referrers = [{"source": r.referrer or "Directo", "count": r.cnt} for r in referrers_raw]

    return {
        "totals": {
            "total_views": total_views,
            "views_today": views_today,
            "views_7d": views_7d,
            "unique_today": unique_today,
            "total_clicks": total_clicks,
        },
        "daily_views": daily_views,
        "top_pages": top_pages,
        "top_products": top_products,
        "click_elements": click_elements,
        "heatmap": heatmap,
        "referrers": referrers,
    }


# ── Métricas de ventas ────────────────────────────────────────────
@router.get("/sales")
def get_sales_metrics(request: Request, db: Session = Depends(get_db)):
    auth = request.cookies.get("admin_auth")
    if auth != "true":
        from fastapi import HTTPException
        raise HTTPException(status_code=401)

    now = datetime.utcnow()
    last_30 = now - timedelta(days=30)

    # Totales
    total_revenue = db.query(func.sum(Sale.total)).scalar() or 0
    total_orders  = db.query(func.count(Sale.id)).scalar() or 0
    revenue_30d   = db.query(func.sum(Sale.total)).filter(Sale.created_at >= last_30).scalar() or 0

    # Ventas por día (últimos 30 días)
    daily_raw = (
        db.query(func.date(Sale.created_at).label("day"), func.sum(Sale.total).label("revenue"))
        .filter(Sale.created_at >= last_30)
        .group_by(func.date(Sale.created_at))
        .order_by(func.date(Sale.created_at))
        .all()
    )
    daily_sales = [{"day": str(r.day), "revenue": float(r.revenue)} for r in daily_raw]

    # Top productos vendidos
    top_sold_raw = (
        db.query(Sale.product_name, func.sum(Sale.quantity).label("units"), func.sum(Sale.total).label("revenue"))
        .group_by(Sale.product_name)
        .order_by(func.sum(Sale.total).desc())
        .limit(8)
        .all()
    )
    top_sold = [{"name": r.product_name, "units": int(r.units), "revenue": float(r.revenue)} for r in top_sold_raw]

    # Historial reciente (últimas 50 ventas)
    recent_raw = (
        db.query(Sale)
        .order_by(Sale.created_at.desc())
        .limit(50)
        .all()
    )
    recent = [
        {
            "id": s.id,
            "product": s.product_name,
            "price": s.product_price,
            "discount": s.discount,
            "final_price": s.final_price,
            "qty": s.quantity,
            "size": s.size,
            "color": s.color,
            "total": s.total,
            "date": s.created_at.strftime("%d/%m/%Y %H:%M") if s.created_at else "—",
        }
        for s in recent_raw
    ]

    return {
        "totals": {
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "revenue_30d": round(revenue_30d, 2),
        },
        "daily_sales": daily_sales,
        "top_sold": top_sold,
        "recent": recent,
    }


# ── Gestión de descuentos y destacados ───────────────────────────
@router.get("/products-list")
def get_products_for_dashboard(request: Request, db: Session = Depends(get_db)):
    auth = request.cookies.get("admin_auth")
    if auth != "true":
        from fastapi import HTTPException
        raise HTTPException(status_code=401)
    products = db.query(Product).order_by(Product.id).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "discount": p.discount or 0,
            "is_featured": p.is_featured or False,
            "stock": p.stock,
            "image": p.image,
        }
        for p in products
    ]


@router.post("/set-discount")
def set_discount(data: DiscountIn, request: Request, db: Session = Depends(get_db)):
    auth = request.cookies.get("admin_auth")
    if auth != "true":
        from fastapi import HTTPException
        raise HTTPException(status_code=401)
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    product.discount = max(0, min(100, data.discount))
    product.is_featured = data.is_featured
    db.commit()
    return {"ok": True, "discount": product.discount, "is_featured": product.is_featured}


# ── NOTIFICACIONES ────────────────────────────────────────────────

def _require_admin(request: Request):
    from fastapi import HTTPException
    if request.cookies.get("admin_auth") != "true":
        raise HTTPException(status_code=401)


@router.get("/notifications")
def get_notifications(request: Request, db: Session = Depends(get_db)):
    """Devuelve las últimas 50 notificaciones + genera las automáticas."""
    _require_admin(request)

    # ── Generar notificaciones automáticas ────────────────────────
    _generate_auto_notifications(db)

    notifications = (
        db.query(Notification)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )

    unread = sum(1 for n in notifications if not n.read)

    return {
        "unread": unread,
        "items": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "read": n.read,
                "ref_id": n.ref_id,
                "created_at": n.created_at.strftime("%d/%m/%Y %H:%M") if n.created_at else "—",
            }
            for n in notifications
        ],
    }


@router.post("/notifications/read-all")
def mark_all_read(request: Request, db: Session = Depends(get_db)):
    """Marca todas las notificaciones como leídas."""
    _require_admin(request)
    db.query(Notification).filter(Notification.read == False).update({"read": True})
    db.commit()
    return {"ok": True}


@router.post("/notifications/{notification_id}/read")
def mark_read(notification_id: int, request: Request, db: Session = Depends(get_db)):
    """Marca una notificación como leída."""
    _require_admin(request)
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if n:
        n.read = True
        db.commit()
    return {"ok": True}


@router.delete("/notifications/{notification_id}")
def delete_notification(notification_id: int, request: Request, db: Session = Depends(get_db)):
    """Elimina una notificación."""
    _require_admin(request)
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if not n:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    db.delete(n)
    db.commit()
    return {"ok": True}


def _generate_auto_notifications(db: Session) -> None:
    """Genera notificaciones automáticas basadas en el estado actual."""
    now = datetime.utcnow()

    # ── 1. Productos sin stock (sin notificación reciente) ─────────
    out_of_stock = db.query(Product).filter(Product.stock <= 0).all()
    for p in out_of_stock:
        # Evitar duplicados: no crear si ya existe una no leída del mismo producto
        exists = db.query(Notification).filter(
            Notification.type == "out_of_stock",
            Notification.ref_id == p.id,
            Notification.read == False,
        ).first()
        if not exists:
            notify(db, "out_of_stock", "Producto agotado",
                   f"{p.name} no tiene stock disponible", ref_id=p.id)

    # ── 2. Stock bajo (≤ 3 unidades) ──────────────────────────────
    low_stock = db.query(Product).filter(Product.stock > 0, Product.stock <= 3).all()
    for p in low_stock:
        exists = db.query(Notification).filter(
            Notification.type == "low_stock",
            Notification.ref_id == p.id,
            Notification.read == False,
        ).first()
        if not exists:
            notify(db, "low_stock", "Stock bajo",
                   f"{p.name} — quedan {p.stock} unidades", ref_id=p.id)

    # ── 3. Productos sin actividad en 30 días ─────────────────────
    thirty_days_ago = now - timedelta(days=30)
    all_products = db.query(Product).filter(Product.stock > 0).all()
    for p in all_products:
        last_sale = (
            db.query(Sale)
            .filter(Sale.product_id == p.id)
            .order_by(Sale.created_at.desc())
            .first()
        )
        # Sin ventas en 30 días y el producto tiene más de 30 días de antigüedad
        if last_sale is None or last_sale.created_at.replace(tzinfo=None) < thirty_days_ago:
            exists = db.query(Notification).filter(
                Notification.type == "no_activity",
                Notification.ref_id == p.id,
                Notification.read == False,
            ).first()
            if not exists:
                notify(db, "no_activity", "Sin actividad",
                       f"{p.name} no registra ventas en los últimos 30 días", ref_id=p.id)

    # ── 4. Hito de visitas (cada 100 visitas) ─────────────────────
    total_views = db.query(func.count(PageView.id)).scalar() or 0
    if total_views > 0 and total_views % 100 == 0:
        exists = db.query(Notification).filter(
            Notification.type == "visit_milestone",
            Notification.message.contains(str(total_views)),
        ).first()
        if not exists:
            notify(db, "visit_milestone", "¡Hito de visitas!",
                   f"La tienda alcanzó {total_views} visitas totales")

    db.commit()

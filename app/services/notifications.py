"""Helpers para crear notificaciones del panel admin."""
from sqlalchemy.orm import Session
from app.db.models.notification import Notification


def notify(db: Session, type: str, title: str, message: str, ref_id: int | None = None) -> None:
    """Crea una notificación. No lanza excepciones para no interrumpir el flujo principal."""
    try:
        n = Notification(type=type, title=title, message=message, ref_id=ref_id)
        db.add(n)
        # No hacemos commit aquí — el caller lo hace junto con el resto de la transacción
    except Exception:
        pass


def notify_sale(db: Session, product_name: str, qty: int, total: float, product_id: int | None = None) -> None:
    notify(
        db, "sale",
        "Nueva venta",
        f"{product_name} × {qty} — €{total:.2f}",
        ref_id=product_id,
    )


def notify_low_stock(db: Session, product_name: str, stock: int, product_id: int) -> None:
    notify(
        db, "low_stock",
        "Stock bajo",
        f"{product_name} — quedan {stock} unidades",
        ref_id=product_id,
    )


def notify_out_of_stock(db: Session, product_name: str, product_id: int) -> None:
    notify(
        db, "out_of_stock",
        "Producto agotado",
        f"{product_name} se quedó sin stock",
        ref_id=product_id,
    )

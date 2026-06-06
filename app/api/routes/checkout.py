from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import json

from app.services.sumup import SumupError, create_checkout
from app.services.notifications import notify_sale, notify_low_stock, notify_out_of_stock
from app.db.database import get_db
from app.db.models.sale import Sale
from app.db.models.product import Product

router = APIRouter(prefix="/checkout", tags=["Checkout"])


def _decrement_stock(product: Product, size: str | None, qty: int) -> None:
    """Descuenta el stock del producto. Actualiza size_stock y stock total."""
    # ── Stock por talle ───────────────────────────────────────────
    if product.size_stock and size:
        size_key = size.strip().upper()
        stock_map: dict = {}

        # Parsear size_stock (formato "S:4, M:2" o JSON)
        raw = product.size_stock.strip()
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                stock_map = {k.strip().upper(): max(0, int(v)) for k, v in parsed.items()}
        except (json.JSONDecodeError, ValueError):
            for part in raw.split(','):
                if ':' in part:
                    k, v = part.split(':', 1)
                    stock_map[k.strip().upper()] = max(0, int(v.strip()) if v.strip().isdigit() else 0)

        if size_key in stock_map:
            stock_map[size_key] = max(0, stock_map[size_key] - qty)
            # Guardar de vuelta en formato "S:4, M:2"
            product.size_stock = ', '.join(f"{k}:{v}" for k, v in stock_map.items())

        # Recalcular stock total como suma de todos los talles
        product.stock = max(0, sum(stock_map.values()))

    else:
        # Sin talles — descontar del stock general
        product.stock = max(0, product.stock - qty)


@router.post("/")
async def process_checkout(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        cart_items = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    if not isinstance(cart_items, list) or not cart_items:
        raise HTTPException(status_code=400, detail="Carrito vacío")

    total = 0.0
    prepared_items = []
    for item in cart_items:
        pid = item.get("id")
        is_shipping = item.get("is_shipping", False)
        product = db.query(Product).filter(Product.id == pid).first() if pid and not is_shipping else None
        discount = product.discount if product else int(item.get("discount", 0) or 0)
        discount = max(0, min(100, discount))
        base_price = float(item.get("price", 0))
        final_price = round(base_price * (1 - discount / 100), 2)
        qty = int(item.get("qty", item.get("quantity", 1)))
        total += final_price * qty
        prepared_items.append((item, pid, product, discount, base_price, final_price, qty, is_shipping))

    total = round(total, 2)

    try:
        checkout_data = await create_checkout(
            total=total,
            description="Compra en Heydemin"
        )

        payment_url = checkout_data.get("hosted_checkout_url")
        if not payment_url:
            raise HTTPException(
                status_code=502,
                detail="No se pudo obtener la URL de pago de SumUp"
            )

            # Registrar venta, descontar stock y crear notificaciones
        for item, pid, product, discount, base_price, final_price, qty, is_shipping in prepared_items:
            # El ítem de envío no se registra como venta ni descuenta stock
            if is_shipping:
                continue
            sale = Sale(
                product_id=pid,
                product_name=item.get("name", "Producto"),
                product_price=base_price,
                discount=discount,
                final_price=final_price,
                quantity=qty,
                size=item.get("size"),
                color=item.get("color"),
                total=round(final_price * qty, 2),
            )
            db.add(sale)

            # Notificación de venta
            notify_sale(db, item.get("name", "Producto"), qty,
                        round(final_price * qty, 2), pid)

            # Descontar stock y notificar si baja
            if product:
                _decrement_stock(product, item.get("size"), qty)
                if product.stock == 0:
                    notify_out_of_stock(db, product.name, product.id)
                elif product.stock <= 3:
                    notify_low_stock(db, product.name, product.stock, product.id)

        db.commit()

        return {"payment_url": payment_url}

    except SumupError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")


@router.get("/thank-you", response_class=HTMLResponse)
async def thank_you():
    """Página de confirmación tras el pago con SumUp."""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>¡Gracias por tu compra! · Heydemin</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', sans-serif;
      background: #f5f2ed;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }
    .card {
      background: #fff;
      border-radius: 16px;
      padding: 48px 40px;
      max-width: 440px;
      width: 100%;
      text-align: center;
      box-shadow: 0 12px 40px rgba(0,0,0,0.08);
    }
    .icon {
      width: 64px; height: 64px;
      background: #ecfdf5;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      margin: 0 auto 24px;
      font-size: 1.8rem;
      color: #059669;
    }
    h1 {
      font-family: 'Playfair Display', serif;
      font-size: 1.8rem;
      color: #111;
      margin-bottom: 12px;
    }
    p {
      color: #6b7280;
      font-size: 0.92rem;
      line-height: 1.6;
      margin-bottom: 28px;
    }
    a {
      display: inline-block;
      background: #111;
      color: #fff;
      text-decoration: none;
      padding: 12px 28px;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      letter-spacing: 0.06em;
      transition: background 0.2s;
    }
    a:hover { background: #333; }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">✓</div>
    <h1>¡Gracias por tu compra!</h1>
    <p>Tu pedido fue procesado correctamente.<br>Recibirás un email de confirmación en breve.</p>
    <a href="/">Volver a la tienda</a>
  </div>
</body>
</html>
""", status_code=200)

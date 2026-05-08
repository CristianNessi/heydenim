from fastapi import APIRouter, HTTPException, Request
from typing import Any

from app.services.sumup import SumupError, create_checkout

router = APIRouter(prefix="/checkout", tags=["Checkout"])

@router.post("/")
async def process_checkout(request: Request) -> dict[str, str]:
    try:
        cart_items = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    if not isinstance(cart_items, list) or not cart_items:
        raise HTTPException(status_code=400, detail="Carrito vacio")

    total = sum(
        item.get("qty", item.get("quantity", 1)) * item.get("price", 0)
        for item in cart_items
    )

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

        return {"payment_url": payment_url}

    except SumupError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

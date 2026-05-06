from fastapi import APIRouter, HTTPException
from typing import Any

from app.db.fake_db import CART

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.get("/")
def get_cart() -> list[dict[str, Any]]:
    return CART

@router.post("/")
def add_to_cart(item: dict[str, Any]) -> dict[str, str]:
    if "product_id" not in item:
        raise HTTPException(status_code=400, detail="product_id requerido")

    CART.append(item)
    return {"message": "Producto agregado"}

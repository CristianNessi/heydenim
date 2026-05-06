from fastapi import APIRouter

from app.db.products import get_all_products

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/")
def get_products():
    return get_all_products()

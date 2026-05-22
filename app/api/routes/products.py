from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.product import Product
from app.schemas.schemas import ProductOut


router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=list[ProductOut])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()
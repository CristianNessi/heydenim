from pydantic import BaseModel, ConfigDict
from typing import Optional


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    price: float
    image: Optional[str] = None
    stock: int = 0
    colors: Optional[str] = None
    sizes: Optional[str] = None
    size_stock: Optional[str] = None
    images: Optional[str] = None
    discount: int = 0
    is_featured: bool = False


class CartItem(BaseModel):
    product_id: int
    quantity: int = 1


class CheckoutResponse(BaseModel):
    payment_url: str

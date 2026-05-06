from pydantic import BaseModel, Field

class Product(BaseModel):
    id: int
    name: str
    price: float

class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)

class CheckoutResponse(BaseModel):
    payment_url: str

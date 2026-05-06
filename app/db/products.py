PRODUCTS = [
    {
        "id": 1,
        "name": "Vestido Summer",
        "price": 49.99
    }
]

def get_all_products():
    return PRODUCTS

def get_product(product_id: int):
    return next((p for p in PRODUCTS if p["id"] == product_id), None)

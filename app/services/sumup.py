import httpx
from app.core.config import settings

class SumupError(Exception):
    pass

async def create_checkout(total: float, description: str):
    """
    Crea un checkout de SumUp para pagos como invitado.
    """
    if not settings.SUMUP_API_KEY or not settings.SUMUP_MERCHANT_CODE:
        raise SumupError("Configuración de SumUp incompleta")

    amount = float(total)
    if amount <= 0:
        raise SumupError("El total del carrito debe ser mayor que 0")

    url = f"{settings.SUMUP_API_URL}/checkouts"

    headers = {
        "Authorization": f"Bearer {settings.SUMUP_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "checkout_reference": f"heydemin-{int(__import__('time').time())}",
        "amount": total,
        "currency": "EUR",
        "merchant_code": settings.SUMUP_MERCHANT_CODE,
        "description": description,
        "pay_to_email": settings.SUMUP_PAY_TO_EMAIL,
        "redirect_url": settings.SUMUP_REDIRECT_URL,
        "return_url": settings.SUMUP_RETURN_URL,
        "customer_id": None  # Para pagos como invitado
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)

            if response.status_code == 201:
                return response.json()
            else:
                raise SumupError(f"Error de SumUp API: {response.status_code} - {response.text}")

        except httpx.TimeoutException:
            raise SumupError("Timeout conectando con SumUp")
        except httpx.RequestError as e:
            raise SumupError(f"Error de conexión: {str(e)}")
    

import time

import httpx

from app.core.config import settings


class SumupError(Exception):
    pass


async def create_checkout(total: float, description: str):
    """
    Crea un checkout de SumUp con Hosted Checkout habilitado.
    Devuelve el objeto checkout que incluye hosted_checkout_url.
    """
    if not settings.SUMUP_API_KEY or not settings.SUMUP_MERCHANT_CODE:
        raise SumupError("Configuración de SumUp incompleta")

    url = f"{settings.SUMUP_API_URL}/checkouts"

    headers = {
        "Authorization": f"Bearer {settings.SUMUP_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "checkout_reference": f"heydemin-{int(time.time())}",
        "amount": total,
        "currency": "EUR",
        "merchant_code": settings.SUMUP_MERCHANT_CODE,
        "description": description,
        # Activar Hosted Checkout para recibir hosted_checkout_url en la respuesta
        "hosted_checkout": {
            "enabled": True,
        },
    }

    # redirect_url solo en producción (requiere dominio real con HTTPS)
    if settings.SUMUP_REDIRECT_URL and settings.SUMUP_REDIRECT_URL.startswith("https://"):
        payload["redirect_url"] = settings.SUMUP_REDIRECT_URL

    # pay_to_email es opcional
    if settings.SUMUP_PAY_TO_EMAIL:
        payload["pay_to_email"] = settings.SUMUP_PAY_TO_EMAIL

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)

            if response.status_code == 201:
                return response.json()
            else:
                raise SumupError(
                    f"Error de SumUp API: {response.status_code} - {response.text}"
                )

        except httpx.TimeoutException:
            raise SumupError("Timeout conectando con SumUp")
        except httpx.RequestError as e:
            raise SumupError(f"Error de conexión: {str(e)}")

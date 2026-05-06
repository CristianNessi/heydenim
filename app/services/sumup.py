import uuid
import httpx
from typing import Any

from app.core.config import settings

class SumupError(Exception):
    pass

# Cliente global reutilizable
_client: httpx.AsyncClient | None = None

async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        timeout = httpx.Timeout(10.0, connect=5.0)
        _client = httpx.AsyncClient(timeout=timeout)
    return _client

async def close_client() -> None:
    global _client
    if _client:
        await _client.aclose()
        _client = None

async def create_checkout(total: float, description: str) -> dict[str, Any]:
    if not settings.SUMUP_API_KEY or not settings.SUMUP_MERCHANT_CODE:
        raise SumupError(
            "SumUp no está configurado. "
            "Agrega SUMUP_API_KEY y SUMUP_MERCHANT_CODE en .env."
        )

    client = await get_client()
    
    url = f"{settings.SUMUP_API_URL}/checkouts"
    headers = {
        "Authorization": f"Bearer {settings.SUMUP_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "checkout_reference": f"order-heydemin-{uuid.uuid4().hex}",
        "amount": total,
        "currency": "EUR",
        "merchant_code": settings.SUMUP_MERCHANT_CODE,
        "description": description
    }

    response = await client.post(url, json=payload, headers=headers)

    if response.status_code != 201:
        try:
            error_data = response.json()
        except ValueError:
            error_data = response.text
        raise SumupError(f"SumUp error ({response.status_code}): {error_data}")

    data = response.json()
    hosted_url = data.get("hosted_checkout_url")

    if not hosted_url:
        raise SumupError("SumUp no devolvio hosted_checkout_url")

    return data

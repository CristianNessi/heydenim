from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from app.api.routes import products, cart, checkout
from app.core.config import settings
from app.services import sumup

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not settings.SUMUP_API_KEY or not settings.SUMUP_MERCHANT_CODE:
        print(
            "WARNING: Las credenciales de SumUp no están configuradas. "
            "El checkout no estará disponible hasta que se configuren."
        )
    yield
    # Shutdown
    await sumup.close_client()

app = FastAPI(title="Heydemin", lifespan=lifespan)
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)

@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

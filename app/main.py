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
    try:
        settings.validate()
    except RuntimeError as e:
        print(f"ERROR: {e}")
        raise
    yield

app = FastAPI(title="Heydemin", lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")

app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)

@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

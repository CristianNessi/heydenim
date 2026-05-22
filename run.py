import uvicorn
import os

if __name__ == "__main__":
    is_prod = os.getenv("ENVIRONMENT", "development") == "production"

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0" if is_prod else "127.0.0.1",
        port=int(os.getenv("PORT", 8000)),
        reload=not is_prod,
        workers=2 if is_prod else 1,
    )

import os
from dotenv import load_dotenv

# 🔥 FIX CRÍTICO WINDOWS + UTF-8
load_dotenv(encoding="utf-8")


class Settings:

    # =========================
    # SUMUP
    # =========================

    SUMUP_API_URL = "https://api.sumup.com/v0.1"

    SUMUP_API_KEY = os.getenv("SUMUP_API_KEY")

    SUMUP_MERCHANT_CODE = os.getenv("SUMUP_MERCHANT_CODE")

    SUMUP_PAY_TO_EMAIL = os.getenv("SUMUP_PAY_TO_EMAIL")

    # redirect_url: a donde SumUp redirige al usuario tras completar el pago
    SUMUP_REDIRECT_URL = os.getenv(
        "SUMUP_REDIRECT_URL",
        "https://heydenim.es/checkout/thank-you"
    )

    # =========================
    # ADMIN AUTH
    # =========================

    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@heydenim.es")

    ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

    SESSION_SECRET = os.getenv("SESSION_SECRET", "changeme")

    # =========================
    # DATABASE
    # =========================

    DATABASE_URL = os.getenv("DATABASE_URL")

    # =========================
    # VALIDATION
    # =========================

    def validate(self):

        required = ["DATABASE_URL"]

        missing = [
            field
            for field in required
            if not getattr(self, field)
        ]

        if missing:
            raise RuntimeError(
                f"Missing env variables: {', '.join(missing)}"
            )


settings = Settings()
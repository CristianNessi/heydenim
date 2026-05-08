import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SUMUP_API_URL = "https://api.sumup.com/v0.1"
    SUMUP_API_KEY = os.getenv("SUMUP_API_KEY")
    SUMUP_MERCHANT_CODE = os.getenv("SUMUP_MERCHANT_CODE")
    SUMUP_PAY_TO_EMAIL = os.getenv("SUMUP_PAY_TO_EMAIL")
    SUMUP_REDIRECT_URL = os.getenv("SUMUP_REDIRECT_URL", "https://heydemin.com/thank-you")
    SUMUP_RETURN_URL = os.getenv("SUMUP_RETURN_URL", "https://heydemin.com/")

    def validate(self):
        required = ["SUMUP_API_KEY", "SUMUP_MERCHANT_CODE"]
        missing = [field for field in required if not getattr(self, field)]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

settings = Settings()
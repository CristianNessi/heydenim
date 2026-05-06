from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUMUP_API_URL: str = "https://api.sumup.com/v0.1"
    SUMUP_API_KEY: str = ""
    SUMUP_MERCHANT_CODE: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

    def validate(self) -> None:
        missing = []
        if not self.SUMUP_API_KEY:
            missing.append("SUMUP_API_KEY")
        if not self.SUMUP_MERCHANT_CODE:
            missing.append("SUMUP_MERCHANT_CODE")

        if missing:
            raise RuntimeError(
                f"Faltan variables de entorno de SumUp: {', '.join(missing)}"
            )

settings = Settings()

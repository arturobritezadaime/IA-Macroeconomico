import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Clase de configuración centralizada del proyecto."""
    FRED_API_KEY: str | None = os.getenv("FRED_API_KEY")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")

import sys
import logging
import pandas as pd
import google.generativeai as genai
from fredapi import Fred

from config import Config
from utils import save_analysis_to_txt

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def configure_fred() -> Fred:
    """Configura y retorna cliente de FRED."""
    if not Config.FRED_API_KEY:
        logging.error("FRED_API_KEY no está configurada en Config.")
        sys.exit(1)
    return Fred(api_key=Config.FRED_API_KEY)

def configure_gemini() -> bool:
    """Configura Gemini si la API_KEY está disponible."""
    if not Config.GEMINI_API_KEY:
        logging.warning("Gemini no configurado.")
        return False
    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        return True
    except Exception as e:
        logging.warning(f"No se pudo configurar Gemini: {e}")
        return False

def fetch_monthly(fred: Fred, series_id: str) -> pd.Series:
    """Descarga una serie de FRED y la resamplea a fin de mes."""
    try:
        series = fred.get_series(series_id)
        if series is None or series.empty:
            logging.warning(f"Serie {series_id} vacía o no encontrada.")
            return pd.Series(dtype="float64")
        series.index = pd.to_datetime(series.index)
        return series.resample("ME").last().ffill().rename(series_id)
    except Exception as e:
        logging.error(f"Error al descargar {series_id}: {e}")
        return pd.Series(dtype="float64")

def build_prompt(yearly_averages: dict) -> tuple[str, str]:
    """Construye el prompt y el string de métricas basado en promedios anuales."""
    indicators = {
        "inflacion": "Inflación",
        "tasa_fed": "Tasa Fed",
        "retorno_nasdaq": "Retorno Nasdaq (12 meses)",
        "vix": "VIX (Índice de Volatilidad)",
        "sentimiento_consumidor": "Sentimiento del Consumidor (UMich)",
    }

    metrics_str = "=== DATOS PROMEDIO ANUALES (últimos 5 años) ===\n"
    for year, data in yearly_averages.items():
        metrics_str += f"\n--- {year} ---\n"
        for key, name in indicators.items():
            value = data.get(key)
            if value is not None:
                suffix = "%" if key not in ["vix", "sentimiento_consumidor"] else ""
                metrics_str += f"{name}: {value:.2f}{suffix}\n"

    prompt = f"""
Actúa como un economista senior en mercados financieros y genera un análisis basado SÓLO en los datos promedio anuales proporcionados.

**Análisis de Tendencias Anuales:**
Analiza la evolución de los indicadores macroeconómicos y su relación.

**Contexto y Futuro:**
Basándote en las tendencias observadas y el contexto actual, proporciona una perspectiva sobre la dirección probable del mercado y riesgos principales.

**Pronóstico:**
* **Pronóstico {pd.Timestamp.now().year}:** Situación actual.
* **Pronóstico {pd.Timestamp.now().year + 1}:** Perspectiva de mediano plazo.

---
Datos de la FED y Mercados:
""" + metrics_str

    return prompt, metrics_str

def main():
    fred = configure_fred()
    gemini_available = configure_gemini()

    # Series necesarias (FRED IDs → nombre amigable)
    series_ids = {
        "CPIAUCSL": "inflacion",
        "FEDFUNDS": "tasa_fed",
        "NASDAQCOM": "retorno_nasdaq",
        "VIXCLS": "vix",
        "UMCSENT": "sentimiento_consumidor",
    }

    # Descargar todas las series
    data = {name: fetch_monthly(fred, series_id) for series_id, name in series_ids.items()}

    # Loguear tamaños para debug
    for k, v in data.items():
        logging.info(f"Serie {k}: {len(v)} puntos desde {v.index.min().date() if not v.empty else 'N/A'}")

    if data["inflacion"].empty or data["tasa_fed"].empty or data["retorno_nasdaq"].empty:
        logging.error("Faltan series esenciales (CPI, FEDFUNDS o NASDAQ).")
        sys.exit(1)

    # Transformaciones
    infl_yoy = data["inflacion"].pct_change(12) * 100
    nas_ret_12m = data["retorno_nasdaq"].pct_change(12) * 100

    df = pd.concat([
        infl_yoy.rename("inflacion"),
        data["tasa_fed"].rename("tasa_fed"),
        nas_ret_12m.rename("retorno_nasdaq"),
        data["vix"].rename("vix"),
        data["sentimiento_consumidor"].rename("sentimiento_consumidor"),
    ], axis=1).dropna()


    if df.empty:
        logging.error("El DataFrame quedó vacío tras limpieza.")
        sys.exit(1)

    logging.info(f"Datos mensuales disponibles: {len(df)} filas. Rango {df.index.min().date()} - {df.index.max().date()}")

    # Promedios anuales últimos 5 años
    end_year = pd.Timestamp.now().year
    yearly_averages = {
        year: df[df.index.year == year].mean().to_dict()
        for year in range(end_year - 4, end_year + 1)
        if not df[df.index.year == year].empty
    }

    # Construir prompt
    prompt, metrics_str = build_prompt(yearly_averages)

    # Ejecutar Gemini
    response_text = "Gemini no configurado."
    if gemini_available:
        try:
            response = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt)
            response_text = getattr(response, "text", "Respuesta vacía de Gemini.")
        except Exception as e:
            logging.warning(f"Llamada a Gemini falló: {e}")
            response_text = f"Error llamando a Gemini: {e}"

    # Guardar análisis
    path = save_analysis_to_txt(prompt, metrics_str, response_text)
    logging.info(f"Análisis guardado en: {path}")

if __name__ == "__main__":
    main()

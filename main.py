
import sys
import logging
import pandas as pd
import google.generativeai as genai

from fredapi import Fred

from config import Config
from utils import save_analysis_to_txt


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def fetch_monthly(fred: Fred, series_id: str) -> pd.Series:
    """Descarga una serie y la resamplea a fin de mes (último valor del mes)."""
    s = fred.get_series(series_id)
    if s is None or s.empty:
        logging.warning(f"Serie {series_id} vacía o no encontrada.")
        return pd.Series(dtype="float64")
    s.index = pd.to_datetime(s.index)
    s = s.resample("ME").last().ffill()
    s.name = series_id
    return s


def main():
    # --- Config APIs ---
    if not getattr(Config, "FRED_API_KEY", None):
        logging.error("FRED_API_KEY no está configurada en config.Config.")
        sys.exit(1)

    fred = Fred(api_key=Config.FRED_API_KEY)

    gemini_available = False
    if getattr(Config, "GEMINI_API_KEY", None):
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            gemini_available = True
        except Exception as e:
            logging.warning(f"No se pudo configurar Gemini: {e}")

    # --- Descargar series y resamplear a mensual (fin de mes) ---
    cpi = fetch_monthly(fred, "CPIAUCSL")
    fedfunds = fetch_monthly(fred, "FEDFUNDS")
    nasdaq = fetch_monthly(fred, "NASDAQCOM")
    vix = fetch_monthly(fred, "VIXCLS")
    umich = fetch_monthly(fred, "UMCSENT")

    # Chequeo mínimo de datos
    if cpi.empty or fedfunds.empty or nasdaq.empty:
        logging.error("Faltan series esenciales (CPI, FEDFUNDS o NASDAQ). Revisa las series FRED o la conexión.")
        sys.exit(1)

    # --- Transformaciones y concatenación ---
    infl_yoy = cpi.pct_change(periods=12, fill_method=None) * 100
    nas_ret_12m = nasdaq.pct_change(periods=12, fill_method=None) * 100

    df = pd.concat(
        [
            infl_yoy.rename("inflacion"),
            fedfunds.rename("tasa_fed"),
            nas_ret_12m.rename("retorno_nasdaq"),
            vix.rename("vix"),
            umich.rename("sentimiento_consumidor"),
        ],
        axis=1,
    )

    df = df.dropna()
    if df.empty:
        logging.error("Después de combinar y hacer dropna() el DataFrame quedó vacío.")
        sys.exit(1)

    logging.info(f"Datos mensuales disponibles: {len(df)} filas. Rango {df.index.min().date()} - {df.index.max().date()}")

    # --- Cálculo de promedios anuales de los últimos 5 años ---
    end_year = pd.Timestamp.now().year
    start_year = end_year - 4 # Últimos 5 años (ej. 2021, 2022, 2023, 2024, 2025)

    yearly_averages = {}
    for year in range(start_year, end_year + 1):
        year_data = df[df.index.year == year]
        if not year_data.empty:
            yearly_averages[year] = year_data.mean().to_dict()

    # --- Preparar prompt para Gemini ---
    metrics_str = "=== DATOS PROMEDIO ANUALES (últimos 5 años) ===\n"
    indicators = {
        "inflacion": "Inflación",
        "tasa_fed": "Tasa Fed",
        "retorno_nasdaq": "Retorno Nasdaq (12 meses)",
        "vix": "VIX (Índice de Volatilidad)",
        "sentimiento_consumidor": "Sentimiento del Consumidor (UMich)",
    }

    for year, data in yearly_averages.items():
        metrics_str += f"\n--- {year} ---\n"
        for key, name in indicators.items():
            value = data.get(key)
            if value is not None:
                # Formato especial para VIX y Sentimiento (sin %)
                if key in ["vix", "sentimiento_consumidor"]:
                    metrics_str += f"{name}: {value:.2f}\n"
                else:
                    metrics_str += f"{name}: {value:.2f}%\n"

    prompt_base = """
Actúa como un economista senior en mercados financieros y genera un análisis basado SÓLO en los datos promedio anuales proporcionados.

**Análisis de Tendencias Anuales:**
Analiza la evolución de los indicadores macroeconómicos y su relación. Describe cómo la inflación y las tasas de la Fed han interactuado con el Nasdaq y otros indicadores.

**Contexto y Futuro:**
Basándote en las tendencias observadas y el contexto actual (sin un modelo de predicción), proporciona una perspectiva sobre la dirección probable del mercado y los riesgos principales para los próximos dos años.

**Pronóstico:**
* **Pronóstico 2025 (basado en datos disponibles):** Resumen de la situación.
* **Pronóstico 2026:** Perspectiva de mediano plazo.

---

Datos de la FED y Mercados:
"""

    prompt = prompt_base + metrics_str

    # --- Llamada a Gemini (si está disponible) ---
    response_text = ""
    if gemini_available:
        try:
            model_g = genai.GenerativeModel("gemini-2.5-flash")
            response = model_g.generate_content(prompt)
            if hasattr(response, "text"):
                response_text = response.text
            else:
                response_text = "Respuesta de Gemini no contiene texto."
        except Exception as e:
            logging.warning(f"Llamada a Gemini falló: {e}")
            response_text = f"Error llamando a Gemini: {e}"
    else:
        response_text = "Gemini no configurado."

    # --- Guardar análisis ---
    try:
        path = save_analysis_to_txt(prompt, "", response_text)
        logging.info(f"Análisis guardado en: {path}")
    except TypeError:
        fallback_path = "analysis_output_promedios.txt"
        with open(fallback_path, "w", encoding="utf-8") as f:
            f.write("PROMPT:\n")
            f.write(prompt + "\n\n")
            f.write("RESPONSE:\n")
            f.write(response_text + "\n")
        logging.info(f"save_analysis_to_txt falló por firma; guardado fallback en: {fallback_path}")

if __name__ == "__main__":
    main()
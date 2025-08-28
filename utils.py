import os
from datetime import datetime

def ensure_dir(path: str) -> None:
    """Crea un directorio si no existe."""
    os.makedirs(path, exist_ok=True)

def save_analysis_to_txt(prompt: str, metrics: str, response: str, prefix: str = "analisis_macro") -> str:
    """
    Guarda análisis con prompt, métricas y respuesta en un archivo .txt.
    
    Args:
        prompt (str): Prompt enviado al modelo.
        metrics (str): Datos o métricas asociadas.
        response (str): Respuesta del modelo.
        prefix (str, optional): Prefijo para el nombre del archivo. Default "analisis_macro".
    
    Returns:
        str: Ruta completa del archivo generado.
    """
    fecha_hora_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"{prefix}_{fecha_hora_str}.txt"

    ensure_dir("outputs")
    path = os.path.join("outputs", nombre)

    with open(path, "w", encoding="utf-8") as f:
        f.write("=== PROMPT COMPLETO ===\n")
        f.write(prompt.strip() + "\n\n")
        f.write("=== MÉTRICAS / DATOS ===\n")
        f.write(metrics.strip() + "\n\n")
        f.write("=== RESPUESTA GEMINI ===\n")
        f.write(response.strip() + "\n")

    return path

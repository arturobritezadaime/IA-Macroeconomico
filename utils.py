import os
from datetime import datetime

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def save_analysis_to_txt(prompt: str, metrics: str, response: str, prefix: str = "analisis_macro"):
    """
    Guarda análisis con prompt completo, métricas y respuesta en un archivo .txt.
    """
    now = datetime.now()
    fecha_hora_str = now.strftime("%d-%m-%Y-%H_%Mhs")
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

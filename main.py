import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from fredapi import Fred
import google.generativeai as genai

from config import Config
from utils import save_analysis_to_txt

# Configuración APIs
fred = Fred(api_key=Config.FRED_API_KEY)
genai.configure(api_key=Config.GEMINI_API_KEY)

# Descargar series FRED
cpi = fred.get_series("CPIAUCSL")     # IPC
fedfunds = fred.get_series("FEDFUNDS")  # Tasa Fed
nasdaq = fred.get_series("NASDAQCOM")   # Nasdaq

# Transformar series
infl_yoy = cpi.pct_change(12) * 100
nas_ret_1m = nasdaq.pct_change(1) * 100

df = pd.concat([infl_yoy.rename("infl_yoy"),
                fedfunds.rename("fedfunds"),
                nas_ret_1m.rename("nas_ret_1m")], axis=1).dropna()

# Entrenamiento regresión lineal
train = df.iloc[:-6]
test = df.iloc[-6:]

X_train, y_train = train[["infl_yoy", "fedfunds"]], train["nas_ret_1m"]
X_test, y_test = test[["infl_yoy", "fedfunds"]], test["nas_ret_1m"]

model = LinearRegression().fit(X_train, y_train)
r2 = model.score(X_train, y_train)
preds = model.predict(X_test)

# Graficar resultados recientes
plt.figure(figsize=(8,4))
plt.plot(test.index, y_test, label="Nasdaq Retorno 1m (real)")
plt.plot(test.index, preds, "--", label="Predicción (lineal)")
plt.title("Retorno mensual Nasdaq vs predicción")
plt.legend()
plt.tight_layout()
plt.show()

# Métricas y datos clave
last_row = df.iloc[-1]
metrics = (
    f"Inflación interanual última lectura: {last_row['infl_yoy']:.2f}%\n"
    f"Tasa Fed última lectura: {last_row['fedfunds']:.2f}%\n"
    f"Retorno Nasdaq último mes: {last_row['nas_ret_1m']:.2f}%\n"
    f"R² del modelo: {r2:.2f}\n"
)

# Prompt optimizado
prompt = f"""
Actúa como economista senior en mercados. 
Analiza el impacto de la inflación actual en el sector tecnológico (usando Nasdaq como proxy).
Evalúa cómo el aumento de costos y la política de tasas de interés afectan la inversión.
Usa los datos recientes de FRED y del modelo, cita cifras específicas.

Estructura el informe en:
1) Diagnóstico
2) Mecanismos de transmisión (costos, valuaciones, capex)
3) Riesgos de segundo orden
4) Pronóstico a 6 y 12 meses con rangos cuantitativos

Sé conciso (200-300 palabras).
"""

# Ejecutar Gemini
model_g = genai.GenerativeModel("gemini-2.5-flash")
response = model_g.generate_content(prompt).text

# Guardar en TXT
path = save_analysis_to_txt(prompt, metrics, response)
print(f"Análisis guardado en: {path}")

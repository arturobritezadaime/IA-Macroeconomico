# Proyecto Análisis Macroeconómico con FRED y Gemini

Este proyecto permite descargar datos macroeconómicos desde la API de la
Reserva Federal de EE.UU. (FRED), procesarlos y generar un análisis
automático usando **Google Gemini**.\
El resultado final se guarda en un archivo `.txt` dentro de la carpeta
`outputs`.

## 🚀 Estructura del Proyecto

    .env                  # Variables de entorno (API Keys)
    .gitignore            # Archivos y carpetas a ignorar por Git
    config.py             # Configuración centralizada de API Keys
    main.py               # Script principal del proyecto
    requirements.txt      # Dependencias del proyecto
    utils.py              # Funciones auxiliares (guardar análisis, crear carpetas, etc.)

## ⚙️ Instalación

1.  Clona este repositorio y entra en la carpeta del proyecto:

    ``` bash
    git clone <URL_REPO>
    cd <NOMBRE_CARPETA>
    ```

2.  Crea un entorno virtual (opcional pero recomendado):

    ``` bash
    python -m venv venv
    source venv/bin/activate   # En Linux/Mac
    venv\Scripts\activate    # En Windows
    ```

3.  Instala dependencias:

    ``` bash
    pip install -r requirements.txt
    ```

4.  Configura las variables de entorno en el archivo `.env`:

    ``` env
    FRED_API_KEY=tu_api_key_fred
    GEMINI_API_KEY=tu_api_key_gemini
    ```

## ▶️ Uso

Ejecutar el script principal:

``` bash
python main.py
```

Esto descargará las series, generará los promedios anuales y consultará
a Gemini (si está configurado).\
El análisis se guardará en `outputs/` con un nombre que incluye fecha y
hora.

## 📦 Dependencias principales

-   pandas
-   fredapi
-   python-dotenv
-   google-generativeai

## 🧪 Próximos pasos

-   Añadir **tests unitarios** con `pytest`
-   Extender las métricas a más indicadores FRED
-   optimizar uso de tokens de entrada y salida
-   Mejorar prompt


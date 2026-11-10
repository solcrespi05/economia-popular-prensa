"""
Rutas y constantes compartidas por todos los scripts del proyecto.

Qué hace: define en un solo lugar dónde están los datos y dónde se guardan
las salidas, para que los scripts funcionen igual en la compu y en Colab.

Cómo se elige la carpeta raíz, en este orden:
1. Si existe la variable de entorno EP_RAIZ, se usa esa carpeta.
2. Si el código corre en Google Colab, se usa la carpeta de Drive
   /content/drive/MyDrive/economia_popular (hay que montar Drive antes y
   copiar ahí la estructura del repositorio).
3. Si no, se usa la carpeta del repositorio (la que contiene a src/).

No se corre por sí solo: los demás scripts lo importan.
"""

import os
from pathlib import Path


def _en_colab():
    try:
        import google.colab  # noqa: F401  (solo existe dentro de Colab)
        return True
    except ImportError:
        return False


if os.getenv("EP_RAIZ"):
    RAIZ = Path(os.environ["EP_RAIZ"])
elif _en_colab():
    RAIZ = Path("/content/drive/MyDrive/economia_popular")
else:
    RAIZ = Path(__file__).resolve().parents[1]

# --- Carpetas ---------------------------------------------------------------
SRC = RAIZ / "src"
DATOS_CRUDOS = RAIZ / "datos" / "crudos"        # con texto completo: NO se sube
DATOS_DERIVADOS = RAIZ / "datos" / "derivados"  # sin texto completo: se sube
RESULTADOS = RAIZ / "resultados"
INFORME = RAIZ / "informe"
FIGURAS_INFORME = INFORME / "fig"
CHECKPOINTS = RAIZ / "checkpoints"              # NO se sube
LECTURA_LLM = SRC / "04_lectura_llm"
LOTES_SALIDA = LECTURA_LLM / "lotes"            # codificaciones, sin texto de las notas
LOTES_ENTRADA = DATOS_CRUDOS / "lotes_entrada"  # notas completas para leer: NO se sube

# --- Archivos ---------------------------------------------------------------
SESION_LANACION = RAIZ / "sesion_lanacion.json"  # credencial: NO se sube
CORPUS = DATOS_CRUDOS / "corpus_economia_popular_avance.xlsx"
CORPUS_SCRAPER = DATOS_CRUDOS / "corpus_economia_popular.xlsx"
CORPUS_RECONSTRUIDO = DATOS_CRUDOS / "corpus_reconstruido_desde_checkpoints.xlsx"

FRAGMENTOS = DATOS_DERIVADOS / "fragmentos_economia_popular.xlsx"
FRAGMENTOS_CODIFICADOS = DATOS_DERIVADOS / "fragmentos_codificados.xlsx"
TABLA_EMISORES_MARCOS = DATOS_DERIVADOS / "tabla_emisores_marcos.xlsx"
REVISION_ANSES = DATOS_DERIVADOS / "fragmentos_codificados_revision_anses.xlsx"

CORPUS_FINAL_XLSX = DATOS_CRUDOS / "corpus_final_codificado.xlsx"
CORPUS_FINAL_PARQUET = DATOS_CRUDOS / "corpus_final_codificado.parquet"
CORPUS_FINAL_SIN_NOTA = DATOS_DERIVADOS / "corpus_final_codificado_sin_nota.xlsx"

CIFRAS_INFORME = RESULTADOS / "cifras.txt"
COMPARACION_METODOS = RESULTADOS / "comparacion_metodos.xlsx"

# --- Constantes -------------------------------------------------------------
# Colores pedidos por la directora: todos los gráficos van separados por diario.
DIARIOS = ["Página/12", "La Nación"]
COLOR = {"Página/12": "#C62828", "La Nación": "#1F5FAE"}

# Separador de las celdas con varios valores (emisores, tipos, marcos).
SEP = " | "

# Excel no guarda más de esta cantidad de caracteres en una celda.
LIMITE_CELDA_EXCEL = 32767

"""
Arma el corpus en Excel a partir de los checkpoints que va guardando el scraper.

Qué hace: une las notas de Página/12 y La Nación, filtra por fecha y deja
solo las columnas del corpus. Únicamente LEE los checkpoints.

Lee:    checkpoints/pagina12_estado.json, pagina12_textos.json y lanacion_logueado.json
Genera: datos/crudos/corpus_reconstruido_desde_checkpoints.xlsx
        (con otro nombre a propósito, para no pisar el corpus de control si
        falta algún checkpoint)

Cómo se corre, desde la carpeta del repositorio:
    python3 src/01_scraper/armar_corpus.py
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

CHECKPOINT_DIR = config.CHECKPOINTS

FECHA_DESDE = datetime(2019, 9, 1)
FECHA_HASTA = datetime(2023, 9, 30)

PATRON_MENCION = re.compile(r"econom[ií]as?\s+popular(?:es)?", re.IGNORECASE)


def cargar_checkpoint(nombre, default=None):
    ruta = CHECKPOINT_DIR / nombre
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    return default if default is not None else {}


def _parsear_fecha(fecha_str):
    if not fecha_str:
        return None
    if isinstance(fecha_str, datetime):
        return fecha_str
    formatos = ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d")
    for fmt in formatos:
        try:
            return datetime.strptime(fecha_str, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(fecha_str.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def filtrar_por_fecha(articulos, desde, hasta):
    filtrados = []
    descartados_sin_fecha = 0
    for a in articulos:
        fecha_raw = a.get("fecha")
        fecha = fecha_raw if isinstance(fecha_raw, datetime) else _parsear_fecha(fecha_raw)
        if fecha is None:
            descartados_sin_fecha += 1
            continue
        a["fecha"] = fecha
        if desde <= fecha <= hasta:
            filtrados.append(a)
    if descartados_sin_fecha:
        print(f"(aviso) {descartados_sin_fecha} artículos sin fecha parseable quedaron afuera del filtro.")
    return filtrados


def menciona_economia_popular(articulo):
    campos = [articulo.get("texto_completo"), articulo.get("titulo"), articulo.get("volanta_bajada")]
    for campo in campos:
        if campo and PATRON_MENCION.search(campo):
            return True
    return False


def exportar_avance_parcial(ruta=config.CORPUS_RECONSTRUIDO):
    """Arma un Excel con todo lo que hay guardado en los checkpoints HASTA
    AHORA (los va escribiendo el otro notebook, el que scrapea), sin
    esperar a que termine el proceso completo. Esta función solo LEE esos
    checkpoints, nunca escribe en ellos, así que no interfiere con el
    scraper que puede estar corriendo en paralelo en otro runtime."""
    estado_p12 = cargar_checkpoint("pagina12_estado.json", {"offset": 0, "articulos": []})
    articulos_p12 = estado_p12["articulos"]
    textos_p12 = cargar_checkpoint("pagina12_textos.json", {})
    for art in articulos_p12:
        art["texto_completo"] = textos_p12.get(art["link"])
    articulos_p12 = filtrar_por_fecha(articulos_p12, FECHA_DESDE, FECHA_HASTA)

    # La Nación: solo las notas recuperadas con la sesión de la suscripción.
    estado_log = cargar_checkpoint("lanacion_logueado.json", {"articulos": [], "fallidos": {}})
    articulos_ln = [a for a in estado_log["articulos"] if menciona_economia_popular(a)]
    articulos_ln = filtrar_por_fecha(articulos_ln, FECHA_DESDE, FECHA_HASTA)

    todos = articulos_p12 + articulos_ln
    print(f"Página/12: {len(articulos_p12)} | La Nación: {len(articulos_ln)} | Total: {len(todos)}")

    df = pd.DataFrame(todos)
    columnas = ["medio", "titulo", "fecha", "autor", "seccion", "volanta_bajada", "texto_completo", "link"]
    for col in columnas:
        if col not in df.columns:
            df[col] = None
    df = df[columnas].sort_values(["medio", "fecha"])

    df.to_excel(ruta, index=False)
    print(f"Guardado en: {ruta}")
    return df


if __name__ == "__main__":
    exportar_avance_parcial()

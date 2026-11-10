"""
Valida los lotes leídos y arma el corpus final codificado.

Qué hace: une los lote_*.jsonl, controla que cada mención esté una sola vez y
que todas las etiquetas sean válidas, y agrega la nota completa por `link`.
Si falta una mención, se detiene y no genera el corpus final.

Lee:    src/04_lectura_llm/lotes/lote_*.jsonl
        datos/derivados/fragmentos_codificados.xlsx
        datos/crudos/corpus_economia_popular_avance.xlsx
        checkpoints/pagina12_textos.json y lanacion_logueado.json, si existen,
        para recuperar el texto de las notas cortadas por Excel
Genera: datos/crudos/corpus_final_codificado.xlsx (con la nota, cortada por Excel)
        datos/crudos/corpus_final_codificado.parquet (con el texto más largo disponible)
        datos/derivados/corpus_final_codificado_sin_nota.xlsx (para el repositorio)

Los lotes conservan las etiquetas numeradas con las que se hizo la lectura
(ver instrucciones.md). Al unirlos se les quita esa numeración.

Cómo se corre, desde la carpeta del repositorio:
    python3 src/04_lectura_llm/validar_y_unir.py
    python3 src/04_lectura_llm/validar_y_unir.py --parcial CARPETA   # prueba con lo ya leído
"""
import argparse
import importlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

COLUMNAS_CODIGO = ["medio", "titulo", "fecha", "seccion", "link", "mencion_textual", "fragmento", "actor_candidato",
                   "verbo_atribucion", "emisores_detectados", "tipo_emisor", "subtipo_emisor", "marcos_detectados"]
COLUMNAS_LLM = ["emisor_llm", "tipo_emisor_llm", "subtipo_emisor_llm", "marcos_llm", "solo_nombre_llm", "duda_llm"]


def sin_numeracion(celda):
    """Quita el prefijo de cada etiqueta: "1b. Algo | 2. Otra" -> "Algo | Otra"."""
    return config.SEP.join(re.sub(r"^\d+[a-z]?\.\s+", "", e) for e in str(celda).split(config.SEP))


def etiquetas_validas():
    d = importlib.import_module("03_codificacion_diccionario")
    return {
        "tipo_emisor_llm": set(d.TIPOS),
        "subtipo_emisor_llm": {s for _, s, _ in d.EMISORES.values()},
        "marcos_llm": set(d.MARCOS),
    }


def leer_lotes():
    filas, errores = [], []
    for f in sorted(config.LOTES_SALIDA.glob("lote_*.jsonl")):
        for n, linea in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if not linea.strip():
                continue
            try:
                filas.append({**json.loads(linea), "_origen": f"{f.name}:{n}"})
            except json.JSONDecodeError as e:
                errores.append(f"{f.name}:{n}: JSON inválido ({e})")
    lotes = pd.DataFrame(filas)
    for col in ("tipo_emisor_llm", "subtipo_emisor_llm", "marcos_llm"):
        if col in lotes:
            lotes[col] = lotes[col].apply(sin_numeracion)
    return lotes, errores


def errores_de_contenido(l, ids_esperados):
    """Lista de problemas. Vacía = todo correcto."""
    err = []
    faltan_col = set(["id_mencion"] + COLUMNAS_LLM) - set(l.columns)
    if faltan_col:
        return [f"faltan columnas: {sorted(faltan_col)}"]
    err += [f"id repetido: {i}" for i in l.id_mencion[l.id_mencion.duplicated()].unique()]
    err += [f"id desconocido: {i}" for i in set(l.id_mencion) - ids_esperados]
    for col, validas in etiquetas_validas().items():
        for _, f in l.iterrows():
            valores = [v for v in str(f[col]).split(config.SEP) if v]
            err += [f"{f._origen} {f.id_mencion}: {col} inválido: {v!r}" for v in valores if v not in validas]
            if col != "marcos_llm" and not valores:
                err.append(f"{f._origen} {f.id_mencion}: {col} vacío")
    err += [f"{f._origen} {f.id_mencion}: solo_nombre_llm no es booleano"
            for _, f in l.iterrows() if not isinstance(f.solo_nombre_llm, (bool,))]
    err += [f"{f._origen} {f.id_mencion}: emisor_llm vacío" for _, f in l.iterrows() if not str(f.emisor_llm).strip()]
    # Un subtipo tiene que pertenecer a alguno de los tipos asignados.
    d = importlib.import_module("03_codificacion_diccionario")
    tipo_de = {s: t for t, s, _ in d.EMISORES.values()}
    for _, f in l.iterrows():
        tipos = str(f.tipo_emisor_llm).split(config.SEP)
        err += [f"{f._origen} {f.id_mencion}: subtipo {s!r} no corresponde a {tipos}"
                for s in str(f.subtipo_emisor_llm).split(config.SEP) if s in tipo_de and tipo_de[s] not in tipos]
    return err


def textos_recuperados():
    """Texto sin el corte de Excel, desde los checkpoints que estén disponibles."""
    enteros = {}
    ruta_p12 = config.CHECKPOINTS / "pagina12_textos.json"
    if ruta_p12.exists():
        enteros.update({k: v for k, v in json.loads(ruta_p12.read_text(encoding="utf-8")).items() if isinstance(v, str)})
    ruta_ln = config.CHECKPOINTS / "lanacion_logueado.json"
    if ruta_ln.exists():
        for a in json.loads(ruta_ln.read_text(encoding="utf-8")).get("articulos", []):
            if isinstance(a.get("texto_completo"), str):
                enteros[a["link"]] = a["texto_completo"]
    return enteros


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parcial", type=Path, help="carpeta donde dejar una salida de prueba con lo ya leído")
    args = ap.parse_args()

    k = pd.read_excel(config.FRAGMENTOS_CODIFICADOS)
    k.insert(0, "id_mencion", [f"M{i:04d}" for i in range(1, len(k) + 1)])
    l, errores = leer_lotes()
    if len(l) == 0:
        sys.exit("No hay lotes leídos.")
    errores += errores_de_contenido(l, set(k.id_mencion))
    faltan = sorted(set(k.id_mencion) - set(l.id_mencion))
    print(f"Menciones leídas: {l.id_mencion.nunique()} de {len(k)} | Faltan: {len(faltan)} | Errores: {len(errores)}")
    for e in errores[:50]:
        print("  ", e)
    if errores or (faltan and not args.parcial):
        sys.exit("No se genera el corpus final: hay errores o faltan menciones." + (f" Primeras: {faltan[:10]}" if faltan else ""))

    corpus = pd.read_excel(config.CORPUS).set_index("link").texto_completo
    enteros = textos_recuperados()
    t = k[["id_mencion"] + COLUMNAS_CODIGO].merge(l[["id_mencion"] + COLUMNAS_LLM], on="id_mencion", how="inner")
    assert list(t.id_mencion) == sorted(t.id_mencion)  # mismo orden de filas que el diccionario

    # Se usa el recuperado solo si amplía de verdad el texto cortado.
    def mejor(link):
        base = corpus[link]
        ent = enteros.get(link)
        return ent if isinstance(ent, str) and len(ent) > len(base) and ent.startswith(base[:1000]) else base

    nota = t.link.map(mejor)
    # Si el texto mide justo el límite, Excel lo cortó aunque no se haya recuperado el resto.
    truncada = t.link.map(lambda x: len(corpus[x]) >= config.LIMITE_CELDA_EXCEL) | (nota.str.len() > config.LIMITE_CELDA_EXCEL)
    entero = t.link.map(lambda x: len(corpus[x]) < config.LIMITE_CELDA_EXCEL) | (nota.str.len() > config.LIMITE_CELDA_EXCEL)

    pos = len(["id_mencion"] + COLUMNAS_CODIGO)
    sin_nota = t.copy()
    sin_nota.insert(pos, "nota_truncada_en_excel", truncada)
    con_nota = sin_nota.copy()
    con_nota.insert(pos, "nota_completa", nota)
    excel = con_nota.copy()
    excel["nota_completa"] = excel.nota_completa.str.slice(0, config.LIMITE_CELDA_EXCEL)
    parquet = con_nota.assign(texto_entero_disponible=entero, fecha=con_nota.fecha.astype(str))

    if args.parcial:
        args.parcial.mkdir(parents=True, exist_ok=True)
        rutas = (args.parcial / "final.xlsx", args.parcial / "final.parquet", args.parcial / "sin_nota.xlsx")
    else:
        rutas = (config.CORPUS_FINAL_XLSX, config.CORPUS_FINAL_PARQUET, config.CORPUS_FINAL_SIN_NOTA)
    excel.to_excel(rutas[0], index=False)
    parquet.to_parquet(rutas[1], index=False)
    sin_nota.to_excel(rutas[2], index=False)
    print(f"Filas: {len(t)} | Notas truncadas por Excel en la tabla: {t.link[truncada].nunique()} | "
          f"sin texto entero disponible: {t.link[~entero].nunique()}")
    for r in rutas:
        print("Guardado:", r)


if __name__ == "__main__":
    main()

"""
Prepara los lotes de notas para la lectura mención por mención.

Qué hace: asigna un id_mencion estable (M0001, M0002...) siguiendo el orden de
filas del diccionario, marca en el texto la aparición exacta de cada mención y
agrupa las notas en lotes. Las menciones de una misma nota van siempre juntas.
Los lotes no incluyen los resultados del diccionario, para que la lectura sea
independiente.

Lee:    datos/crudos/corpus_economia_popular_avance.xlsx
        datos/derivados/fragmentos_codificados.xlsx
Genera: datos/crudos/lotes_entrada/lote_NNN.txt (con texto completo: no se sube)

Cómo se corre, desde la carpeta del repositorio:
    python3 src/04_lectura_llm/preparar_lotes.py --piloto   # lote_000, ~30 menciones
    python3 src/04_lectura_llm/preparar_lotes.py            # el resto, lote_001 en adelante
"""
import argparse
import importlib
import random
import re
import sys
import textwrap
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

MAX_CARACTERES_LOTE = 150_000
MAX_MENCIONES_LOTE = 60
MENCIONES_PILOTO = 30
SEMILLA = 2026
# Filas de la revisión de ANSES que conviene mirar en la prueba: cita del
# organismo, voz del diario, columna de opinión y ANSES como fuente de datos.
FILAS_PILOTO_FIJAS = [536, 802, 1636, 1846]


def cargar():
    """Devuelve las menciones con su id y el corpus indexado por link."""
    k = pd.read_excel(config.FRAGMENTOS_CODIFICADOS)
    k.insert(0, "id_mencion", [f"M{i:04d}" for i in range(1, len(k) + 1)])
    c = pd.read_excel(config.CORPUS).set_index("link")
    return k, c


def texto_con_marcas(texto, menciones, patron):
    """Inserta ⟦id⟧...⟦/id⟧ en cada aparición. Como 02_extraer_fragmentos genera
    las filas de una nota en orden de aparición, la n-ésima fila de la nota
    corresponde a la n-ésima coincidencia del patrón."""
    apariciones = list(patron.finditer(texto))
    assert len(apariciones) == len(menciones), "cantidad de menciones distinta"
    salida, pos = [], 0
    for m, (_, fila) in zip(apariciones, menciones.iterrows()):
        assert m.group(0) == fila.mencion_textual, fila.id_mencion
        salida += [texto[pos:m.start()], f"⟦{fila.id_mencion}⟧{m.group(0)}⟦/{fila.id_mencion}⟧"]
        pos = m.end()
    return "".join(salida) + texto[pos:]


def bloque_nota(link, menciones, corpus, patron, n, total):
    nota = corpus.loc[link]
    # Se parten las líneas largas para que la herramienta de lectura no las corte.
    cuerpo = "\n".join(
        textwrap.fill(p, 200, break_long_words=False, break_on_hyphens=False)
        for p in texto_con_marcas(nota.texto_completo, menciones, patron).split("\n")
    )
    campos = [("medio", nota.medio), ("titulo", nota.titulo), ("fecha", nota.fecha), ("autor", nota.autor),
              ("seccion", nota.seccion), ("volanta_bajada", nota.volanta_bajada), ("link", link)]
    cabecera = "\n".join(f"{c}: {'' if pd.isna(v) else v}" for c, v in campos)
    return (f"===== NOTA {n} de {total} =====\n{cabecera}\n"
            f"marcas a codificar: {', '.join(menciones.id_mencion)}\n----- TEXTO -----\n{cuerpo}\n\n")


def elegir_piloto(k):
    """Notas de las filas fijas y luego notas al azar, alternando diario."""
    azar = random.Random(SEMILLA)
    links = list(dict.fromkeys(k.link.iloc[FILAS_PILOTO_FIJAS]))
    resto = {d: sorted(set(k.link[k.medio == d]) - set(links)) for d in config.DIARIOS}
    for lista in resto.values():
        azar.shuffle(lista)
    d = 0
    while k.link.isin(links).sum() < MENCIONES_PILOTO:
        links.append(resto[config.DIARIOS[d % 2]].pop())
        d += 1
    return links


def agrupar(k, corpus):
    """Reparte las notas en lotes, respetando los dos topes."""
    lotes, actual, chars, menc = [], [], 0, 0
    for link, m in k.groupby("link", sort=False):
        largo = len(corpus.loc[link].texto_completo)
        if actual and (chars + largo > MAX_CARACTERES_LOTE or menc + len(m) > MAX_MENCIONES_LOTE):
            lotes.append(actual)
            actual, chars, menc = [], 0, 0
        actual.append(link)
        chars += largo
        menc += len(m)
    return lotes + ([actual] if actual else [])


def escribir(numero, links, k, corpus, patron):
    config.LOTES_ENTRADA.mkdir(parents=True, exist_ok=True)
    grupos = [(l, k[k.link == l]) for l in links]
    texto = "".join(bloque_nota(l, m, corpus, patron, i, len(grupos)) for i, (l, m) in enumerate(grupos, 1))
    (config.LOTES_ENTRADA / f"lote_{numero:03d}.txt").write_text(texto, encoding="utf-8")
    return len(grupos), sum(len(m) for _, m in grupos), len(texto)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piloto", action="store_true")
    args = ap.parse_args()
    patron = importlib.import_module("02_extraer_fragmentos").PATRON_MENCION
    k, corpus = cargar()

    if args.piloto:
        print("lote_000: %d notas, %d menciones, %d caracteres" % escribir(0, elegir_piloto(k), k, corpus, patron))
        return

    # Si la prueba ya está hecha y validada, sus notas no se vuelven a leer.
    salida_piloto = config.LOTES_SALIDA / "lote_000.jsonl"
    pendientes = k
    if salida_piloto.exists():
        hechos = pd.read_json(salida_piloto, lines=True).id_mencion
        pendientes = k[~k.link.isin(k.link[k.id_mencion.isin(hechos)])]
    lotes = agrupar(pendientes, corpus)
    for n, links in enumerate(lotes, 1):
        print(f"lote_{n:03d}: %d notas, %d menciones, %d caracteres" % escribir(n, links, pendientes, corpus, patron))
    print(f"Total: {len(lotes)} lotes, {len(pendientes)} menciones")


if __name__ == "__main__":
    main()

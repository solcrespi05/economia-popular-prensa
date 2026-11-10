"""
Confirma que la cadena da los valores de control y que el repo no expone texto.

Qué hace:
1. Compara las salidas de los scripts 02 y 03 con los valores esperados.
2. Recorre datos/derivados y resultados y falla si algún Excel o Parquet tiene
   una columna con el texto completo de las notas.

Lee:    datos/derivados/fragmentos_codificados.xlsx y las carpetas que se suben
Genera: nada; imprime OK o ERROR por cada control

Cómo se corre, desde la carpeta del repositorio:
    python3 src/verificar_controles.py
"""
import importlib
import sys

import pandas as pd

import config

ESPERADOS = {
    "Menciones": 2043,
    "Notas con al menos una mención": 1204,
    "Menciones de Página/12": 1059,
    "Menciones de La Nación": 984,
    "Menciones con el marco Trabajo (con la corrección)": 881,
    "Menciones con el marco Trabajo (sin la corrección)": 1366,
}
COLUMNAS_PROHIBIDAS = {"texto_completo", "nota_completa"}


def calcular_controles():
    dic = importlib.import_module("03_codificacion_diccionario")
    k = pd.read_excel(config.FRAGMENTOS_CODIFICADOS)
    marco12 = "Trabajo / trabajadores"
    con = k.marcos_detectados.fillna("").apply(lambda s: marco12 in s.split(config.SEP))
    # "Sin la corrección" = buscar el marco sobre el fragmento con los nombres propios.
    sin = k.fragmento.fillna("").apply(lambda s: bool(dic.MARCOS_COMPILADOS[marco12].search(s)))
    return {
        "Menciones": len(k),
        "Notas con al menos una mención": k.link.nunique(),
        "Menciones de Página/12": int((k.medio == "Página/12").sum()),
        "Menciones de La Nación": int((k.medio == "La Nación").sum()),
        "Menciones con el marco Trabajo (con la corrección)": int(con.sum()),
        "Menciones con el marco Trabajo (sin la corrección)": int(sin.sum()),
    }


def archivos_con_texto():
    """Devuelve los archivos publicables que tienen columnas de texto completo."""
    malos = []
    for carpeta in (config.DATOS_DERIVADOS, config.RESULTADOS):
        for f in sorted(carpeta.rglob("*")):
            if f.suffix == ".xlsx":
                hojas = pd.read_excel(f, sheet_name=None, nrows=0)
                columnas = {c for d in hojas.values() for c in d.columns}
            elif f.suffix == ".parquet":
                columnas = set(pd.read_parquet(f).columns)
            else:
                continue
            if columnas & COLUMNAS_PROHIBIDAS:
                malos.append(f)
    return malos


def main():
    obtenidos = calcular_controles()
    ok = True
    for nombre, esperado in ESPERADOS.items():
        bien = obtenidos[nombre] == esperado
        ok &= bien
        print(f"{'OK   ' if bien else 'ERROR'} {nombre}: {obtenidos[nombre]} (esperado {esperado})")
    malos = archivos_con_texto()
    print(f"{'OK   ' if not malos else 'ERROR'} Archivos publicables con texto completo: {len(malos)}")
    for f in malos:
        print("      ", f)
    sys.exit(0 if ok and not malos else 1)


if __name__ == "__main__":
    main()

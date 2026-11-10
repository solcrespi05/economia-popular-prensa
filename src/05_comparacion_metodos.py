"""
Compara, mención por mención, el diccionario con la lectura asistida por IA.

Qué hace: calcula matrices de confusión binarias por marco y por tipo de
emisor, una matriz multiclase del emisor principal y una tabla de las menciones
"solo nombre". Todo se calcula en total y por diario.

La lectura se toma como referencia para poder medir, pero NO es una verdad
absoluta: falta validarla con el equipo. Por eso, "precisión" y "cobertura"
significan acá acuerdo con la lectura, no acierto comprobado.

Criterio del emisor principal (matriz multiclase):
- Lectura: el primer tipo de `tipo_emisor_llm`. Las instrucciones piden poner
  primero el rol desde el que habla la persona.
- Diccionario: no sabe quién habla, así que se aproxima. Si la nota es de
  opinión, gana Otros / medios / academia, porque el emisor es el autor de la columna. Si no,
  gana el emisor cuyo patrón aparece más cerca de la mención dentro del
  fragmento. Si no detectó ninguno, la fila queda como "Sin emisor detectado".

Lee:    datos/derivados/corpus_final_codificado_sin_nota.xlsx
Genera: resultados/comparacion_metodos.xlsx
        resultados/figuras/*.pdf (heatmaps separados por diario) y una copia en informe/fig/

Cómo se corre, desde la carpeta del repositorio:
    python3 src/05_comparacion_metodos.py
    python3 src/05_comparacion_metodos.py --entrada ARCHIVO --salida CARPETA   # prueba
"""
import argparse
import importlib
import shutil
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd

import config

dic = importlib.import_module("03_codificacion_diccionario")

SEP = config.SEP
SIN_EMISOR = "Sin emisor detectado"
ALCANCES = ["Total"] + config.DIARIOS
AVISO = ("La lectura con IA se usa como referencia para medir el acuerdo, pero no es una verdad absoluta: "
         "falta validarla con el equipo.")
RAMPA = {
    "Página/12": LinearSegmentedColormap.from_list("rojos", ["#FFFFFF", "#F4C7C3", "#C62828"]),
    "La Nación": LinearSegmentedColormap.from_list("azules", ["#FFFFFF", "#BCD3EE", "#1F5FAE"]),
}
NOMBRE_ARCHIVO = {"Página/12": "pagina12", "La Nación": "lanacion"}


def lista(valor):
    return [v for v in str(valor).split(SEP) if v and v != "nan"]


def seleccionar(k, alcance):
    return k if alcance == "Total" else k[k.medio == alcance]


def metricas(codigo, lectura):
    """VP, FP, FN, VN y medidas, con el código como predicción y la lectura como referencia."""
    c, l = np.asarray(codigo, bool), np.asarray(lectura, bool)
    vp, fp, fn, vn = int((c & l).sum()), int((c & ~l).sum()), int((~c & l).sum()), int((~c & ~l).sum())
    n = vp + fp + fn + vn
    prec = vp / (vp + fp) if vp + fp else np.nan
    cob = vp / (vp + fn) if vp + fn else np.nan
    f1 = 2 * vp / (2 * vp + fp + fn) if 2 * vp + fp + fn else np.nan
    # Kappa de Cohen: acuerdo observado corregido por el esperable por azar.
    po = (vp + vn) / n if n else np.nan
    pe = ((vp + fp) * (vp + fn) + (fn + vn) * (fp + vn)) / n**2 if n else np.nan
    kappa = (po - pe) / (1 - pe) if n and pe < 1 else np.nan
    return {"VP": vp, "FP": fp, "FN": fn, "VN": vn, "total_codigo": vp + fp, "total_lectura": vp + fn,
            "precision": prec, "cobertura": cob, "F1": f1, "kappa": kappa}


def tabla_binaria(k, col_codigo, col_lectura, etiquetas, nombre):
    filas = []
    for alcance in ALCANCES:
        s = seleccionar(k, alcance)
        cod, lec = s[col_codigo].apply(lista), s[col_lectura].apply(lista)
        for e in etiquetas:
            filas.append({"alcance": alcance, nombre: e,
                          **metricas(cod.apply(lambda x: e in x), lec.apply(lambda x: e in x))})
    return pd.DataFrame(filas)


def posicion_mencion(fragmento, mencion):
    """Posición de la mención: la aparición más cercana al centro de la ventana."""
    pos, inicio = [], fragmento.find(mencion)
    while inicio != -1:
        pos.append(inicio)
        inicio = fragmento.find(mencion, inicio + 1)
    return min(pos, key=lambda p: abs(p - 300)) if pos else 300


def tipo_principal_codigo(fila):
    emisores = lista(fila.emisores_detectados)
    if not emisores:
        return SIN_EMISOR
    if dic.EMISOR_EDITORIAL in emisores:
        return dic.EMISORES[dic.EMISOR_EDITORIAL][0]
    frag = str(fila.fragmento)
    limpio = dic.PATRON_NOMBRE_CON_TERMINO.sub(lambda m: " " * len(m.group(0)), frag)  # conserva posiciones
    centro = posicion_mencion(frag, str(fila.mencion_textual))
    distancia = {}
    for e in emisores:
        apariciones = [abs(m.start() - centro) for m in dic.EMISORES_COMPILADOS[e].finditer(limpio)]
        if apariciones:
            distancia[e] = min(apariciones)
    # Al sacar los nombres puede no quedar coincidencia; entonces vale el primero detectado.
    elegido = min(distancia, key=distancia.get) if distancia else emisores[0]
    return dic.EMISORES[elegido][0]


def matriz_multiclase(k, alcance):
    s = seleccionar(k, alcance)
    return (pd.crosstab(s.tipo_principal_codigo, s.tipo_principal_lectura)
            .reindex(index=dic.TIPOS + [SIN_EMISOR], columns=dic.TIPOS, fill_value=0))


def es_nombre_en_mencion(fila):
    """True si la mención cae dentro de un nombre propio según el patrón del diccionario."""
    frag, centro = str(fila.fragmento), posicion_mencion(str(fila.fragmento), str(fila.mencion_textual))
    return any(m.start() <= centro < m.end() for m in dic.PATRON_NOMBRE_CON_TERMINO.finditer(frag))


def tabla_solo_nombre(k):
    filas = []
    for alcance in ALCANCES:
        s = seleccionar(k, alcance)
        for valor in (True, False):
            g = s[s.solo_nombre_llm == valor]
            n = len(g)
            filas.append({
                "alcance": alcance, "solo_nombre_lectura": valor, "menciones": n,
                "patron_nombre_del_diccionario": int(g.apply(es_nombre_en_mencion, axis=1).sum()) if n else 0,
                "codigo_sin_emisor": int(g.emisores_detectados.isna().sum()),
                "codigo_con_emisor": int(g.emisores_detectados.notna().sum()),
                "codigo_sin_marco": int(g.marcos_detectados.isna().sum()),
                "codigo_con_marco": int(g.marcos_detectados.notna().sum()),
                "codigo_marco_trabajo": int(g.marcos_detectados.apply(lambda v: "Trabajo / trabajadores" in lista(v)).sum()),
                "codigo_marco_integracion": int(g.marcos_detectados.apply(
                    lambda v: "Integración económica / desarrollo productivo" in lista(v)).sum()),
            })
    return pd.DataFrame(filas)


def desacuerdos(k, n=30, ejemplos=3):
    """Los n desacuerdos más frecuentes, de marcos y de emisor principal."""
    casos = {}
    for _, f in k.iterrows():
        cod, lec = set(lista(f.marcos_detectados)), set(lista(f.marcos_llm))
        claves = [("Marco", m, "El código lo marca y la lectura no") for m in cod - lec]
        claves += [("Marco", m, "La lectura lo marca y el código no") for m in lec - cod]
        if f.tipo_principal_codigo != f.tipo_principal_lectura:
            claves.append(("Emisor principal", f"Código: {f.tipo_principal_codigo}", f"Lectura: {f.tipo_principal_lectura}"))
        for c in claves:
            casos.setdefault(c, []).append(f)
    filas = []
    for (dimension, etiqueta, detalle), lista_filas in sorted(casos.items(), key=lambda kv: -len(kv[1]))[:n]:
        conteo = Counter(x.medio for x in lista_filas)
        fila = {"dimension": dimension, "etiqueta": etiqueta, "detalle": detalle, "menciones": len(lista_filas),
                "Página/12": conteo["Página/12"], "La Nación": conteo["La Nación"]}
        for i, x in enumerate(lista_filas[:ejemplos], 1):
            fila[f"ejemplo_{i}_id"] = x.id_mencion
            fila[f"ejemplo_{i}_fragmento"] = x.fragmento
        filas.append(fila)
    return pd.DataFrame(filas)


def corto(etiqueta):
    return (str(etiqueta).split(". ", 1)[-1].replace(" / desarrollo productivo", "").replace(" / seguridad / orden público", "")
            .replace("Organizaciones de la economía popular", "Organizaciones de la EP"))


def pintar(ax, valores, textos, rampa):
    ax.imshow(valores, cmap=rampa, vmin=0, vmax=1, aspect="auto")
    for (i, j), t in np.ndenumerate(textos):
        ax.text(j, i, t, ha="center", va="center", fontsize=7, color="white" if valores[i, j] > 0.62 else "#222222")
    ax.set_xticks(np.arange(valores.shape[1] + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(valores.shape[0] + 1) - 0.5, minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5)
    ax.tick_params(which="both", length=0)
    for lado in ax.spines.values():
        lado.set_visible(False)


def fig_multiclase(k, carpeta):
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.1), sharey=True)
    for ax, d in zip(axs, config.DIARIOS):
        m = matriz_multiclase(k, d)
        # El color muestra el % de cada fila, para comparar diarios de distinto tamaño.
        pct = m.div(m.sum(axis=1).replace(0, np.nan), axis=0).fillna(0).values
        pintar(ax, pct, m.values.astype(str), RAMPA[d])
        ax.set_xticks(range(len(m.columns)), ["Estatal", "Organiz.", "Dirig.", "Privado", "Otros"], fontsize=7)
        ax.set_yticks(range(len(m.index)), [corto(i) for i in m.index], fontsize=7.5)
        ax.set_xlabel("Tipo según la lectura con IA", fontsize=8)
        ax.set_title(f"{d} (n = {int(m.values.sum()):,})".replace(",", "."), fontsize=9, loc="left", fontweight="bold")
    axs[0].set_ylabel("Tipo según el diccionario", fontsize=8)
    fig.text(0.5, -0.02, "Otros incluye medios y academia. "
             "Número: menciones. Color: % de la fila.", ha="center", fontsize=7, color="#555555")
    fig.tight_layout()
    fig.savefig(carpeta / "fig_confusion_emisor.pdf", bbox_inches="tight")
    plt.close(fig)


def fig_binaria(tabla, columna, etiquetas, archivo, carpeta, alto):
    claves = ["VP", "FP", "FN", "VN"]
    fig, axs = plt.subplots(1, 2, figsize=(7.2, alto), sharey=True)
    for ax, d in zip(axs, config.DIARIOS):
        t = tabla[tabla.alcance == d].set_index(columna).loc[etiquetas]
        vals = t[claves].values.astype(float)
        pintar(ax, vals / vals.sum(axis=1, keepdims=True), t[claves].values.astype(str), RAMPA[d])
        ax.set_xticks(range(4), claves, fontsize=8)
        ax.xaxis.tick_top()
        ax.set_yticks(range(len(etiquetas)), [corto(e) for e in etiquetas], fontsize=7.5)
        ax.set_title(f"{d}", fontsize=9, loc="left", fontweight="bold", pad=18)
    fig.text(0.5, -0.02, "VP: ambos marcan · FP: solo el diccionario · FN: solo la lectura · VN: ninguno. "
             "Número: menciones. Color: % de la fila.", ha="center", fontsize=7, color="#555555")
    fig.tight_layout()
    fig.savefig(carpeta / archivo, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", type=Path, default=config.CORPUS_FINAL_SIN_NOTA)
    ap.add_argument("--salida", type=Path, default=None, help="carpeta alternativa, para pruebas")
    args = ap.parse_args()

    carpeta = args.salida or config.RESULTADOS
    figuras = carpeta / "figuras"
    figuras.mkdir(parents=True, exist_ok=True)

    k = pd.read_excel(args.entrada)
    k["solo_nombre_llm"] = k.solo_nombre_llm.astype(bool)
    k["tipo_principal_codigo"] = k.apply(tipo_principal_codigo, axis=1)
    k["tipo_principal_lectura"] = k.tipo_emisor_llm.apply(lambda v: lista(v)[0])

    marcos = list(dic.MARCOS)
    t_marcos = tabla_binaria(k, "marcos_detectados", "marcos_llm", marcos, "marco")
    t_tipos = tabla_binaria(k, "tipo_emisor", "tipo_emisor_llm", dic.TIPOS, "tipo_emisor")
    t_solo = tabla_solo_nombre(k)
    # Efecto de la corrección del marco Trabajo: el patrón aplicado sobre el fragmento con los nombres propios.
    marco12 = "Trabajo / trabajadores"
    sin_correccion = k.fragmento.fillna("").apply(lambda f: bool(dic.MARCOS_COMPILADOS[marco12].search(f)))
    filas_12 = []
    for alcance in ALCANCES:
        s = seleccionar(k, alcance)
        lectura = s.marcos_llm.apply(lambda v: marco12 in lista(v))
        filas_12.append({"alcance": alcance, "version": "sin la corrección", **metricas(sin_correccion[s.index], lectura)})
        filas_12.append({"alcance": alcance, "version": "con la corrección",
                         **metricas(s.marcos_detectados.apply(lambda v: marco12 in lista(v)), lectura)})
    t_12 = pd.DataFrame(filas_12)
    t_desac = desacuerdos(k)

    salida = carpeta / config.COMPARACION_METODOS.name
    with pd.ExcelWriter(salida) as w:
        pd.DataFrame({"nota": [AVISO,
                               "Marcos y tipos: el código es la predicción y la lectura la referencia.",
                               "Emisor principal: primer tipo de la lectura; en el código, opinión o patrón más cercano a la mención."]
                      }).to_excel(w, sheet_name="leeme", index=False)
        t_marcos.to_excel(w, sheet_name="marcos_binario", index=False)
        t_tipos.to_excel(w, sheet_name="tipos_binario", index=False)
        for a in ALCANCES:
            matriz_multiclase(k, a).to_excel(w, sheet_name=f"emisor_principal_{a}"[:31].replace("/", "_"))
        t_solo.to_excel(w, sheet_name="solo_nombre", index=False)
        t_12.to_excel(w, sheet_name="marco_trabajo_correccion", index=False)
        t_desac.to_excel(w, sheet_name="desacuerdos_top30", index=False)

    fig_multiclase(k, figuras)
    fig_binaria(t_marcos, "marco", marcos, "fig_confusion_marcos.pdf", figuras, 4.4)
    fig_binaria(t_tipos, "tipo_emisor", dic.TIPOS, "fig_confusion_tipos.pdf", figuras, 2.2)
    if args.salida is None:
        for f in figuras.glob("*.pdf"):
            shutil.copy2(f, config.FIGURAS_INFORME / f.name)

    print(AVISO)
    print(t_marcos[t_marcos.alcance == "Total"][["marco", "VP", "FP", "FN", "VN", "precision", "cobertura", "F1", "kappa"]]
          .round(2).to_string(index=False))
    print(f"Guardado: {salida}")


if __name__ == "__main__":
    main()

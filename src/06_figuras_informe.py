"""Figuras y cifras del informe final.

Lee:    datos/crudos/corpus_economia_popular_avance.xlsx
        datos/derivados/fragmentos_codificados.xlsx (salida de
        03_codificacion_diccionario.py, con la corrección del marco Trabajo)
Genera: informe/fig/*.pdf (una figura por archivo, separadas por diario)
        resultados/cifras.txt (los números que cita el texto del informe)

Cómo se corre, desde la carpeta del repositorio:
    python3 src/06_figuras_informe.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config

CORPUS, CODIF, SALIDA = config.CORPUS, config.FRAGMENTOS_CODIFICADOS, config.FIGURAS_INFORME
COLOR, DIARIOS = config.COLOR, config.DIARIOS


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    config.RESULTADOS.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
        "axes.spines.right": False, "axes.titlesize": 10, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "legend.frameon": False,
    })
    cifras = []
    def anota(t):
        cifras.append(t); print(t)

    c = pd.read_excel(CORPUS)
    c["fecha"] = pd.to_datetime(c.fecha, errors="coerce", utc=True).dt.tz_localize(None)
    k = pd.read_excel(CODIF)
    k["fecha"] = pd.to_datetime(k.fecha, errors="coerce", utc=True).dt.tz_localize(None)

    anota(f"corpus notas: {len(c)} | por diario {c.medio.value_counts().to_dict()} | con texto {c.texto_completo.notna().sum()}")
    anota(f"rango fechas: {c.fecha.min()} a {c.fecha.max()}")
    anota(f"menciones: {len(k)} | por diario {k.medio.value_counts().to_dict()} | notas con mención {k.link.nunique()}")

    # --- Figura 1: notas por trimestre y diario -------------------------------------------
    c["trim"] = c.fecha.dt.to_period("Q")
    t = c.groupby(["trim", "medio"]).size().unstack(fill_value=0).reindex(columns=DIARIOS, fill_value=0)
    t = t.reindex(pd.period_range(t.index.min(), t.index.max(), freq="Q"), fill_value=0)
    fig, ax = plt.subplots(figsize=(6.3, 2.8))
    x = np.arange(len(t))
    for d in DIARIOS:
        ax.plot(x, t[d], marker="o", ms=3, lw=1.6, color=COLOR[d], label=d)
    ax.set_xticks(x); ax.set_xticklabels([f"{p.year}\nT{p.quarter}" if p.quarter == 1 or i == 0 else f"T{p.quarter}" for i, p in enumerate(t.index)], fontsize=7)
    ax.set_ylabel("Notas"); ax.grid(axis="y", color="#e5e5e5"); ax.set_axisbelow(True)
    for i, p in enumerate(t.index):
        if str(p) == "2019Q4":
            ax.axvline(i, color="#888", lw=0.8, ls="--")
            ax.text(i + 0.15, 4, "asume el\nFrente de Todos", fontsize=6.5, color="#555")
    ax.legend(loc="upper left", ncol=2)
    ax.set_title("Notas por trimestre y diario")
    fig.tight_layout(); fig.savefig(SALIDA / "fig_notas_trimestre.pdf"); plt.close(fig)
    anota("notas por año: " + c.groupby([c.fecha.dt.year, "medio"]).size().unstack(fill_value=0).to_string().replace("\n", " ; "))
    pico = t.sum(axis=1).idxmax(); anota(f"trimestre pico: {pico} con {int(t.sum(axis=1).max())} notas")

    # El denominador de los porcentajes son las menciones de cada diario.
    # --- helpers ----------------------------------------------------------------------
    def explotar(col):
        s = k[[col, "medio", "fecha"]].copy()
        s[col] = s[col].fillna("").str.split(r"\s*\|\s*")
        s = s.explode(col)
        return s[s[col] != ""]

    n_menc = k.medio.value_counts()

    def barras_por_diario(col, titulo, archivo, etiquetas=None, alto=3.6):
        s = explotar(col)
        tab = s.groupby([col, "medio"]).size().unstack(fill_value=0).reindex(columns=DIARIOS, fill_value=0)
        pct = tab / n_menc[DIARIOS] * 100
        pct = pct.loc[pct.mean(axis=1).sort_values().index]
        fig, ax = plt.subplots(figsize=(6.3, alto))
        y = np.arange(len(pct)); h = 0.38
        for i, d in enumerate(DIARIOS):
            b = ax.barh(y + (0.5 - i) * h, pct[d], h, color=COLOR[d], label=f"{d} (n = {n_menc[d]:,} menciones)".replace(",", "."))
            for r, v, nn in zip(b, pct[d], tab.loc[pct.index, d]):
                ax.text(v + 0.6, r.get_y() + r.get_height() / 2, f"{v:.0f}% ({nn})", va="center", fontsize=6.5, color="#444")
        lab = [i.split(". ",1)[-1].replace(" / desarrollo productivo","").replace(" / seguridad","") for i in pct.index]
        ax.set_yticks(y); ax.set_yticklabels(lab, fontsize=7.5)
        ax.set_xlabel("% de las menciones de cada diario (entre paréntesis, conteo)", fontsize=7.5)
        ax.set_xlim(0, pct.values.max() * 1.3)
        ax.grid(axis="x", color="#e5e5e5"); ax.set_axisbelow(True)
        ax.legend(loc="lower right", fontsize=7.5); ax.set_title(titulo)
        fig.tight_layout(); fig.savefig(SALIDA / archivo); plt.close(fig)
        return tab, pct

    tab_m, pct_m = barras_por_diario("marcos_detectados", "Marcos de referencia por diario",
                                     "fig_marcos_diario.pdf", alto=4.4)
    anota("MARCOS conteo:\n" + tab_m.assign(total=tab_m.sum(axis=1)).sort_values("total", ascending=False).to_string())
    anota("MARCOS %:\n" + pct_m.round(1).to_string())
    tab_e, pct_e = barras_por_diario("tipo_emisor", "Tipo de emisor por diario",
                                     "fig_emisores_diario.pdf", alto=2.4)
    anota("EMISORES conteo:\n" + tab_e.assign(total=tab_e.sum(axis=1)).to_string())
    anota("EMISORES %:\n" + pct_e.round(1).to_string())
    anota(f"sin emisor: {k.tipo_emisor.isna().sum()} | sin marco: {k.marcos_detectados.isna().sum()}")
    anota("sin emisor por diario %: " + str((k.tipo_emisor.isna().groupby(k.medio).mean() * 100).round(1).to_dict()))

    # emisores individuales
    e = explotar("emisores_detectados")
    anota("TOP EMISORES:\n" + e.groupby(["emisores_detectados", "medio"]).size().unstack(fill_value=0)
          .reindex(columns=DIARIOS, fill_value=0).assign(total=lambda d: d.sum(axis=1))
          .sort_values("total", ascending=False).head(12).to_string())

    # --- Figura: marcos clave por año, un panel por marco, una línea por diario ----------------
    CLAVE = ["Trabajo / trabajadores", "Asistencia social", "Conflicto / seguridad / orden público"]
    NOMBRE = {CLAVE[0]: "Trabajo / trabajadores", CLAVE[1]: "Asistencia social", CLAVE[2]: "Conflicto / orden público"}
    k["anio"] = k.fecha.dt.year
    den = k.groupby(["anio", "medio"]).size().unstack(fill_value=0).reindex(columns=DIARIOS, fill_value=0)
    anota("menciones por año:\n" + den.to_string())
    fig, axs = plt.subplots(1, 3, figsize=(6.3, 2.4), sharey=False)
    for ax, m in zip(axs, CLAVE):
        tiene = k.marcos_detectados.fillna("").str.contains(m, regex=False)
        num = tiene.groupby([k.anio, k.medio]).sum().unstack(fill_value=0).reindex(columns=DIARIOS, fill_value=0)
        pc = num / den * 100
        for d in DIARIOS:
            ax.plot(pc.index, pc[d], marker="o", ms=3, lw=1.5, color=COLOR[d], label=d)
        ax.set_title(NOMBRE[m], fontsize=8.5); ax.set_xticks(pc.index); ax.set_xticklabels([str(a) for a in pc.index], fontsize=7, rotation=45)
        ax.set_ylim(0, max(5, pc.values.max() * 1.25)); ax.grid(axis="y", color="#e5e5e5"); ax.set_axisbelow(True)
        ax.tick_params(axis="y", labelsize=7)
        anota(f"{NOMBRE[m]} % por año:\n" + pc.round(1).to_string())
    axs[0].set_ylabel("% de las menciones del año", fontsize=7.5)
    axs[0].legend(fontsize=6.5, loc="lower left")
    fig.tight_layout(); fig.savefig(SALIDA / "fig_marcos_anio.pdf"); plt.close(fig)

    config.CIFRAS_INFORME.write_text("\n\n".join(cifras), encoding="utf-8")


if __name__ == "__main__":
    main()

"""Revisión manual de las 32 menciones cuyo fragmento nombra a ANSES.

Qué hace: agrega cuatro columnas a la codificación por diccionario, sin tocar
las originales: emisor_revisado, tipo_emisor_revisado, solo_nombre_revisado y
nota_revision. Las decisiones están escritas a mano en este archivo, y los
números de la lista son filas (empezando en 0) de fragmentos_codificados.xlsx.

Lee:    datos/derivados/fragmentos_codificados.xlsx
Genera: datos/derivados/fragmentos_codificados_revision_anses.xlsx

Cómo se corre, desde la carpeta del repositorio:
    python3 src/03b_revision_anses.py
"""
import pandas as pd

import config

ENTRADA, SALIDA = config.FRAGMENTOS_CODIFICADOS, config.REVISION_ANSES


def main():
    k = pd.read_excel(ENTRADA)

    # Lista cerrada: si cambian las filas, el assert de más abajo frena el script.
    MEDIO = "Voz del diario"
    T5 = "Otros / medios / academia"
    T1 = "Estatal"

    cita_anses = [536, 537, 538, 540, 548, 549, 550, 551, 552, 563, 577, 578, 580, 583, 589, 592]
    voz_diario_registro = [615, 665, 672, 682, 685, 686, 687, 1538]

    rev = {}
    for i in cita_anses:
        rev[i] = ("ANSES (cita textual del organismo)", T1, True,
                  "ANSES es quien habla, pero el término aparece solo dentro del nombre del Registro Nacional de "
                  "Trabajadores de la Economía Popular. Si las menciones 'solo nombre' se excluyen del análisis de "
                  "emisores, esta queda afuera.")
    for i in voz_diario_registro:
        rev[i] = (MEDIO, T5, True,
                  "La frase sobre compatibilidad con el registro la dice el diario, no la ANSES. Término solo como nombre del registro.")
    rev[88] = (MEDIO, T5, True,
               "El diario enumera a quienes participaron del relevamiento de barrios populares; la CTEP aparece solo por su nombre.")
    rev[802] = (MEDIO, T5, False,
                "El diario explica a quién va dirigido el bono: 'personas que se desempeñan en la llamada economía popular'. Uso conceptual.")
    rev[957] = ("Amado Boudou (asesor del ministro de Economía)", T1, False,
                "Boudou cuestiona que el 'modelo de economía popular' de Grabois sea peronista. Grabois es de quien se habla, no quien habla. "
                "Duda: Boudou podría codificarse como exfuncionario (Otros) según el criterio del equipo.")
    rev[1636] = ("Autor/a de la nota de opinión", T5, False,
                 "El autor de la columna usa el término para describir a los trabajadores informales.")
    rev[1846] = (MEDIO, T5, False, "El diario compara datos del RENATEP y del SIPA; ANSES solo aparece como fuente del SIPA.")
    rev[1847] = (MEDIO, T5, False, "El diario compara datos del RENATEP y del SIPA; ANSES solo aparece como fuente del SIPA.")
    for i in (1999, 2000):
        rev[i] = ("Autor/a de la columna, que escribe en nombre de las organizaciones de la EP", "Organizaciones y movimientos", False,
                  "Columna firmada: 'Las organizaciones de la Economía Popular seguiremos avanzando'. Completar el nombre del autor "
                  "(el fragmento se corta en '*Mil...'). Duda: según si se lo codifica como organización o como dirigente.")

    m = k.fragmento.fillna("").str.contains(r"\bANSES\b", case=False, regex=True)
    assert set(k[m].index) == set(rev), sorted(set(k[m].index) ^ set(rev))

    for col in ["emisor_revisado", "tipo_emisor_revisado", "solo_nombre_revisado", "nota_revision"]:
        k[col] = None
    for i, (e, t, s, n) in rev.items():
        k.loc[i, ["emisor_revisado", "tipo_emisor_revisado", "solo_nombre_revisado", "nota_revision"]] = [e, t, s, n]

    revisadas = k[m].copy()
    revisadas.insert(0, "fila", revisadas.index + 2)
    with pd.ExcelWriter(SALIDA) as w:
        revisadas[["fila", "medio", "fecha", "titulo", "fragmento", "emisores_detectados", "tipo_emisor",
                   "emisor_revisado", "tipo_emisor_revisado", "solo_nombre_revisado", "nota_revision", "link"]].to_excel(
            w, sheet_name="revision_anses", index=False)
        k.to_excel(w, sheet_name="fragmentos_codificados", index=False)

    print(revisadas.tipo_emisor_revisado.value_counts().to_string())
    print("solo nombre:", int(revisadas.solo_nombre_revisado.sum()), "de", len(revisadas))


if __name__ == "__main__":
    main()

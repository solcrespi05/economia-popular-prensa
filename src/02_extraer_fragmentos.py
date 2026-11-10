"""
Extracción automática de fragmentos alrededor de cada mención de
"economía popular" - primer paso para la codificación de quién nombra el
término y con qué connotación.

Por qué existe este script: según lo que definimos con el proyecto, la
codificación final (tipo de actor, sentido/marco) necesita un codebook
que todavía hay que armar con Gabriela. Pero juntar cada mención
con su contexto - y una primera pista automática de quién podría estar
hablando ahí - no depende de ese codebook y sirve para tener el material
ya recortado y listo cuando se haga la codificación manual.

Qué hace, para cada mención de "economía popular" en el texto completo:
1. Recorta un fragmento de contexto alrededor (antes y después).
2. Busca un verbo de atribución de discurso cerca ("afirmó", "sostuvo",
   "señaló", etc.) - si aparece uno, es señal de que alguien está siendo
   citado o parafraseado ahí, no que es la voz del propio medio.
3. Busca el nombre propio más cercano (heurística simple de mayúsculas,
   NO es NER real) como actor candidato - hay que confirmarlo a mano.

El punto 3 no reemplaza la codificación cualitativa con codebook - es
una pista para acelerarla, no la respuesta.

Lee:    datos/crudos/corpus_economia_popular_avance.xlsx
Genera: datos/derivados/fragmentos_economia_popular.xlsx (una fila por mención)

Cómo se corre, desde la carpeta del repositorio:
    python3 src/02_extraer_fragmentos.py
"""

import re

import pandas as pd

import config

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

RUTA_CORPUS = config.CORPUS
RUTA_SALIDA = config.FRAGMENTOS

# Admite singular/plural y la falta de tilde; es la definición de "mención".
PATRON_MENCION = re.compile(r"econom[ií]as?\s+popular(?:es)?", re.IGNORECASE)

# Caracteres de contexto antes/después de cada mención (~2-3 oraciones)
VENTANA_CHARS = 300

# Verbos de atribución de discurso: si aparecen cerca de la mención, es
# señal de que alguien está siendo citado o parafraseado ahí.
VERBOS_ATRIBUCION = [
    "dijo", "afirmó", "sostuvo", "señaló", "indicó", "aseguró", "explicó",
    "consideró", "planteó", "advirtió", "remarcó", "subrayó", "destacó",
    "manifestó", "opinó", "sugirió", "definió", "describió", "criticó",
    "denunció", "reclamó", "pidió", "propuso", "anunció", "declaró",
    "expresó", "resaltó", "insistió", "reconoció", "admitió",
]
PATRON_ATRIBUCION = re.compile(r"\b(" + "|".join(VERBOS_ATRIBUCION) + r")\b", re.IGNORECASE)

# Nombre propio candidato: secuencia de 2+ palabras con mayúscula inicial.
# Heurística simple (no es NER), pensada para acotar quién puede estar
# hablando - hay que confirmarlo a mano en la codificación.
PATRON_NOMBRE_PROPIO = re.compile(
    r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\b"
)


# ---------------------------------------------------------------------------
# EXTRACCIÓN
# ---------------------------------------------------------------------------

def _ventana(texto, inicio, fin):
    desde = max(0, inicio - VENTANA_CHARS)
    hasta = min(len(texto), fin + VENTANA_CHARS)
    return texto[desde:hasta].replace("\n", " ").strip(), desde


def _actor_candidato(fragmento, pos_mencion_en_fragmento):
    """Heurística: si hay un verbo de atribución cerca, preferimos el
    nombre propio que aparece ANTES de ese verbo (patrón típico:
    "Fulano afirmó que la economía popular..."). Si no hay verbo,
    devolvemos el nombre propio más cercano a la mención como candidato
    débil (menos confiable, hay que revisar a mano)."""
    m_verbo = PATRON_ATRIBUCION.search(fragmento)
    nombres = list(PATRON_NOMBRE_PROPIO.finditer(fragmento))
    if not nombres:
        return None, (m_verbo.group(1) if m_verbo else None)

    if m_verbo:
        antes_del_verbo = [n for n in nombres if n.start() < m_verbo.start()]
        if antes_del_verbo:
            return antes_del_verbo[-1].group(1), m_verbo.group(1)

    mas_cercano = min(nombres, key=lambda n: abs(n.start() - pos_mencion_en_fragmento))
    return mas_cercano.group(1), (m_verbo.group(1) if m_verbo else None)


def extraer_fragmentos(df):
    filas = []
    for _, art in df.iterrows():
        texto = art.get("texto_completo")
        if not isinstance(texto, str) or not texto.strip():
            continue
        for m in PATRON_MENCION.finditer(texto):
            fragmento, desde = _ventana(texto, m.start(), m.end())
            pos_relativa = m.start() - desde
            actor, verbo = _actor_candidato(fragmento, pos_relativa)
            filas.append({
                "medio": art.get("medio"),
                "titulo": art.get("titulo"),
                "fecha": art.get("fecha"),
                "seccion": art.get("seccion"),
                "link": art.get("link"),
                "mencion_textual": m.group(0),
                "fragmento": fragmento,
                "actor_candidato": actor,
                "verbo_atribucion": verbo,
            })
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print(f"Leyendo corpus desde: {RUTA_CORPUS}")
    df = pd.read_excel(RUTA_CORPUS)

    fragmentos = extraer_fragmentos(df)
    print(f"\nTotal de menciones encontradas: {len(fragmentos)} (en {df['texto_completo'].notna().sum()} notas con texto)")

    fragmentos.to_excel(RUTA_SALIDA, index=False)
    print(f"Guardado en: {RUTA_SALIDA}")

    print("\n" + "=" * 60)
    print("PARA LA REUNIÓN - pantallazo rápido (todo esto es provisorio)")
    print("=" * 60)

    print("\nMenciones con verbo de atribución cerca (posible cita/parafraseo):")
    con_verbo = fragmentos["verbo_atribucion"].notna().sum()
    print(f"  {con_verbo} de {len(fragmentos)} ({con_verbo / len(fragmentos):.1%})" if len(fragmentos) else "  (sin datos)")

    print("\nActores candidatos más frecuentes (heurística, revisar a mano):")
    print(fragmentos["actor_candidato"].value_counts().head(15).to_string())

    print(
        "\nOjo: 'actor_candidato' es una pista automática para priorizar la "
        "lectura, no la codificación final. Esa codificación (tipo de actor, "
        "sentido/marco) se hace con el codebook del proyecto (ver "
        "analisis_emisores_marcos.py) o leyendo la nota completa."
    )


if __name__ == "__main__":
    main()

"""
Tarea 1 y Tarea 2 del codebook: emisores y marcos de referencia de
"economía popular", según la taxonomía de Daniela (documento de
metodología: tipo de emisor + objeto directo / marco de referencia).

Tarea 1: para cada mención de "economía popular" (con su fragmento de
contexto, el mismo que arma extraer_fragmentos.py), detectar qué emisores
aparecen y clasificarlos en los 5 tipos del codebook:
    Estatal                      (a Presidente, b Área social/desarrollo,
                                     c Área económica/laboral,
                                     d Subnacional, e Otros poderes)
    Organizaciones y movimientos (a UTEP y sus organizaciones,
                                     b Patria Grande, c Izquierda/no alineadas,
                                     d Sindicatos tradicionales)
    Dirigentes sociales
    Sector privado / empresarial
    Otros / medios / academia    (incluye las notas de opinión/editoriales)

Tarea 2: para cada mención, detectar cuáles de los 16 marcos de referencia
aparecen en el mismo fragmento y cruzar emisor x marco.

Es una codificación por diccionario (búsqueda de nombres/frases, no NLP/NER
real): manual y transparente a propósito, para que se pueda auditar y
corregir el listado de patrones. Los patrones tolerantes a tildes y
mayúsculas ("Pérsico" = "persico" = "PÉRSICO"). Es un primer corte
cuantitativo, no un reemplazo de la lectura de los casos dudosos.

Lee:    datos/derivados/fragmentos_economia_popular.xlsx
Genera, en datos/derivados/:
    - fragmentos_codificados.xlsx   (una fila por mención, con las columnas
      emisores_detectados / tipo_emisor / subtipo_emisor / marcos_detectados)
    - tabla_emisores_marcos.xlsx    (hojas: tipo_x_marco, subtipo_x_marco,
      emisor_x_marco - el resultado de la Tarea 2)

Cómo se corre, desde la carpeta del repositorio:
    python3 src/03_codificacion_diccionario.py

Se puede importar sin que se ejecute la codificación: los scripts 04 y 05
toman de acá las etiquetas válidas (EMISORES, TIPOS y MARCOS).
"""

import re

import pandas as pd

import config

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

RUTA_FRAGMENTOS = config.FRAGMENTOS
RUTA_SALIDA_FRAGMENTOS = config.FRAGMENTOS_CODIFICADOS
RUTA_SALIDA_TABLA = config.TABLA_EMISORES_MARCOS

SEP = " | "


# ---------------------------------------------------------------------------
# HELPERS DE PATRONES
# ---------------------------------------------------------------------------

_TILDES = {"a": "[aáà]", "e": "[eéè]", "i": "[iíì]", "o": "[oóò]", "u": "[uúü]"}


def tol(frase):
    """Frase literal -> regex tolerante a tildes y a espacios múltiples, con
    límites de palabra. 'Persico' matchea 'Pérsico'."""
    partes = []
    for ch in frase.lower():
        if ch == " ":
            partes.append(r"\s+")
        elif ch in _TILDES:
            partes.append(_TILDES[ch])
        else:
            partes.append(re.escape(ch))
    return r"\b" + "".join(partes) + r"\b"


def N(*frases):
    """Varios términos literales -> un solo patrón. Si empieza con 're:' se
    toma como regex crudo (para raíces, plurales y exclusiones)."""
    return [f[3:] if f.startswith("re:") else tol(f) for f in frases]


def compilar(patrones):
    return re.compile("|".join(patrones), re.IGNORECASE)


# ---------------------------------------------------------------------------
# TAREA 1 - EMISORES (taxonomía de Daniela)
# ---------------------------------------------------------------------------

T1 = "Estatal"
T2 = "Organizaciones y movimientos"
T3 = "Dirigentes sociales"
T4 = "Sector privado"
T5 = "Otros / medios / academia"

TIPOS = [T1, T2, T3, T4, T5]

S1A = "Presidente"
S1B = "Ejecutivo nacional - Área social/desarrollo"
S1C = "Ejecutivo nacional - Área económica/laboral"
S1D = "Ejecutivo subnacional"
S1E = "Otros poderes del Estado"
S2A = "UTEP y sus organizaciones"
S2B = "Patria Grande"
S2C = "Organizaciones de izquierda / no alineadas"
S2D = "Sindicatos tradicionales"

# nombre canónico -> (tipo, subtipo, patrones)
EMISORES = {
    # --- ESTATAL ---------------------------------------------------------
    "Presidente de la Nación": (T1, S1A, N(
        "Alberto Fernández", "Mauricio Macri", "Presidencia de la Nación",
        # "el presidente" a secas; se excluye "el presidente de la UTEP/Cámara..."
        r"re:\bel\s+presidente\b(?!\s+(?:de|del)\s+(?!la\s+naci[oó]n))",
        "Gobierno nacional", "Casa Rosada",
    )),
    "Ministerio de Desarrollo Social / Economía Social": (T1, S1B, N(
        "Daniel Arroyo", "Arroyo", "Juan Zabaleta",
        "Ministerio de Desarrollo Social", "ministro de Desarrollo Social",
        "ministra de Desarrollo Social", "Secretaría de Economía Social",
        "secretario de Economía Social", "Secretaría de Economía Popular",
        "Alexandre Roig", "INAES",
        "Instituto Nacional de Asociativismo y Economía Social",
    )),
    "Ministerio de Trabajo / Economía": (T1, S1C, N(
        "Claudio Moroni", "Moroni", "Ministerio de Trabajo",
        "ministro de Trabajo", "ministra de Trabajo",
        "Ministerio de Economía", "ministro de Economía",
        "ministra de Economía", "Ministerio de Hacienda",
    )),
    "Gobierno subnacional (provincias y municipios)": (T1, S1D, N(
        "gobernador", "gobernadora", "intendente", "intendenta",
        "jefe de Gobierno", "Axel Kicillof", "Kicillof",
        "Horacio Rodríguez Larreta", "Rodríguez Larreta",
        "Gobierno porteño", "Gobierno bonaerense", "Gobierno de la Ciudad",
        "Gobierno de la Provincia", "Municipalidad",
    )),
    "Poder Legislativo / Judicial": (T1, S1E, N(
        "Congreso", "Senado", "Cámara de Diputados", "diputado", "diputada",
        "senador", "senadora", "legislador", "legisladora", "Corte Suprema",
        "juez", "jueza", "Poder Judicial", "Poder Legislativo",
    )),

    # --- ORGANIZACIONES Y MOVIMIENTOS SOCIALES / SINDICALES ---------------
    "UTEP / CTEP": (T2, S2A, N(
        "UTEP", "CTEP",
        r"re:\buni[oó]n\s+de\s+trabajadores(?:\s+y\s+trabajadoras)?\s+de\s+la\s+econom[ií]a\s+popular\b",
        r"re:\bconfederaci[oó]n\s+de\s+trabajadores(?:\s+y\s+trabajadoras)?\s+de\s+la\s+econom[ií]a\s+popular\b",
    )),
    "Movimiento Evita": (T2, S2A, N("Movimiento Evita", "Agrupación Evita")),
    "Barrios de Pie": (T2, S2A, N("Barrios de Pie", "Somos Barrios de Pie")),
    "Otras organizaciones de la UTEP": (T2, S2A, N(
        "Movimiento de Trabajadores Excluidos", "MTE",
        "Corriente Clasista y Combativa", "Frente Popular Darío Santillán",
        "Frente Darío Santillán", "Movimiento Octubres",
        "Movimiento Nacional Campesino Indígena", "MNCI",
        "Nuestra América", "Organizaciones Libres del Pueblo",
        "Federación de Organizaciones de Base", "Movimiento Popular La Dignidad",
        "Corriente Popular Eva Perón", "Misioneros de Francisco",
        "Movimiento de Inclusión Popular", "Movimiento Nacional de Empresas Recuperadas",
        "Federación Nacional Campesina", "Frente de Organizaciones Populares",
        "Frente Barrial 19 de Diciembre", "Movimiento Popular Los Pibes",
        "Federación Argentina de Cartoneros, Carreros y Recicladores", "FACCYR",
        "Movimiento Social 17 de Noviembre", "Frente Nacional Néstor Kirchner",
    )),
    "Frente Patria Grande": (T2, S2B, N("Frente Patria Grande", "Patria Grande")),
    "Organizaciones de izquierda / no alineadas": (T2, S2C, N(
        "Polo Obrero", "Movimiento Socialista de los Trabajadores", "MST",
        "Unidad Piquetera", "Barrios de Pie Libres del Sur",
        "Frente de Izquierda", "Partido Obrero",
    )),
    "Sindicatos tradicionales (CGT / CTA)": (T2, S2D, N(
        "CGT", "Confederación General del Trabajo", "CTA",
        "CTA de los Trabajadores", "CTA Autónoma", "CTA-T", "CTA-A",
    )),

    # --- DIRIGENTES SOCIALES ---------------------------------------------
    # Las personas van acá (no en la organización), aunque el documento
    # también nombra a Grabois y Castro dentro de Patria Grande.
    "Juan Grabois": (T3, "Dirigente social", N("Juan Grabois", "Grabois")),
    "Emilio Pérsico": (T3, "Dirigente social", N("Emilio Pérsico", "Pérsico")),
    "Esteban \"Gringo\" Castro": (T3, "Dirigente social", N(
        "Esteban Castro", "Gringo Castro", "Esteban \"Gringo\" Castro",
        "Esteban “Gringo” Castro",
    )),
    "Alejandro \"Peluca\" Gramajo": (T3, "Dirigente social", N(
        "Alejandro Gramajo", "Peluca Gramajo", "Gramajo",
    )),
    "Fernando \"Chino\" Navarro": (T3, "Dirigente social", N(
        "Fernando Navarro", "Chino Navarro", "Fernando Chino Navarro",
    )),
        "Daniel Menéndez": (T3, "Dirigente social", N("Daniel Menéndez", "Menéndez")),
    "Eduardo \"Chiquito\" Belliboni": (T3, "Dirigente social", N(
        "Eduardo Belliboni", "Chiquito Belliboni", "Belliboni",
    )),
    "Fernanda Miño": (T3, "Dirigente social", N("Fernanda Miño")),

    # --- SECTOR PRIVADO / EMPRESARIAL ------------------------------------
    "Cámaras y entidades empresarias": (T4, "Sector privado / empresarial", N(
        "UIA", "Unión Industrial Argentina", "CAME",
        "Confederación Argentina de la Mediana Empresa", "Sociedad Rural",
        "Cámara Argentina de Comercio", "Cámara Argentina de la Construcción",
        "Coninagro", "Confederaciones Rurales", "Federación Agraria",
        "Asociación Empresaria", "cámara empresaria", "cámaras empresarias",
        "empresario", "empresaria", "empresarios", "empresarias",
        "Consejo Interamericano de Comercio","cámara empresarial", "cámaras empresariales",
    )),

    # --- OTROS / MEDIOS / ACADEMIA ---------------------------------------
    "Expertos y academia": (T5, "Academia / expertos", N(
        "especialista", "especialistas", "investigador", "investigadora",
        "investigadores", "economista", "economistas", "sociólogo",
        "socióloga", "politólogo", "politóloga", "académico", "académica",
        "analista", "analistas", "CONICET", "Universidad", "consultora",
        "Observatorio",
    )),
    "Iglesia / Papa Francisco": (T5, "Otros", N(
        "Papa Francisco", "Iglesia", "Pastoral Social", "Cáritas",
    )),
}

# Emisor "de prensa": se detecta por la sección o la URL de la nota, no por
# el texto del fragmento.
EMISOR_EDITORIAL = "Nota de opinión / editorial"
EMISORES[EMISOR_EDITORIAL] = (T5, "Medios / notas editoriales", [])
PATRON_EDITORIAL = re.compile(r"opini[oó]n|editorial|columnista|/opinion/", re.IGNORECASE)

EMISORES_COMPILADOS = {
    nombre: compilar(pats) for nombre, (_t, _s, pats) in EMISORES.items() if pats
}


# ---------------------------------------------------------------------------
# TAREA 2 - MARCOS DE REFERENCIA (los 16 de Daniela)
# ---------------------------------------------------------------------------
# Trabajo, Asistencia, Informalidad, Conflicto e Integración son categorías "paraguas": se detectan por cualquiera de
# los términos que el documento lista en "Comprende".

MARCOS = {
    "Organizaciones de la economía popular": N(
        "organizaciones de la economía popular", "organización de la economía popular",
        "organizaciones sociales", "organización social", "organizaciones populares",
        "organizaciones de la economía social", "organización de la economía social",
    ),
    "Movimientos sociales": N(
        "movimientos sociales", "movimiento social", "movimientos populares",
    ),
    "Sector": [
        # "sector" suelto, sin los usos que no son el sector de la EP
        r"\bsector(?:es)?\b(?!\s+(?:privado|p[uú]blico|agropecuario|financiero|energ[eé]tico|empresari\w+|industrial|exportador))",
    ],
    "Políticas sociales y laborales": N(
        "política social", "políticas sociales", "política laboral",
        "políticas laborales", "política de empleo", "políticas de empleo",
        "políticas públicas", "política pública",
    ),
    "Trabajadores informales": N(
        "trabajador informal", "trabajadores informales", "trabajadora informal",
        "trabajadoras informales", "informales",
        "desocupado", "desocupados", "desocupada", "desocupadas", "sin empleo",
"trabajador en negro", "trabajadores en negro", "trabajadora en negro", "trabajadoras en negro",
    ),
    "Pobres": [r"\bpobres?\b", r"\bpobreza\b", r"\bindigen\w+"],
    "Humildes": [r"\bhumildes?\b", r"\blos\s+m[aá]s\s+necesitados\b", r"\bsectores?\s+m[aá]s\s+postergados?\b"],
    "Piqueteros": [r"\bpiquetero\w*"],
    "Derechos": [r"\bderechos\b"],
    "IFE": N("IFE", "Ingreso Familiar de Emergencia"),
    "Potenciar Trabajo": N("Potenciar Trabajo"),
    "Trabajo / trabajadores": N(
        "trabajador por cuenta propia", "trabajadores por cuenta propia",
        "trabajadora por cuenta propia", "trabajador de la economía popular",
        "trabajadores de la economía popular", "trabajadora de la economía popular",
        "trabajadores y trabajadoras de la economía popular",
        "trabajador de la economía social", "trabajadores de la economía social",
        "productor de la economía popular", "productores de la economía popular",
        "agricultor familiar", "agricultores familiares", "agricultura familiar",
        "cartonero", "cartoneros", "cartonera", "cartoneras",
        "cooperativa", "cooperativas", "unidad productiva", "unidades productivas",
        "autogestión", "economía social y solidaria", "economía social",
        "economía solidaria", "inventan su propio trabajo", "inventores de su propio trabajo",
        "changarín", "changarines", "trabajador golondrina", "trabajadores golondrina",
        "artesano", "artesanos", "artesana", "artesanas",
        "empresa recuperada", "empresas recuperadas", "fábrica recuperada",
        "fábricas recuperadas",
        # "trabajador(es)" suelto, pero sin contar el nombre de la UTEP/CTEP
        # ("Unión/Confederación de Trabajadores de la Economía Popular")
        r"re:(?<!\bde\s)\btrabajador(?:es|a|as)?\b(?!\s+(?:y\s+trabajadoras\s+)?de\s+la\s+econom)",
        "vendedores ambulantes", "vendedor ambulante", "vendedora ambulante",
        r"re:\btrabajador(?:es|a|as)?\s+(?:de|en)\s+(?:los\s+)?(?:comedor|merendero)\w*",

    ),
    "Asistencia social": N(
        "plan social", "planes sociales", "Potenciar Trabajo", "subsidio",
        "subsidios", "asistencia", "asistencial", "asistencialismo", "contención",
        "tarjeta alimentar", "Tarjeta Alimentar", "comedor", "comedores",
        "merendero", "merenderos", "vulnerabilidad", "población vulnerable",
        "ayuda del Estado", "ayudas del Estado","beneficiario", "beneficiarios", "beneficiaria", "beneficiarias",
        r"re:\btitulares?\s+de\s+(?:programas|planes)\s+sociales\b",
    ),
    "Informalidad / precarización": N(
        "trabajo no registrado", "trabajo en negro", "trabajador informal",
        "trabajadores informales", "informalidad", "informalidad laboral",
        "marginalidad", "economía no formal", "economía informal", "changa",
        "changas", "precariedad laboral", "precarización", "precariedad",
        "subempleo", "venta ambulante", "vendedores ambulantes",
        "vendedor ambulante", "vendedora ambulante",
        "desocupación",
    ),
    "Conflicto / seguridad / orden público": [
        r"\bpiquet\w*", r"\bprotestas?\b", r"\bmovilizaci[oó]n(?:es)?\b",
        r"\bacampes?\b", r"\bintermediaci[oó]n\b", r"(?<!en\s)\bmarchas?\b",
        r"\bocupaci[oó]n(?:es)?\b", r"\bcortes?\s+de\s+(?:calle|ruta)s?\b",
        r"\bmanifestaci[oó]n(?:es)?\b",
    ],
    "Integración económica / desarrollo productivo": N(
        "RENATEP", "Registro Nacional de Trabajadores de la Economía Popular",
        "monotributo social", "salario social complementario",
        "acceso al crédito", "crédito", "créditos", "compras estatales",
        "compre estatal", "cadena de valor", "cadenas de valor",
        "inclusión financiera", "herramientas productivas",
        "desarrollo productivo", "fondo de capital social",
    ),
}

MARCOS_COMPILADOS = {nombre: compilar(pats) for nombre, pats in MARCOS.items()}


# ---------------------------------------------------------------------------
# DETECCIÓN
# ---------------------------------------------------------------------------

def _es_editorial(fila):
    texto = " ".join(str(fila.get(c) or "") for c in ("seccion", "link"))
    return bool(PATRON_EDITORIAL.search(texto))


# Nombres propios que ya contienen el término "economía popular": si solo aparecen como
# nombre completo, no cuentan como emisor (la sigla UTEP/CTEP u otro nombre sí).
PATRON_NOMBRE_CON_TERMINO = re.compile(
    r"(?:uni[oó]n|confederaci[oó]n)\s+de\s+trabajadores(?:\s+y\s+trabajadoras)?\s+de\s+la\s+econom[ií]as?\s+popular(?:es)?"
    r"|registro\s+nacional\s+de\s+trabajadores(?:\s+y\s+trabajadoras)?\s+de\s+la\s+econom[ií]as?\s+popular(?:es)?"
    r"|secretar[ií]a\s+de\s+econom[ií]a\s+popular",
    re.IGNORECASE,
)


def detectar_emisores(fragmento, fila=None):
    """Devuelve la lista de emisores encontrados en el fragmento (más el
    emisor editorial si la nota es de opinión). El nombre completo de una
    organización que contiene el término no cuenta como emisor por sí solo."""
    encontrados = []
    if isinstance(fragmento, str):
        limpio = PATRON_NOMBRE_CON_TERMINO.sub(" ", fragmento)
        encontrados = [n for n, p in EMISORES_COMPILADOS.items() if p.search(limpio)]
    if fila is not None and _es_editorial(fila):
        encontrados.append(EMISOR_EDITORIAL)
    return encontrados


def tipos_y_subtipos(emisores):
    tipos = [t for t in TIPOS if any(EMISORES[e][0] == t for e in emisores)]
    subtipos = sorted({EMISORES[e][1] for e in emisores})
    return tipos, subtipos


# El marco Trabajo / trabajadores se busca sin los nombres propios que contienen
# "Trabajadores de la Economía Popular" (UTEP, CTEP, RENATEP): si no, el nombre de la
# organización activa el marco aunque la nota no hable de trabajo. Los demás marcos se
# buscan sobre el fragmento completo (Integración usa el nombre del RENATEP a propósito).
MARCOS_SIN_NOMBRES = {"Trabajo / trabajadores"}


def detectar_marcos(fragmento):
    if not isinstance(fragmento, str):
        return []
    limpio = PATRON_NOMBRE_CON_TERMINO.sub(" ", fragmento)
    return [n for n, p in MARCOS_COMPILADOS.items()
            if p.search(limpio if n in MARCOS_SIN_NOMBRES else fragmento)]


def codificar(df):
    filas = []
    for _, fila in df.iterrows():
        emisores = detectar_emisores(fila.get("fragmento"), fila)
        tipos, subtipos = tipos_y_subtipos(emisores)
        marcos = detectar_marcos(fila.get("fragmento"))
        filas.append({
            **fila.to_dict(),
            "emisores_detectados": SEP.join(emisores) if emisores else None,
            "tipo_emisor": SEP.join(tipos) if tipos else None,
            "subtipo_emisor": SEP.join(subtipos) if subtipos else None,
            "marcos_detectados": SEP.join(marcos) if marcos else None,
        })
    return pd.DataFrame(filas)


def _tiene(serie, valor):
    """Serie booleana: la celda (lista unida con ' | ') contiene `valor`
    como elemento exacto."""
    return serie.fillna("").apply(lambda s: valor in s.split(SEP)).astype(bool)


def _cruce(df_cod, columna, valores, extra=None):
    filas = []
    for v in valores:
        sub = df_cod[_tiene(df_cod[columna], v)]
        fila = {columna: v, **(extra(v) if extra else {}), "total_menciones": len(sub)}
        for marco in MARCOS:
            fila[marco] = int(_tiene(sub["marcos_detectados"], marco).sum())
        filas.append(fila)
    return pd.DataFrame(filas)


def tabla_cruce(df_cod):
    """Tarea 2. Devuelve tres tablas emisor x marco, a distinto nivel:
    por tipo, por subtipo y por emisor individual."""
    subtipos = [s for s in dict.fromkeys(EMISORES[e][1] for e in EMISORES)]
    por_tipo = _cruce(df_cod, "tipo_emisor", TIPOS)
    por_subtipo = _cruce(
        df_cod, "subtipo_emisor", subtipos,
        extra=lambda s: {"tipo": next(EMISORES[e][0] for e in EMISORES if EMISORES[e][1] == s)},
    )
    por_emisor = _cruce(
        df_cod, "emisores_detectados", list(EMISORES),
        extra=lambda e: {"tipo": EMISORES[e][0], "subtipo": EMISORES[e][1]},
    )
    por_emisor = por_emisor.rename(columns={"emisores_detectados": "emisor"})
    por_subtipo = por_subtipo.rename(columns={"subtipo_emisor": "subtipo"})
    por_tipo = por_tipo.rename(columns={"tipo_emisor": "tipo"})
    return por_tipo, por_subtipo, por_emisor


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print(f"Leyendo fragmentos desde: {RUTA_FRAGMENTOS}")
    df = pd.read_excel(RUTA_FRAGMENTOS)

    df_codificado = codificar(df)
    n = len(df_codificado)
    con_emisor = df_codificado["emisores_detectados"].notna().sum()
    con_marco = df_codificado["marcos_detectados"].notna().sum()
    print(f"\nTotal de menciones: {n}")
    print(f"Con al menos un emisor detectado: {con_emisor} ({con_emisor / n:.1%})")
    print(f"Con al menos un marco detectado: {con_marco} ({con_marco / n:.1%})")

    df_codificado.to_excel(RUTA_SALIDA_FRAGMENTOS, index=False)
    print(f"Guardado: {RUTA_SALIDA_FRAGMENTOS}")

    por_tipo, por_subtipo, por_emisor = tabla_cruce(df_codificado)

    print("\nMenciones por tipo de emisor:")
    print(por_tipo[["tipo", "total_menciones"]].to_string(index=False))
    print("\nMenciones por emisor:")
    print(por_emisor.sort_values("total_menciones", ascending=False)[
        ["emisor", "tipo", "total_menciones"]].to_string(index=False))
    print("\nMenciones por marco:")
    print(pd.Series({m: int(_tiene(df_codificado["marcos_detectados"], m).sum())
                     for m in MARCOS}).sort_values(ascending=False).to_string())

    print("\n" + "=" * 60)
    print("TAREA 2 - cruce tipo de emisor x marco")
    print("=" * 60)
    with pd.ExcelWriter(RUTA_SALIDA_TABLA) as w:
        por_tipo.to_excel(w, sheet_name="tipo_x_marco", index=False)
        por_subtipo.to_excel(w, sheet_name="subtipo_x_marco", index=False)
        por_emisor.to_excel(w, sheet_name="emisor_x_marco", index=False)
    print(f"Guardado: {RUTA_SALIDA_TABLA}")
    print(por_tipo.to_string(index=False))

    print(
        "\nOjo: esto es codificación por diccionario, no NLP real. Los patrones "
        "genéricos (sector, derechos, asistencia, marcha, trabajador, "
        "empresarios, Universidad, Francisco, 'el presidente') pueden traer "
        "falsos positivos - conviene revisar a mano los casos de mayor volumen "
        "antes de citarlos como definitivos."
    )


if __name__ == "__main__":
    main()

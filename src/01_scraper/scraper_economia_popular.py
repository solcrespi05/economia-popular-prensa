"""
Scraper completo - Página/12 + La Nación - "economía popular" (2019-2023)

Cómo funciona cada medio:

- PÁGINA/12: se consulta directamente la API interna de búsqueda (Solr),
  y para cada nota se trae el texto completo desde
  window.Fusion.globalContent (el dato ya viene en el HTML/JS de la
  página, más allá del paywall visual).

- LA NACIÓN: no tiene una API de búsqueda tan fácil de encontrar, así que
  se recolectan los links igual que en la primera versión del scraper
  (recorriendo el buscador con scroll/"Cargar más" y juntando todos los
  links de notas que aparecen en la página). Ese método junta también
  links que no son de la búsqueda (notas relacionadas, recomendadas, etc.)
  - por eso, en vez de tratar de "apuntar" al contenedor exacto de
  resultados, el filtro se hace DESPUÉS: se le trae el texto completo a
  CADA link candidato con la sesión de la suscripción de La Nación (misma lógica de
  window.Fusion.globalContent, porque La Nación usa la misma plataforma
  que Página/12), y al final nos quedamos solo con las notas cuyo texto
  realmente contiene "economía popular". Así el ruido se descarta solo.

Requisitos:
    pip install playwright pandas openpyxl
    playwright install chromium

Lee:    checkpoints/ (si existen) y sesion_lanacion.json (ver capturar_sesion.py)
Genera: datos/crudos/corpus_economia_popular.xlsx y los checkpoints

Cómo se corre, desde la carpeta del repositorio (OJO: vuelve a recolectar):
    python3 src/01_scraper/scraper_economia_popular.py

Los checkpoints (carpeta checkpoints/) permiten cortar y retomar en
cualquier etapa sin perder lo ya hecho ni repetir pedidos innecesarios.
"""

import asyncio
import json
import re
import time
import urllib.request
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.parse import quote, quote_plus

import sys

import pandas as pd
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

# ---------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------------------------------

QUERY = "economía popular"
FECHA_DESDE = datetime(2019, 9, 1)
FECHA_HASTA = datetime(2023, 9, 30)

HEADLESS = True  # obligatorio en Colab, no hay pantalla
DELAY_ENTRE_ARTICULOS = 1.5

PROCESAR_PAGINA12 = True
PROCESAR_LANACION = True

# Frenos de seguridad para probar antes de correr todo:
#   None = sin límite (correr todo)
#   un número = cortar ahí, para probar rápido
MAX_LINKS_LANACION_RECOLECCION = None   # tope al juntar links del buscador

# --- La Nación: solo con la sesión de la suscripción ---
# Necesita sesion_lanacion.json en la carpeta del proyecto (ver Paso 3b).
ARCHIVO_SESION_LANACION = config.SESION_LANACION
MAX_LANACION_LOGUEADO = 1500   # notas por corrida (None = todas las pendientes)
DELAY_LOGUEADO = 2.5          # segundos entre notas; no conviene bajarlo
MAX_INTENTOS_LOGUEADO = 3     # una nota que falla 3 veces se deja de reintentar
FALLOS_SEGUIDOS_PARA_CORTAR = 8

OUTPUT_XLSX = config.CORPUS_SCRAPER
CHECKPOINT_DIR = config.CHECKPOINTS
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
    "(investigacion academica UNSAM - economia popular - "
    "contacto: revisar con Gabriela Delamata)"
)

PATRON_MENCION = re.compile(r"econom[ií]as?\s+popular(?:es)?", re.IGNORECASE)


# ---------------------------------------------------------------------------
# CHECKPOINTS (genérico)
# ---------------------------------------------------------------------------

def guardar_checkpoint(nombre, data):
    ruta = CHECKPOINT_DIR / nombre
    ruta.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cargar_checkpoint(nombre, default=None):
    ruta = CHECKPOINT_DIR / nombre
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    return default if default is not None else {}


# ---------------------------------------------------------------------------
# UTILIDADES COMUNES
# ---------------------------------------------------------------------------

def _limpiar_html(texto):
    if not texto:
        return texto
    sin_tags = re.sub(r"<[^>]+>", "", texto)
    return unescape(sin_tags).strip()


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
    """Filtro de contenido: ¿esta nota realmente habla de "economía
    popular"? Se usa para descartar el ruido que trae la recolección de
    links de La Nación (notas relacionadas/recomendadas que no tienen
    nada que ver con la búsqueda)."""
    campos = [articulo.get("texto_completo"), articulo.get("titulo"), articulo.get("volanta_bajada")]
    for campo in campos:
        if campo and PATRON_MENCION.search(campo):
            return True
    return False


# ---------------------------------------------------------------------------
# PÁGINA/12 - búsqueda vía API interna
# ---------------------------------------------------------------------------

PAGINA12_API_URL = "https://www.pagina12.com.ar/pf/api/v3/content/fetch/p12-solr-search"
PAGINA12_TAMANO_PAGINA = 100


def _armar_url_busqueda_pagina12(query, offset):
    query_obj = {
        "author": "", "endDate": "", "offset": offset,
        "page": offset // PAGINA12_TAMANO_PAGINA,
        "q": f'"{query}"',
        "section": "", "size": PAGINA12_TAMANO_PAGINA, "startDate": "",
    }
    qs = quote_plus(json.dumps(query_obj, ensure_ascii=False, separators=(",", ":")))
    return f"{PAGINA12_API_URL}?query={qs}&d=132&mxId=00000000&_website=pagina12"


def _campo_basic(valor):
    """Algunos campos de la API vienen como {"basic": "..."} y otras veces
    como texto plano directamente. Soporta las dos formas."""
    if isinstance(valor, dict):
        return valor.get("basic")
    if isinstance(valor, str):
        return valor
    return None


def _parsear_elemento_pagina12(el):
    autores_raw = (el.get("credits") or {}).get("by", []) or []
    autor = ", ".join(
        a.get("name") or a.get("byline") or "" for a in autores_raw if isinstance(a, dict)
    ).strip(", ")
    seccion = ((el.get("taxonomy") or {}).get("primary_section") or {}).get("name")
    canonical = el.get("canonical_url") or ""
    return {
        "medio": "Página/12",
        "titulo": _campo_basic(el.get("headlines")),
        "fecha": el.get("display_date"),
        "autor": autor or None,
        "seccion": seccion,
        "volanta_bajada": _campo_basic(el.get("subheadlines")) or _campo_basic(el.get("description")),
        "link": "https://www.pagina12.com.ar" + canonical if canonical.startswith("/") else canonical,
    }


async def buscar_y_extraer_pagina12(context, query):
    estado = cargar_checkpoint("pagina12_estado.json", {"offset": 0, "articulos": []})
    offset = estado["offset"]
    articulos = estado["articulos"]

    page = await context.new_page()
    await page.goto("https://www.pagina12.com.ar/", wait_until="domcontentloaded")

    num_found = None
    while True:
        url_api = _armar_url_busqueda_pagina12(query, offset)
        resultado = await page.evaluate(
            """async (u) => {
                const r = await fetch(u);
                if (!r.ok) return null;
                return await r.json();
            }""",
            url_api,
        )
        if not resultado:
            break
        num_found = resultado.get("numFound", num_found)
        elementos = resultado.get("content_elements", [])
        if not elementos:
            break
        articulos.extend(_parsear_elemento_pagina12(el) for el in elementos)
        offset += len(elementos)
        guardar_checkpoint("pagina12_estado.json", {"offset": offset, "articulos": articulos})
        print(f"[Página/12] {len(articulos)} / {num_found}")
        if num_found is not None and offset >= num_found:
            break

    await page.close()
    return articulos


async def _extraer_texto_completo_pagina12(page, url):
    await page.goto(url, wait_until="domcontentloaded")
    global_content = await page.evaluate(
        "() => (window.Fusion && window.Fusion.globalContent) || null"
    )
    if not global_content:
        return None
    elementos = global_content.get("content_elements", [])
    parrafos = [
        _limpiar_html(el.get("content"))
        for el in elementos
        if isinstance(el, dict) and el.get("type") == "text" and el.get("content")
    ]
    parrafos = [p for p in parrafos if p]
    return "\n\n".join(parrafos) if parrafos else None


async def agregar_texto_completo_pagina12(context, articulos):
    textos = cargar_checkpoint("pagina12_textos.json", {})
    page = await context.new_page()

    pendientes = [a for a in articulos if a["link"] not in textos]
    print(f"[Página/12] Trayendo texto completo: {len(pendientes)} pendientes de {len(articulos)}")

    for i, art in enumerate(pendientes, 1):
        try:
            texto = await _extraer_texto_completo_pagina12(page, art["link"])
        except Exception as e:
            print(f"  (aviso) error en {art['link']}: {e}")
            texto = None
        textos[art["link"]] = texto
        if i % 20 == 0:
            guardar_checkpoint("pagina12_textos.json", textos)
            print(f"  ... {i}/{len(pendientes)}")
        await asyncio.sleep(DELAY_ENTRE_ARTICULOS)

    guardar_checkpoint("pagina12_textos.json", textos)
    await page.close()

    for art in articulos:
        art["texto_completo"] = textos.get(art["link"])
    return articulos


# ---------------------------------------------------------------------------
# LA NACIÓN - recolección de links (scroll/"Cargar más", sin filtrar)
# ---------------------------------------------------------------------------
#
# (Probamos una variante basada en paginación por ?offset=N comparando qué
# links se repiten entre offsets muy separados para detectar "ruido
# constante" del sitio - pero dio un total sospechosamente bajo, 24 links,
# muy por debajo de lo que ya sabíamos que existía. El buscador de La
# Nación probablemente no maneja bien una consulta de dos palabras sin
# comillas, o el widget de "recomendados" es aleatorio en cada carga y
# rompe la comparación. Volvemos al método de scroll, que es más lento
# pero ya demostró encontrar notas reales; el filtro de contenido en la
# Etapa 3 sigue descartando el ruido que este método trae de más.)

LANACION_LINK_RE = re.compile(r"https://www\.lanacion\.com\.ar/[^\"'\s?]+-nid\d+/?")
LANACION_BOTONES = ["Cargar más", "Ver más", "Mostrar más", "Más resultados"]
MAX_INTENTOS_SIN_CRECIMIENTO = 4


async def recolectar_links_por_patron(page, patron, boton_textos, max_links=None):
    links = set()
    intentos_sin_crecimiento = 0
    ronda = 0

    while True:
        ronda += 1
        html_links = await page.eval_on_selector_all(
            "a", "els => els.map(e => e.href)"
        )
        nuevos = {l for l in html_links if patron.search(l or "")}
        antes = len(links)
        links |= nuevos
        crecio = len(links) > antes

        if ronda % 5 == 0 or not crecio:
            print(f"    ronda {ronda}: {len(links)} links encontrados hasta ahora")

        if max_links and len(links) >= max_links:
            break

        if not crecio:
            intentos_sin_crecimiento += 1
            if intentos_sin_crecimiento >= MAX_INTENTOS_SIN_CRECIMIENTO:
                break
        else:
            intentos_sin_crecimiento = 0

        clickeo = False
        for texto in boton_textos:
            try:
                boton = page.get_by_text(texto, exact=False).first
                if await boton.is_visible(timeout=1000):
                    await boton.click(timeout=2000)
                    clickeo = True
                    await page.wait_for_timeout(1200)
                    break
            except Exception:
                continue

        if not clickeo:
            await page.mouse.wheel(0, 3000)
            await page.wait_for_timeout(1200)

    return list(links)


async def buscar_links_lanacion(page, query, max_links=None):
    url = f"https://www.lanacion.com.ar/buscador/?query={quote(query)}"
    print(f"[La Nación] Abriendo buscador: {url}")
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    return await recolectar_links_por_patron(
        page, LANACION_LINK_RE, LANACION_BOTONES, max_links=max_links
    )


# ---------------------------------------------------------------------------
# LA NACIÓN - extracción del texto de la nota
# ---------------------------------------------------------------------------

def _extraer_de_global_content_lanacion(global_content, url_original):
    if not global_content:
        return None

    elementos = global_content.get("content_elements", []) or []
    parrafos = [
        _limpiar_html(el.get("content"))
        for el in elementos
        if isinstance(el, dict) and el.get("type") == "text" and el.get("content")
    ]
    parrafos = [p for p in parrafos if p]
    texto_completo = "\n\n".join(parrafos) if parrafos else None
    if not texto_completo:
        return None

    autores_raw = (global_content.get("credits") or {}).get("by", []) or []
    autor = ", ".join(
        a.get("name") or a.get("byline") or "" for a in autores_raw if isinstance(a, dict)
    ).strip(", ")
    seccion = ((global_content.get("taxonomy") or {}).get("primary_section") or {}).get("name")

    return {
        "medio": "La Nación",
        "titulo": _campo_basic(global_content.get("headlines")),
        "fecha": global_content.get("first_publish_date") or global_content.get("display_date"),
        "autor": autor or None,
        "seccion": seccion,
        "volanta_bajada": _campo_basic(global_content.get("subheadlines")),
        "texto_completo": texto_completo,
        "link": url_original,
    }


async def extraer_articulo_con_sesion(page, url, reintentos=2):
    """Abre la nota con la sesión logueada y extrae el texto completo.
    Espera a que la página cargue los datos de la nota y reintenta antes de
    darla por fallida (a veces los datos tardan en estar listos)."""
    ultimo = "sin_texto"
    for intento in range(reintentos + 1):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            ultimo = f"error_navegacion:{e}"
            await asyncio.sleep(3)
            continue

        try:
            await page.wait_for_function(
                "() => window.Fusion && window.Fusion.globalContent && window.Fusion.globalContent.content_elements",
                timeout=10000,
            )
        except Exception:
            pass

        try:
            gc = await page.evaluate("() => (window.Fusion && window.Fusion.globalContent) || null")
        except Exception as e:
            ultimo = f"error_js:{e}"
            continue

        datos = _extraer_de_global_content_lanacion(gc, url)
        if datos:
            return datos, "ok"

        ultimo = "sin_texto"
        await asyncio.sleep(3 + 3 * intento)

    return None, ultimo


async def recuperar_con_sesion(context, links):
    """Recupera el texto completo de La Nación con la sesión de la
    suscripción. Devuelve TODAS las notas recuperadas hasta ahora (incluye
    las de corridas anteriores)."""
    estado = cargar_checkpoint(
        "lanacion_logueado.json", {"articulos": [], "fallidos": {}, "intentos": {}}
    )
    articulos = estado.get("articulos", [])
    fallidos = estado.get("fallidos", {})
    intentos = estado.get("intentos", {})

    def _guardar():
        guardar_checkpoint(
            "lanacion_logueado.json",
            {"articulos": articulos, "fallidos": fallidos, "intentos": intentos},
        )

    if not ARCHIVO_SESION_LANACION.exists():
        print(
            "[La Nación] FALTA sesion_lanacion.json en Drive (ver Paso 3b): no se puede leer "
            f"el texto completo. Se usan solo las {len(articulos)} notas recuperadas en corridas anteriores."
        )
        return articulos

    ya_sesion = {a["link"] for a in articulos}
    pendientes = [
        l for l in links
        if l not in ya_sesion and intentos.get(l, 0) < MAX_INTENTOS_LOGUEADO
    ]
    total_pendientes = len(pendientes)
    if MAX_LANACION_LOGUEADO:
        pendientes = pendientes[:MAX_LANACION_LOGUEADO]

    print(
        f"[La Nación] {total_pendientes} links pendientes "
        f"(se procesan {len(pendientes)} en esta corrida)"
    )
    if not pendientes:
        return articulos

    browser = context.browser
    ctx = await browser.new_context(locale="es-AR", storage_state=str(ARCHIVO_SESION_LANACION))
    page = await ctx.new_page()

    fallos_seguidos = 0
    try:
        for i, link in enumerate(pendientes, 1):
            datos, resultado = await extraer_articulo_con_sesion(page, link)
            if datos:
                articulos.append(datos)
                fallidos.pop(link, None)
                fallos_seguidos = 0
                print(f"  ({i}/{len(pendientes)}) OK: {datos['titulo']}")
            else:
                intentos[link] = intentos.get(link, 0) + 1
                fallidos[link] = resultado
                fallos_seguidos += 1
                print(f"  ({i}/{len(pendientes)}) FALLÓ ({resultado}): {link}")
                if fallos_seguidos >= FALLOS_SEGUIDOS_PARA_CORTAR:
                    print(
                        f"\n(aviso) {fallos_seguidos} fallos seguidos: probablemente la sesión venció. "
                        "Renová sesion_lanacion.json (ver Paso 3b), subilo a Drive y volvé a correr."
                    )
                    break

            if i % 5 == 0:
                _guardar()

            await asyncio.sleep(DELAY_LOGUEADO)
    finally:
        # Se guarda siempre, incluso si se corta la celda a mitad de camino.
        _guardar()
        await page.close()
        await ctx.close()

    print(f"[La Nación] Recuperadas con sesión (acumulado): {len(articulos)}")
    return articulos


async def procesar_lanacion(context, query):
    # --- Etapa 1: links ---
    links_guardados = cargar_checkpoint("lanacion_links.json", {"links": None})
    if links_guardados.get("links") is not None:
        links = links_guardados["links"]
        print(f"[La Nación] Usando {len(links)} links ya recolectados (checkpoint).")
    else:
        page = await context.new_page()
        links = await buscar_links_lanacion(page, query, max_links=MAX_LINKS_LANACION_RECOLECCION)
        await page.close()
        guardar_checkpoint("lanacion_links.json", {"links": links})
        print(f"[La Nación] {len(links)} links candidatos recolectados (sin filtrar todavía).")

    # --- Etapa 2: texto completo con la sesión de la suscripción ---
    articulos = await recuperar_con_sesion(context, links)
    print(f"[La Nación] Notas con texto completo (acumulado): {len(articulos)}")

    # --- Etapa 3: filtro de contenido (descarta el ruido de la recolección) ---
    relevantes = [a for a in articulos if menciona_economia_popular(a)]
    print(f"[La Nación] Tras filtrar por contenido ('economía popular' real): {len(relevantes)} de {len(articulos)}")

    return relevantes


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(user_agent=USER_AGENT, locale="es-AR")

        articulos_pagina12 = []
        articulos_lanacion = []

        if PROCESAR_PAGINA12:
            articulos_pagina12 = await buscar_y_extraer_pagina12(context, QUERY)
            articulos_pagina12 = filtrar_por_fecha(articulos_pagina12, FECHA_DESDE, FECHA_HASTA)
            print(f"[Página/12] {len(articulos_pagina12)} dentro del rango de fechas")
            articulos_pagina12 = await agregar_texto_completo_pagina12(context, articulos_pagina12)
        else:
            print("[Página/12] Salteado (PROCESAR_PAGINA12 = False)")

        if PROCESAR_LANACION:
            articulos_lanacion = await procesar_lanacion(context, QUERY)
            articulos_lanacion = filtrar_por_fecha(articulos_lanacion, FECHA_DESDE, FECHA_HASTA)
            print(f"[La Nación] {len(articulos_lanacion)} dentro del rango de fechas")
        else:
            print("[La Nación] Salteado (PROCESAR_LANACION = False)")

        await browser.close()

    todos = articulos_pagina12 + articulos_lanacion
    print(f"\nTotal combinado: {len(todos)}")

    df = pd.DataFrame(todos)
    columnas = ["medio", "titulo", "fecha", "autor", "seccion", "volanta_bajada", "texto_completo", "link"]
    for col in columnas:
        if col not in df.columns:
            df[col] = None
    df = df[columnas].sort_values(["medio", "fecha"])

    df.to_excel(OUTPUT_XLSX, index=False)
    print(f"\nListo. Corpus guardado en: {OUTPUT_XLSX.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())

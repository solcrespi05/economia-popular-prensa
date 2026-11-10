"""
Guarda la sesión de la suscripción de La Nación para que la use el scraper.

Se conecta a un Chrome abierto a mano con depuración remota (puerto 9222), en
el que ya se inició sesión. El archivo que genera funciona como una contraseña.

Lee:    la sesión abierta en ese Chrome
Genera: sesion_lanacion.json (está en .gitignore: nunca debe subirse)

Cómo se corre, desde la carpeta del repositorio:
    python3 src/01_scraper/capturar_sesion.py
"""
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

ARCHIVO_SESION = config.SESION_LANACION

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        print(f"Cookies capturadas: {len(await context.cookies())}")
        await context.storage_state(path=str(ARCHIVO_SESION))
        print("Sesión guardada en:", ARCHIVO_SESION.resolve())

if __name__ == "__main__":
    asyncio.run(main())

# ¿Qué es la Economía Popular? Una exploración a través de la prensa (2019-2023)

Código y datos derivados de una práctica de investigación de la Licenciatura en Ciencia de Datos (UNSAM), dirigida por Gabriela Delamata en el Instituto de Investigaciones Políticas (IIP, Escuela de Política y Gobierno, UNSAM-CONICET).

El proyecto estudia quién nombra la "economía popular" en la prensa argentina y con qué sentidos, en notas de **Página/12** y **La Nación** publicadas entre septiembre de 2019 y septiembre de 2023.

- **Corpus:** 1.245 notas (645 de La Nación y 600 de Página/12), 1.215 con texto.
- **Unidad de análisis:** cada mención del término. Son 2.043 menciones, en 1.204 notas.
- **Codificación:** [libro de códigos](codebook.md) del equipo, con 5 tipos de emisor y 16 marcos de referencia.
- **Dos vías que se comparan:** un diccionario de patrones y una lectura mención por mención asistida por IA. La lectura se usa como referencia, pero **no es una verdad absoluta**: falta validarla con el equipo.

## Estructura

```
economia-popular-prensa/
├── src/
│   ├── config.py                     # rutas, para correr en local o en Colab
│   ├── 01_scraper/                   # recolección de las notas
│   ├── 02_extraer_fragmentos.py      # una fila por mención
│   ├── 03_codificacion_diccionario.py
│   ├── 03b_revision_anses.py         # revisión manual de 32 menciones
│   ├── 04_lectura_llm/               # lectura con IA, por lotes
│   ├── 05_comparacion_metodos.py     # matrices de confusión
│   ├── 06_figuras_informe.py
│   └── verificar_controles.py        # controla los totales esperados
├── datos/
│   ├── crudos/      # texto completo: no se incluye en el repositorio
│   └── derivados/   # salidas sin el texto completo de las notas
├── resultados/      # tablas y figuras
└── informe/         # LaTeX, figuras y PDF
```

## Instalación

Hace falta Python 3.9 o superior. Desde la carpeta del repositorio:

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

Para volver a recolectar notas también hay que correr `playwright install chromium`.

## Orden de ejecución

Los pasos 2 en adelante necesitan el corpus en `datos/crudos/corpus_economia_popular_avance.xlsx`.

| Paso | Comando | Resultado |
|---|---|---|
| 1. Recolección (opcional) | `python3 src/01_scraper/scraper_economia_popular.py` | Corpus y checkpoints |
| 2. Menciones | `python3 src/02_extraer_fragmentos.py` | `fragmentos_economia_popular.xlsx` |
| 3. Diccionario | `python3 src/03_codificacion_diccionario.py` | `fragmentos_codificados.xlsx`, `tabla_emisores_marcos.xlsx` |
| 3b. Revisión de ANSES | `python3 src/03b_revision_anses.py` | `fragmentos_codificados_revision_anses.xlsx` |
| Control | `python3 src/verificar_controles.py` | Compara con los totales esperados |
| 4. Lectura con IA | `python3 src/04_lectura_llm/preparar_lotes.py` | Lotes para leer |
| 4. Unión | `python3 src/04_lectura_llm/validar_y_unir.py` | Corpus final codificado |
| 5. Comparación | `python3 src/05_comparacion_metodos.py` | `resultados/comparacion_metodos.xlsx` y heatmaps |
| 6. Figuras | `python3 src/06_figuras_informe.py` | Figuras del informe y `resultados/cifras.txt` |

La lectura del paso 4 no es automática: `src/04_lectura_llm/instrucciones.md` tiene las instrucciones exactas que siguieron los agentes lectores y cada lote guarda su resultado en `src/04_lectura_llm/lotes/`.

La recolección se hizo en Google Colab. `src/01_scraper/notebooks/` conserva esos notebooks, sin sus salidas. Los scripts también corren en Colab: `config.py` detecta el entorno y usa la carpeta `economia_popular` de Drive, que tiene que replicar esta estructura.

El informe se compila desde `informe/` con `latexmk -xelatex informe_final.tex`.

## Datos que no se incluyen

> Por ahora el repositorio es privado e incluye `datos/crudos/`, con el texto completo de las notas. Antes de hacerlo público hay que quitar esa carpeta y borrarla del historial.

- **Texto completo de las notas** (`datos/crudos/`): tiene derechos de autor. Incluye el corpus y el corpus final con la columna `nota_completa`.
- **`sesion_lanacion.json`:** es la sesión de una suscripción y funciona como una credencial.
- **`checkpoints/`:** guardan texto de las notas durante la recolección.

Para reproducir el trabajo sin esos archivos se pueden usar las salidas de `datos/derivados/`. Otra opción es volver a recolectar el corpus; en ese caso los totales pueden cambiar, porque los buscadores se actualizan.

## Limitaciones

- La codificación por diccionario busca patrones en una ventana de 300 caracteres a cada lado de la mención: no identifica quién habla.
- La lectura con IA puede equivocarse y todavía no fue validada por el equipo.
- Excel corta las celdas en 32.767 caracteres y el corpus quedó guardado con ese corte: 8 notas están truncadas.
- Cinco notas de Página/12 tienen fecha 10/08/2022, pero por su título y contenido parecen de 2019. No se corrigieron.
- El corpus de Página/12 tiene exactamente 600 notas, con trimestres vacíos, por lo que no debe tomarse como una cobertura completa.

## Cómo citar

> Crespi, M. S. (2026). *¿Qué es la Economía Popular? Una exploración a través de la prensa (2019-2023)* [Código y datos derivados]. Práctica de investigación, Licenciatura en Ciencia de Datos, Universidad Nacional de San Martín. Dirección: G. Delamata.

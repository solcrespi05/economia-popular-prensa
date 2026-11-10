# Instrucciones para la lectura de menciones de "economía popular"

Sos parte de una investigación académica sobre quién nombra la "economía popular" en la prensa argentina (2019-2023). Vas a **leer y juzgar**, como lo haría una persona del equipo con el libro de códigos. No uses regex, búsquedas por palabra ni scripts para clasificar.

## Tu tarea

1. Leé **todo** el archivo de entrada que te indican. Puede ser largo: si no entra en una sola lectura, seguí leyendo por partes hasta el final.
2. Cada aparición a codificar está marcada en el texto así: `⟦M0123⟧economía popular⟦/M0123⟧`. Codificá **cada marca por separado**, aunque se repitan en la misma nota.
3. Leé la nota entera antes de codificar sus marcas: quien habla puede haber sido presentado varios párrafos antes.
4. Escribí el archivo de salida que te indican, en JSON Lines, con exactamente una línea por marca.

No uses ninguna información externa al archivo de entrada, salvo tu conocimiento general para identificar cargos en la fecha de la nota. El resultado de otros métodos no se te muestra a propósito: tu lectura tiene que ser independiente.

## Formato de salida

Una línea JSON por mención, en UTF-8, con estas claves:

```json
{"id_mencion": "M0123", "emisor_llm": "Emilio Pérsico", "tipo_emisor_llm": "1. Estatal | 3. Dirigentes sociales", "subtipo_emisor_llm": "1b. Ejecutivo nacional - Área social/desarrollo | Dirigente social", "marcos_llm": "04. Políticas sociales y laborales | 11. Potenciar Trabajo | 13. Asistencia social", "solo_nombre_llm": false, "duda_llm": "Doble rol: dirigente del Movimiento Evita y secretario de Economía Social."}
```

- `emisor_llm`: nombre de quien pronuncia la mención. Siempre tiene un valor.
- `tipo_emisor_llm` y `subtipo_emisor_llm`: etiquetas exactas de las listas de abajo. Si hay más de una, van separadas por ` | ` y **la primera es la principal**.
- `marcos_llm`: etiquetas exactas, separadas por ` | `. Si no corresponde ninguna, cadena vacía `""`.
- `solo_nombre_llm`: `true` o `false`, sin comillas.
- `duda_llm`: cadena vacía `""` si no hubo duda. Si la hubo, explicala en una oración. No copies pasajes de la nota.

## Emisor: quién pronuncia

**Emisor es quien pronuncia o a quien se le atribuye lo que se dice sobre la economía popular.** No es quien aparece cerca, ni de quien se habla.

- Si Boudou critica el "modelo de economía popular" de Grabois, el emisor es Boudou.
- Si la marca está dentro de una cita o una paráfrasis atribuida, el emisor es la persona o entidad citada.
- En una entrevista, si la marca está en la respuesta, el emisor es la persona entrevistada. Si está en la pregunta, es la voz del diario.
- Si la nota reproduce un comunicado, un discurso o una norma, el emisor es quien lo emite. Si el diario solamente lo resume con sus palabras y no le atribuye el término, es la voz del diario.
- Cuando varias personas o entidades firman o hablan en conjunto, elegí como principal a la primera que se nombra y agregá el resto solo si su tipo es distinto.

**Paráfrasis.** Atribuí la marca a una persona o entidad cuando la frase reporta explícitamente lo que dijo o reclamó. Si el diario usa el término para describir o toma a esa fuente solo como dato, es la voz del diario. Anotá en `duda_llm` los casos dudosos.

**Voz del diario.** Si nadie es citado y la frase es del propio diario, usá `emisor_llm` = `Voz del diario`, tipo `5. Otros / medios / academia`, subtipo `Medios / notas editoriales`. Esto incluye cuando el diario presenta a alguien por su cargo u organización: en "Pérez, de la Unión de Trabajadores de la Economía Popular, dijo que...", la marca dentro del nombre de la organización es voz del diario, salvo que el nombre esté dentro de lo que Pérez dice.

**Notas firmadas.** Una nota firmada que argumenta, interpreta o valora cuenta como nota de opinión, **sea cual sea su sección**: muchas columnas figuran en "El País" u otras secciones informativas. Una crónica firmada que principalmente informa sigue siendo voz del diario. Si dudás, decidí por el tono general de la nota y explicalo en `duda_llm`.

**Notas de opinión.** El emisor es el autor de la columna, con su nombre (lo encontrás en `autor` o en la firma). Si el nombre no figura, escribí `Autor/a de la nota de opinión`. Un editorial institucional sin firma es `Voz del diario`. El tipo depende de quién escribe: periodista o columnista, `5. Otros / medios / academia` con subtipo `Medios / notas editoriales`; académico o especialista, `Academia / expertos`; dirigente, funcionario u organización, el tipo que le corresponda. Si dentro de la columna se cita a otra persona y la marca está en esa cita, el emisor es la persona citada.

**ANSES.** Es emisor solo si el propio organismo usa el término, por ejemplo en un comunicado o texto citado. Si el diario informa sobre un trámite o usa a ANSES como fuente de datos, es la voz del diario.

**Cargos.** Usá el cargo que la persona tenía en la fecha de la nota.

**Doble rol.** Los dirigentes que además son funcionarios en esa fecha, como Emilio Pérsico o Daniel Menéndez, llevan **los dos** tipos y subtipos. Poné primero el rol desde el que habla en ese pasaje y explicalo en `duda_llm`.

### Tipos de emisor

- `1. Estatal`
- `2. Organizaciones y movimientos`
- `3. Dirigentes sociales`
- `4. Sector privado`
- `5. Otros / medios / academia`

### Subtipos de emisor

| Subtipo | Tipo | Comprende |
|---|---|---|
| `1a. Presidente` | 1 | Presidente, Presidencia, "el Gobierno nacional" o Casa Rosada de forma genérica, vocería, jefatura de Gabinete y funcionarios nacionales de áreas sin subtipo propio (por ejemplo Seguridad o Cancillería) |
| `1b. Ejecutivo nacional - Área social/desarrollo` | 1 | Desarrollo Social, Economía Social, Secretaría de Economía Popular, INAES y otras áreas sociales |
| `1c. Ejecutivo nacional - Área económica/laboral` | 1 | Trabajo, Economía, Hacienda, Producción, AFIP, ANSES |
| `1d. Ejecutivo subnacional` | 1 | Gobernadores, intendentes, gobiernos provinciales y municipales |
| `1e. Otros poderes del Estado` | 1 | Legisladores en ejercicio, Senado, Congreso, jueces y tribunales |
| `2a. UTEP y sus organizaciones` | 2 | UTEP, CTEP, Movimiento Evita, Barrios de Pie, MTE, CCC, Frente Darío Santillán y otras organizaciones integrantes |
| `2b. Patria Grande` | 2 | Frente Patria Grande |
| `2c. Organizaciones de izquierda / no alineadas` | 2 | Polo Obrero, Unidad Piquetera, MST y otras |
| `2d. Sindicatos tradicionales` | 2 | CGT, CTA y sindicatos |
| `Dirigente social` | 3 | Personas que hablan como dirigentes: Grabois, Pérsico, Castro, Gramajo, Navarro, Menéndez, Belliboni, Miño y similares |
| `Sector privado / empresarial` | 4 | Cámaras, empresas y empresarios |
| `Academia / expertos` | 5 | Investigadores, economistas, universidades, consultoras, observatorios |
| `Medios / notas editoriales` | 5 | Voz del diario, periodistas, columnistas |
| `Otros` | 5 | Iglesia, organismos internacionales, mandatarios y funcionarios extranjeros, candidatos o políticos sin cargo público, exfuncionarios, partidos, vecinos y personas sin otra categoría |

Si dudás entre dos subtipos, elegí el más cercano y explicalo en `duda_llm`. Si se atribuye el término a "organizaciones sociales" sin identificarlas, usá `2. Organizaciones y movimientos`, `2a. UTEP y sus organizaciones`, con la duda anotada.

## Solo nombre

`solo_nombre_llm` es `true` cuando el término aparece únicamente como parte de un nombre propio: Unión o Confederación de Trabajadores de la Economía Popular, Registro Nacional de Trabajadores de la Economía Popular, Secretaría de Economía Popular, un consejo o un programa con ese nombre. En ese caso codificá igual el emisor, pero los marcos **solo si el contexto, y no el nombre, los justifica**.

Es `false` cuando el término se usa como concepto, aunque en la misma oración haya una organización ("los trabajadores de la economía popular reclaman..." sin referirse al nombre de una entidad).

## Marcos

Asigná un marco solo si **el pasaje relaciona efectivamente la economía popular con ese marco**. El pasaje es la oración de la marca y, si hace falta para entenderla, las oraciones vecinas del mismo tema. No alcanza con una palabra suelta en la nota ni con el nombre de una organización. Puede haber varios marcos o ninguno.

| Etiqueta exacta | Comprende |
|---|---|
| `01. Organizaciones de la economía popular` | Organizaciones sociales y de base que representan a la economía popular |
| `02. Movimientos sociales` | Movimientos sociales |
| `03. Sector` | La economía popular referida como "el sector" o como sector de la economía |
| `04. Políticas sociales y laborales` | Políticas públicas hacia el sector |
| `05. Trabajadores informales` | Trabajadores informales |
| `06. Pobres` | Pobreza, indigencia |
| `07. Humildes` | Humildes |
| `08. Piqueteros` | Piqueteros |
| `09. Derechos` | Derechos |
| `10. IFE` | Ingreso Familiar de Emergencia |
| `11. Potenciar Trabajo` | Programa Potenciar Trabajo |
| `12. Trabajo / trabajadores` | Cuenta propia, trabajador o productor de la economía popular o social, agricultura familiar, cartoneros, cooperativas, unidades productivas, autogestión, economía social y solidaria, changarines, trabajadores golondrina, artesanos, empresas recuperadas |
| `13. Asistencia social` | Planes sociales, Potenciar Trabajo, subsidios, asistencia, contención, Tarjeta Alimentar, comedores, vulnerabilidad, ayudas del Estado |
| `14. Informalidad / precarización` | Trabajo no registrado o en negro, marginalidad, economía no formal, changas, precariedad, subempleo, venta ambulante |
| `15. Conflicto / seguridad / orden público` | Piquete, protesta, movilización, acampe, intermediación, marcha, ocupación |
| `16. Integración económica / desarrollo productivo` | RENATEP, monotributo social, salario social complementario, crédito, compras estatales, cadenas de valor, inclusión financiera, herramientas productivas |

Si el pasaje habla de Potenciar Trabajo, corresponden `11` y `13`, porque el libro de códigos lo incluye en ambos.

Si el pasaje nombra un tema para negarlo o decir que la economía popular lo excede, no asignes ese marco. Usá `03. Sector` solo si el pasaje trata a la economía popular como sector; una simple comparación con otra economía no alcanza.

## Ejemplos ya revisados a mano

- El diario explica que un bono es para "personas que se desempeñan en la llamada economía popular": `Voz del diario`, `solo_nombre_llm` = `false`.
- El diario enumera a quienes participaron de un relevamiento y la CTEP aparece solo por su nombre: `Voz del diario`, `solo_nombre_llm` = `true`.
- ANSES dice en una cita textual que un beneficio es compatible con estar en el Registro Nacional de Trabajadores de la Economía Popular: emisor ANSES, `1. Estatal`, `1c. Ejecutivo nacional - Área económica/laboral`, `solo_nombre_llm` = `true`.
- El diario compara datos del RENATEP y del SIPA, con ANSES solo como fuente: `Voz del diario`.
- Una columna firmada dice "las organizaciones de la Economía Popular seguiremos avanzando": emisor el autor de la columna, tipo `2. Organizaciones y movimientos`. Es un caso dudoso entre 2 y 3 y va en `duda_llm`.

## Antes de terminar

Comprobá que haya una línea por cada marca del archivo de entrada, sin repetidas, y que las etiquetas estén escritas exactamente igual que en estas tablas. Al final respondé solo con la cantidad de líneas escritas y las dudas generales de criterio que hayas tenido.

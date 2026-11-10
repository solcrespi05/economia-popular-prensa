# Libro de códigos

Cada mención de "economía popular" se codifica en dos dimensiones, emisor y marco de referencia, y lleva además una marca de "solo nombre".

## Variables de la base final

La base tiene una fila por cada una de las 2.043 menciones. Las versiones son `corpus_final_codificado.xlsx` y `.parquet`, con la nota completa y de uso interno, y `corpus_final_codificado_sin_nota.xlsx`, que es la publicable y no incluye `nota_completa`.

Las variables de tipo Lista pueden tener varios valores, separados por ` | `.

| Variable | Tipo | Descripción |
|---|---|---|
| `id_mencion` | Texto | Identificador estable de la mención (M0001 a M2043), en el orden de filas de la base. |
| `medio` | Texto | Diario: Página/12 o La Nación. |
| `titulo` | Texto | Título de la nota. |
| `fecha` | Fecha | Fecha de publicación registrada en la nota. |
| `seccion` | Texto | Sección del diario. |
| `link` | Texto | Enlace de la nota. Une cada mención con su nota. |
| `mencion_textual` | Texto | Forma exacta en que aparece el término. |
| `fragmento` | Texto | Contexto de hasta 300 caracteres antes y después de la mención. |
| `actor_candidato` | Texto | Nombre propio cercano, detectado por heurística. Es una pista, no una codificación. |
| `verbo_atribucion` | Texto | Verbo de atribución encontrado en el fragmento (dijo, afirmó, sostuvo...). |
| `emisores_detectados` | Lista | Emisores encontrados por el diccionario en el fragmento. Valores en la sección siguiente. |
| `tipo_emisor` | Lista | Tipos de emisor según el diccionario. |
| `subtipo_emisor` | Lista | Subtipos de emisor según el diccionario. |
| `marcos_detectados` | Lista | Marcos de referencia según el diccionario. |
| `nota_completa` | Texto | Texto completo de la nota. No se publica, por derechos de autor. |
| `nota_truncada_en_excel` | Verdadero/falso | Indica si el texto de la nota supera el límite de 32.767 caracteres de una celda de Excel o quedó cortado en ese límite. |
| `emisor_llm` | Texto | Quién pronuncia la mención según la lectura con IA. Puede ser `Voz del diario`. |
| `tipo_emisor_llm` | Lista | Tipos de emisor según la lectura. El primero es el principal. |
| `subtipo_emisor_llm` | Lista | Subtipos de emisor según la lectura. El primero es el principal. |
| `marcos_llm` | Lista | Marcos de referencia según la lectura. Vacío si no corresponde ninguno. |
| `solo_nombre_llm` | Verdadero/falso | Indica si el término aparece únicamente como parte de un nombre propio. |
| `duda_llm` | Texto | Duda de criterio registrada por el lector. Vacío si no hubo. |
| `texto_entero_disponible` | Verdadero/falso | Indica si se cuenta con el texto entero de la nota. Solo está en el archivo Parquet. |

Las variables sin el sufijo `_llm` provienen del diccionario y las que lo llevan, de la lectura con IA. Las etiquetas válidas de tipos, subtipos y marcos son las de las tablas que siguen.

### Valores de `emisores_detectados`

| Valor | Tipo | Subtipo |
|---|---|---|
| Presidente de la Nación | Estatal | Presidente |
| Ministerio de Desarrollo Social / Economía Social | Estatal | Ejecutivo nacional - Área social/desarrollo |
| Ministerio de Trabajo / Economía | Estatal | Ejecutivo nacional - Área económica/laboral |
| Gobierno subnacional (provincias y municipios) | Estatal | Ejecutivo subnacional |
| Poder Legislativo / Judicial | Estatal | Otros poderes del Estado |
| UTEP / CTEP | Organizaciones y movimientos | UTEP y sus organizaciones |
| Movimiento Evita | Organizaciones y movimientos | UTEP y sus organizaciones |
| Barrios de Pie | Organizaciones y movimientos | UTEP y sus organizaciones |
| Otras organizaciones de la UTEP | Organizaciones y movimientos | UTEP y sus organizaciones |
| Frente Patria Grande | Organizaciones y movimientos | Patria Grande |
| Organizaciones de izquierda / no alineadas | Organizaciones y movimientos | Organizaciones de izquierda / no alineadas |
| Sindicatos tradicionales (CGT / CTA) | Organizaciones y movimientos | Sindicatos tradicionales |
| Juan Grabois | Dirigentes sociales | Dirigente social |
| Emilio Pérsico | Dirigentes sociales | Dirigente social |
| Esteban "Gringo" Castro | Dirigentes sociales | Dirigente social |
| Alejandro "Peluca" Gramajo | Dirigentes sociales | Dirigente social |
| Fernando "Chino" Navarro | Dirigentes sociales | Dirigente social |
| Daniel Menéndez | Dirigentes sociales | Dirigente social |
| Eduardo "Chiquito" Belliboni | Dirigentes sociales | Dirigente social |
| Fernanda Miño | Dirigentes sociales | Dirigente social |
| Cámaras y entidades empresarias | Sector privado | Sector privado / empresarial |
| Expertos y academia | Otros / medios / academia | Academia / expertos |
| Iglesia / Papa Francisco | Otros / medios / academia | Otros |
| Nota de opinión / editorial | Otros / medios / academia | Medios / notas editoriales |

## Emisor

Es quien pronuncia o a quien se le atribuye lo que se dice sobre la economía popular. No es quien aparece cerca ni de quien se habla.

| Tipo | Subtipo | Comprende |
|---|---|---|
| Estatal | Presidente | Presidencia, Gobierno nacional o Casa Rosada de forma genérica, vocería, jefatura de Gabinete y funcionarios nacionales de áreas sin subtipo propio |
| Estatal | Ejecutivo nacional - Área social/desarrollo | Desarrollo Social, Economía Social, Secretaría de Economía Popular, INAES y otras áreas sociales |
| Estatal | Ejecutivo nacional - Área económica/laboral | Trabajo, Economía, Hacienda, Producción, AFIP, ANSES |
| Estatal | Ejecutivo subnacional | Gobernadores, intendentes, gobiernos provinciales y municipales |
| Estatal | Otros poderes del Estado | Legisladores en ejercicio, Senado, Congreso, jueces y tribunales |
| Organizaciones y movimientos | UTEP y sus organizaciones | UTEP, CTEP, Movimiento Evita, Barrios de Pie, MTE, CCC, Frente Darío Santillán y otras integrantes |
| Organizaciones y movimientos | Patria Grande | Frente Patria Grande |
| Organizaciones y movimientos | Organizaciones de izquierda / no alineadas | Polo Obrero, Unidad Piquetera, MST y otras |
| Organizaciones y movimientos | Sindicatos tradicionales | CGT, CTA y sindicatos |
| Dirigentes sociales | Dirigente social | Personas que hablan como dirigentes: Grabois, Pérsico, Castro, Gramajo, Navarro, Menéndez, Belliboni, Miño y similares |
| Sector privado | Sector privado / empresarial | Cámaras, empresas y empresarios |
| Otros / medios / academia | Medios / notas editoriales | Voz del diario, periodistas, columnistas |
| Otros / medios / academia | Academia / expertos | Investigadores, economistas, universidades, consultoras, observatorios |
| Otros / medios / academia | Otros | Iglesia, organismos internacionales, mandatarios y funcionarios extranjeros, candidatos o políticos sin cargo, exfuncionarios, partidos, vecinos y personas sin otra categoría |

### Criterios de emisor

- Si la mención está dentro de una cita o de una paráfrasis atribuida, el emisor es la persona o entidad citada.
- Si nadie es citado y la frase es del propio diario, el emisor es la voz del diario.
- En una nota de opinión, el emisor es el autor de la columna. Su tipo depende de quién escribe: periodista, académico, dirigente o funcionario.
- En una entrevista, el emisor es la persona entrevistada si la mención está en la respuesta, y la voz del diario si está en la pregunta.
- ANSES es emisor solo si el propio organismo usa el término.
- Se usa el cargo que la persona tenía en la fecha de la nota.
- Los dirigentes que además son funcionarios en esa fecha llevan los dos tipos y subtipos. Va primero el rol desde el que hablan en ese pasaje.

## Marcos de referencia

Un marco se asigna solo si el pasaje relaciona efectivamente la economía popular con él. No alcanza con una palabra suelta ni con el nombre de una organización. Una mención puede tener varios marcos o ninguno.

| Marco | Comprende |
|---|---|
| Organizaciones de la economía popular | Organizaciones sociales y de base que representan a la economía popular |
| Movimientos sociales | Movimientos sociales |
| Sector | La economía popular referida como "el sector" o como sector de la economía |
| Políticas sociales y laborales | Políticas públicas hacia el sector |
| Trabajadores informales | Trabajadores informales |
| Pobres | Pobreza, indigencia |
| Humildes | Humildes |
| Piqueteros | Piqueteros |
| Derechos | Derechos |
| IFE | Ingreso Familiar de Emergencia |
| Potenciar Trabajo | Programa Potenciar Trabajo |
| Trabajo / trabajadores | Cuenta propia, trabajador o productor de la economía popular o social, agricultura familiar, cartoneros, cooperativas, unidades productivas, autogestión, economía social y solidaria, changarines, trabajadores golondrina, artesanos, empresas recuperadas |
| Asistencia social | Planes sociales, Potenciar Trabajo, subsidios, asistencia, contención, Tarjeta Alimentar, comedores, vulnerabilidad, ayudas del Estado |
| Informalidad / precarización | Trabajo no registrado o en negro, marginalidad, economía no formal, changas, precariedad, subempleo, venta ambulante |
| Conflicto / seguridad / orden público | Piquete, protesta, movilización, acampe, intermediación, marcha, ocupación |
| Integración económica / desarrollo productivo | RENATEP, monotributo social, salario social complementario, crédito, compras estatales, cadenas de valor, inclusión financiera, herramientas productivas |

Si el pasaje habla de Potenciar Trabajo, corresponden ese marco y el de asistencia social, porque el libro de códigos lo incluye en ambos.

## Solo nombre

Es verdadero cuando el término aparece únicamente como parte de un nombre propio: Unión o Confederación de Trabajadores de la Economía Popular, Registro Nacional de Trabajadores de la Economía Popular, Secretaría de Economía Popular, un consejo o un programa con ese nombre.

En esos casos el emisor se codifica igual, y los marcos solo si los justifica el contexto y no el nombre.

## Reglas agregadas durante la lectura

Estas reglas se sumaron o aclararon al aplicar el libro de códigos y falta revisarlas con el equipo.

- Una nota firmada que argumenta, interpreta o valora cuenta como nota de opinión, sea cual sea su sección. Una crónica firmada que principalmente informa es voz del diario.
- Un editorial institucional sin firma es voz del diario.
- Una paráfrasis se atribuye a una persona o entidad solo si la frase reporta explícitamente lo que dijo o reclamó. Si el diario usa el término para describir, o toma a esa fuente solo como dato, es voz del diario.
- Si se atribuye el término a "organizaciones sociales" sin identificarlas, se usa el subtipo UTEP y sus organizaciones, con la duda anotada.
- Si el pasaje nombra un tema para negarlo o para decir que la economía popular lo excede, no se asigna ese marco.
- El marco Sector se usa solo si el pasaje trata a la economía popular como sector. Una simple comparación con otra economía no alcanza.

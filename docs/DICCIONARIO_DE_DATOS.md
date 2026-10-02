# Diccionario de datos

> **Archivo generado** por `scripts/generar_diccionario.py` desde `src/evaplan/esquemas.py`. No editar a mano: cambia el esquema y vuelve a generarlo.

Cada fuente se lee con un lector tipado (`src/evaplan/lectura.py`) que devuelve nombres canónicos, tipos consistentes y la columna `fila_excel` (fila en el archivo original).

## Tipos lógicos

| Tipo | Significado |
|---|---|
| `texto` | Texto libre. Los marcadores de vacío ('.', 'nan', '') se convierten en nulo. |
| `codigo` | Identificador guardado como texto (nunca como número: evita '2024009990001.0'). |
| `entero` | Número entero (Int64). Valores no numéricos (p. ej. '2020-2023') pasan a nulo. |
| `decimal` | Número real. Acepta formato es-CO ('1.500,00'). 'NO DISPONIBLE', 'ERROR' pasan a nulo. |
| `moneda` | Pesos colombianos como número real. Acepta '2.339.400.000' (texto) y 0 (entero). |
| `valor_np` | Número o 'NP' (No Programado). Genera dos columnas: <campo> y <campo>_np (booleano). |
| `si_no` | Booleano a partir de 'Sí'/'No'. |
| `fecha` | Fecha (datetime). Inválidas pasan a NaT. |
| `codigo_nombre` | Celda 'COD - NOMBRE'. Genera <campo>_codigo y <campo>_nombre. |

## EVAPLAN · Informe de Plan Indicativo MP

Metas de producto (MP) de UNA entidad con su programación vigente y el resultado reportado.

- **Origen:** Descarga de EVAPLAN: 'Informe de Plan Indicativo MP.xlsx'
- **Hoja:** primera hoja · **Encabezados en la fila:** 2
- **Llave:** `codigo_mp`
- **Lector:** `leer_pi_mp_evaplan()`

> Fila 1 es un título ('EvaPlan'); los encabezados están en la fila 2.
> No se leen (se ignoran) los bloques de enfoque poblacional (~22 columnas), 'Otros', '¿Cuál Otro?' y enfoque territorial (una columna por municipio, ~42).
> Los encabezados de año son numéricos (2024, 2025, 2026.0…): se normalizan.

| # | Encabezado original | Campo canónico | Tipo | ¿Vacío? | Descripción | Notas |
|---|---|---|---|---|---|---|
| 1 | `Codigo Entidad` | `codigo_entidad` | codigo | no | Código de la entidad (p. ej. '9999'). |  |
| 2 | `Nombre Entidad` | `nombre_entidad` | texto | no | Nombre completo de la entidad. |  |
| 3 | `Código de Meta` | `codigo_mp` | codigo | no | Código de la meta de producto: 'MP'+MR(5)+subprograma(2)+consecutivo(2)+producto MGA(7). | 18 caracteres. Ver descomponer_codigo_mp(). |
| 4 | `Descripción de Meta` | `descripcion_mp` | texto | no | Texto de la meta de producto. |  |
| 5 | `Codigo Programa` | `programa` | codigo_nombre (2 columnas) | no | Programa del PDD ('14 - Nombre'). |  |
| 6 | `Codigo Subprograma` | `subprograma` | codigo_nombre (2 columnas) | no | Subprograma ('04 - Nombre'). |  |
| 7 | `Comportamiento del Indicador` | `comportamiento` | texto | no | Tipo de indicador; define cómo se calcula el cumplimiento del PG. |  |
| 8 | `Valor Linea Base` | `linea_base` | decimal | sí | Valor de la línea base. |  |
| 9 | `Año Linea Base` | `anio_linea_base` | entero | sí | Año de la línea base. |  |
| 10 | `Periodicidad de Medición` | `periodicidad` | texto | no | Anual, semestral, trimestral… |  |
| 11 | `Unidad de Medida` | `unidad_medida` | texto | no | Número, Porcentaje, Kilómetros… |  |
| 12 | `Variable` | `variables` | texto | no | Definición de las variables V1..Vn del indicador. |  |
| 13 | `Constante (K)` | `constante_k` | decimal | no | Constante de la fórmula. |  |
| 14 | `Fórmula` | `formula` | texto | no | Fórmula del indicador, p. ej. 'V1' o '((V1+V2)/720)*100'. |  |
| 15 | `Resultado` | `resultado` | decimal | no | Resultado reportado por la entidad en el periodo de corte (vigencia en curso). | Dato clave de seguimiento. Semántica exacta por confirmar (¿acumulado de la vigencia?). |
| 16 | `Valor Proyectado` | `valor_proyectado` | decimal | sí | Proyección reportada por la entidad. | Por confirmar su significado. |
| 17 | `PG` | `valor_pg` | valor_np (2 columnas) | no | Meta del cuatrienio (Programación de Gobierno) vigente. | Reprogramada; puede diferir de 'pi_pg' (PI original). |
| 18 | `2024` | `valor_2024` | valor_np (2 columnas) | no | Valor de la vigencia 2024. | Valor por vigencia. Vigencia cerrada: logro alcanzado; vigencia en curso: meta reprogramada (coincide 100 % con el bloque 'LOGRO / REPROGRAMACIÓN PLAN DE ACCIÓN' de Drive). Por confirmar. |
| 19 | `2025` | `valor_2025` | valor_np (2 columnas) | no | Valor de la vigencia 2025. | Valor por vigencia. Vigencia cerrada: logro alcanzado; vigencia en curso: meta reprogramada (coincide 100 % con el bloque 'LOGRO / REPROGRAMACIÓN PLAN DE ACCIÓN' de Drive). Por confirmar. |
| 20 | `2026` | `valor_2026` | valor_np (2 columnas) | no | Valor de la vigencia 2026. | Valor por vigencia. Vigencia cerrada: logro alcanzado; vigencia en curso: meta reprogramada (coincide 100 % con el bloque 'LOGRO / REPROGRAMACIÓN PLAN DE ACCIÓN' de Drive). Por confirmar. |
| 21 | `2027` | `valor_2027` | valor_np (2 columnas) | no | Valor de la vigencia 2027. | Valor por vigencia. Vigencia cerrada: logro alcanzado; vigencia en curso: meta reprogramada (coincide 100 % con el bloque 'LOGRO / REPROGRAMACIÓN PLAN DE ACCIÓN' de Drive). Por confirmar. |
| 22 | `Principal Logro en Función del Cumplimiento` | `principal_logro` | texto | sí | Narrativa reportada por la entidad. |  |
| 23 | `Análisis del Logro` | `analisis_logro` | texto | sí | Análisis del logro reportado. |  |
| 24 | `Dificultades o Gestiones` | `dificultades_gestiones` | texto | sí | Dificultades o gestiones reportadas. |  |

## EVAPLAN · Informe de Plan Indicativo MR

Metas de resultado (MR) de UNA entidad con programación vigente y resultado reportado.

- **Origen:** Descarga de EVAPLAN: 'Informe de Plan Indicativo MR.xlsx'
- **Hoja:** primera hoja · **Encabezados en la fila:** 2
- **Llave:** `codigo_mr`
- **Lector:** `leer_pi_mr_evaplan()`

> Estructura inferida de un archivo de 4 filas; confirmar con una entidad con más metas.

| # | Encabezado original | Campo canónico | Tipo | ¿Vacío? | Descripción | Notas |
|---|---|---|---|---|---|---|
| 1 | `Codigo Entidad` | `codigo_entidad` | codigo | no | Código de la entidad. |  |
| 2 | `Nombre Entidad` | `nombre_entidad` | texto | no | Nombre completo de la entidad. |  |
| 3 | `Código de Meta` | `codigo_mr` | codigo | no | Código de la meta de resultado, 5 dígitos ('99001'). | Equivale a los dígitos 3-7 del código MP asociado. |
| 4 | `Descripción de Meta` | `descripcion_mr` | texto | no | Texto de la meta de resultado. |  |
| 5 | `Codigo Programa` | `programa` | codigo_nombre (2 columnas) | no | Programa del PDD. |  |
| 6 | `Comportamiento del Indicador` | `comportamiento` | texto | no | Tipo de indicador. |  |
| 7 | `Valor Linea Base` | `linea_base` | decimal | sí | Valor de la línea base. |  |
| 8 | `Año Linea Base` | `anio_linea_base` | entero | sí | Año de la línea base. |  |
| 9 | `Periodicidad de Medición` | `periodicidad` | texto | no | Periodicidad de medición. |  |
| 10 | `Unidad de Medida` | `unidad_medida` | texto | no | Unidad de medida. |  |
| 11 | `Variable` | `variables` | texto | no | Definición de variables. |  |
| 12 | `Constante (K)` | `constante_k` | decimal | no | Constante de la fórmula. |  |
| 13 | `Fórmula` | `formula` | texto | no | Fórmula del indicador. |  |
| 14 | `Resultado` | `resultado` | decimal | no | Resultado reportado en el periodo de corte. |  |
| 15 | `Valor Proyectado` | `valor_proyectado` | decimal | sí | Proyección reportada. |  |
| 16 | `PG` | `valor_pg` | valor_np (2 columnas) | no | Meta del cuatrienio (Programación de Gobierno) vigente. | Reprogramada; puede diferir de 'pi_pg' (PI original). |
| 17 | `2024` | `valor_2024` | valor_np (2 columnas) | no | Valor de la vigencia 2024. | Valor por vigencia. Vigencia cerrada: logro alcanzado; vigencia en curso: meta reprogramada (coincide 100 % con el bloque 'LOGRO / REPROGRAMACIÓN PLAN DE ACCIÓN' de Drive). Por confirmar. |
| 18 | `2025` | `valor_2025` | valor_np (2 columnas) | no | Valor de la vigencia 2025. | Valor por vigencia. Vigencia cerrada: logro alcanzado; vigencia en curso: meta reprogramada (coincide 100 % con el bloque 'LOGRO / REPROGRAMACIÓN PLAN DE ACCIÓN' de Drive). Por confirmar. |
| 19 | `2026` | `valor_2026` | valor_np (2 columnas) | no | Valor de la vigencia 2026. | Valor por vigencia. Vigencia cerrada: logro alcanzado; vigencia en curso: meta reprogramada (coincide 100 % con el bloque 'LOGRO / REPROGRAMACIÓN PLAN DE ACCIÓN' de Drive). Por confirmar. |
| 20 | `2027` | `valor_2027` | valor_np (2 columnas) | no | Valor de la vigencia 2027. | Valor por vigencia. Vigencia cerrada: logro alcanzado; vigencia en curso: meta reprogramada (coincide 100 % con el bloque 'LOGRO / REPROGRAMACIÓN PLAN DE ACCIÓN' de Drive). Por confirmar. |
| 21 | `Principal Logro en Función del Cumplimiento` | `principal_logro` | texto | sí | Narrativa reportada por la entidad. |  |
| 22 | `Análisis del Logro` | `analisis_logro` | texto | sí | Análisis del logro reportado. |  |
| 23 | `Dificultades o Gestiones` | `dificultades_gestiones` | texto | sí | Dificultades o gestiones reportadas. |  |

## EVAPLAN · Centralizadas (Plan de Acción)

Actividades de proyectos de inversión de UNA entidad, con presupuesto y avance de la vigencia.

- **Origen:** Descarga de EVAPLAN: 'Centralizadas.xlsx'
- **Hoja:** primera hoja · **Encabezados en la fila:** 2
- **Llave:** `codigo_actividad`
- **Lector:** `leer_centralizadas()`

> Fila 1 es un título ('EvaPlan'); los encabezados están en la fila 2.

| # | Encabezado original | Campo canónico | Tipo | ¿Vacío? | Descripción | Notas |
|---|---|---|---|---|---|---|
| 1 | `ID` | `id_registro` | codigo | no | Identificador interno de EVAPLAN. |  |
| 2 | `Cod.Entidad` | `codigo_entidad` | codigo | no | Código de la entidad. |  |
| 3 | `Nombre.Entidad` | `nombre_entidad` | texto | no | Nombre ABREVIADO y con caracteres perdidos. | No usar como llave: 'SRIA DE EJEMPLO  DE LA INFORM' (faltan tildes). |
| 4 | `Cód. Proyecto` | `codigo_proyecto` | codigo | no | Código del proyecto de inversión ('PI99-000001'). |  |
| 5 | `Nombre Proyecto` | `nombre_proyecto` | texto | no | Nombre del proyecto. |  |
| 6 | `Cód. BPIN` | `bpin` | codigo | no | Código BPIN (13 dígitos). Un proyecto tiene un solo BPIN. |  |
| 7 | `Cód. MP` | `codigo_mp` | codigo | no | Meta de producto a la que contribuye la actividad. |  |
| 8 | `Descripción MP` | `descripcion_mp` | texto | no | Texto de la meta de producto. |  |
| 9 | `Cód.Producto MGA` | `codigo_producto_mga` | codigo | no | Producto MGA (7 dígitos). | Siempre igual a los últimos 7 caracteres del código MP. |
| 10 | `Producto MGA` | `producto_mga` | texto | no | Nombre del producto MGA. |  |
| 11 | `Cod.Indicador Producto MGA` | `codigo_indicador_producto_mga` | codigo | no | Indicador de producto MGA (9 dígitos). | Normalmente producto + '00', no siempre. |
| 12 | `Indicador Producto MGA` | `indicador_producto_mga` | texto | no | Nombre del indicador de producto. |  |
| 13 | `Cód. Actividad` | `codigo_actividad` | codigo | no | Código de la actividad: '<proyecto>/a/b/cc/dd' (5 partes separadas por '/'). | Empieza siempre por el código del proyecto. |
| 14 | `Nombre Actividad` | `nombre_actividad` | texto | no | Nombre de la actividad. |  |
| 15 | `Cód. Fondo` | `codigo_fondo` | codigo | no | Código de la fuente de financiación. |  |
| 16 | `Nombre Fondo` | `nombre_fondo` | texto | no | Nombre de la fuente de financiación. |  |
| 17 | `Ppto. Inicial` | `ppto_inicial` | moneda | no | Presupuesto inicial (COP). | Llega como texto con puntos de miles ('2.339.400.000'). |
| 18 | `Ppto. Definitivo` | `ppto_definitivo` | moneda | no | Presupuesto definitivo (COP). |  |
| 19 | `Ppto. Total Obligaciones` | `ppto_obligaciones` | moneda | no | Total obligado (COP). | Mezcla texto y entero 0 en la misma columna. |
| 20 | `Ppto. Disponible` | `ppto_disponible` | moneda | no | Saldo aún no comprometido (COP). | Invariante observado: disponible ≤ definitivo − obligaciones. |
| 21 | `Ppto. Gestión` | `ppto_gestion` | moneda | sí | Presupuesto de gestión. | Vacío en toda la muestra. |
| 22 | `Cód. Fondo Gestión` | `codigo_fondo_gestion` | codigo | sí | Fondo de gestión. |  |
| 23 | `Fondo Gestión` | `fondo_gestion` | texto | sí | Fondo de gestión. |  |
| 24 | `Estado Actividad` | `estado_actividad` | texto | no | CON EJECUCION / SIN EJECUCION. | Observado: CON EJECUCION ⇔ obligaciones > 0. |
| 25 | `Unid. Medida` | `unidad_medida` | texto | no | Unidad de medida de la actividad. |  |
| 26 | `Complemento` | `complemento` | texto | no | Complemento de la unidad. |  |
| 27 | `Unid. + Compl.` | `unidad_complemento` | texto | no | Unidad + complemento (texto armado). |  |
| 28 | `Cant. Prog. Vig.` | `cant_programada_vigencia` | decimal | no | Cantidad programada en la vigencia. |  |
| 29 | `Cant. Ejec. Vig.` | `cant_ejecutada_vigencia` | decimal | sí | Cantidad ejecutada en la vigencia. | Vacío = sin avance reportado (se trata como 0 en el % de avance). |
| 30 | `% Avance x Actividad` | `avance_actividad_pct` | decimal | no | Avance de la actividad en %. | = ejecutada / programada × 100 (verificado). |
| 31 | `Observación` | `observacion` | texto | sí | Observación libre. El '.' es un marcador de vacío. |  |
| 32 | `Estado` | `estado_registro` | texto | no | Estado del registro (ACTIVO). |  |

## Drive · Plan Indicativo (hoja MP)

Libro maestro del Plan Indicativo 2024-2027: todas las metas de producto de TODAS las entidades.

- **Origen:** Hoja de cálculo en Drive '<fecha>_Plan Indicativo (PI) 2024-2027', hoja 'MP' (URL en st.secrets).
- **Hoja:** `MP` · **Encabezados en la fila:** 2
- **Llave:** `codigo_mp`
- **Lector:** `leer_pi_drive_mp()`

> Las 2 primeras filas son: 1) bandas de bloque (celdas combinadas), 2) encabezados.
> Solo se leen las 103 primeras columnas de las 276. Los bloques posteriores (fuentes de recurso por año, enfoques poblacionales y territoriales, políticas públicas, POTD, IPM) no se leen aún.
> Hay ~448 filas con un par de filas vacías al final.

| Col. | Encabezado original | Campo canónico | Tipo | ¿Vacío? | Descripción | Notas |
|---|---|---|---|---|---|---|
| 1 | `Código MP` | `codigo_mp` | codigo | no | Código de la meta de producto (18 caracteres). |  |
| 2 | `Meta Producto` | `meta_producto` | texto | no | '<código> - <descripción>' de la meta de producto. |  |
| 3 | `Entidad` | `entidad` | codigo_nombre (2 columnas) | no | '9999 - SECRETARÍA…': código y nombre en una celda. |  |
| 4 | `Línea Estrategica` | `linea_estrategica` | codigo_nombre (2 columnas) | no | Línea estratégica del PDD. |  |
| 5 | `Línea Programa` | `programa` | codigo_nombre (2 columnas) | no | Programa del PDD. |  |
| 6 | `Meta Resultado Asociada` | `meta_resultado` | codigo_nombre (2 columnas) | no | MR a la que aporta la MP. |  |
| 7 | `Subprograma` | `subprograma` | codigo_nombre (2 columnas) | no | Subprograma. |  |
| 8 | `Indicador Principal` | `indicador_principal` | texto | sí | Indicador principal. |  |
| 22 | `Unidad de medida` | `unidad_medida` | texto | no | Unidad de medida. |  |
| 23 | `Comportamiento` | `comportamiento` | texto | no | Tipo de indicador. | Hay variantes de mayúsculas ('Incremento flujo'): se normalizan. |
| 24 | `Valor Linea Base` | `linea_base` | decimal | sí | Línea base. | Contiene 'NO DISPONIBLE' en algunas filas. |
| 25 | `Año Linea Base` | `anio_linea_base` | entero | sí | Año de línea base. | Contiene rangos ('2020-2023') que pasan a nulo. |
| 26 | `Periodicidad de medición` | `periodicidad` | texto | no | Periodicidad. | Mayúsculas aquí ('ANUAL'); en EVAPLAN 'Anual'. |
| 27 | `Fecha Actualizacion Indicador` | `fecha_actualizacion_indicador` | fecha | sí | Fecha de última actualización de la ficha del indicador. |  |
| 28 | `Meta PG` | `meta_pg_original` | decimal | sí | PG original del Plan de Desarrollo. |  |
| 29 | `VARIABLES` | `variables` | texto | sí | Definición de variables. |  |
| 30 | `FÓRMULA` | `formula` | texto | sí | Fórmula. |  |
| 31 | `PG 2024-2027.` | `pi_pg` | valor_np (2 columnas) | no | PG del Plan Indicativo original. | Encabezado con punto final (distinto de 'PG 2024-2027' de la pos. 35). |
| 32 | `2024.` | `pi_2024` | valor_np (2 columnas) | no | Programación original 2024. |  |
| 33 | `2025.` | `pi_2025` | valor_np (2 columnas) | no | Programación original 2025. |  |
| 34 | `2026.` | `pi_2026` | valor_np (2 columnas) | no | Programación original 2026. |  |
| 35 | `2027.` | `pi_2027` | valor_np (2 columnas) | no | Programación original 2027. |  |
| 36 | `PG 2024-2027` | `valor_pg` | valor_np (2 columnas) | no | PG vigente (reprogramado). |  |
| 37 | `VAL ALC 2024` | `valor_2024` | valor_np (2 columnas) | no | Valor 2024 (logro). | Valor por vigencia. Vigencia cerrada: logro alcanzado; vigencia en curso: meta reprogramada (coincide 100 % con el bloque 'LOGRO / REPROGRAMACIÓN PLAN DE ACCIÓN' de Drive). Por confirmar. |
| 38 | `VAL ALC 2025` | `valor_2025` | valor_np (2 columnas) | no | Valor 2025 (logro). | Valor por vigencia. Vigencia cerrada: logro alcanzado; vigencia en curso: meta reprogramada (coincide 100 % con el bloque 'LOGRO / REPROGRAMACIÓN PLAN DE ACCIÓN' de Drive). Por confirmar. |
| 39 | `2026` | `valor_2026` | valor_np (2 columnas) | no | Valor 2026 (reprogramado). | Valor por vigencia. Vigencia cerrada: logro alcanzado; vigencia en curso: meta reprogramada (coincide 100 % con el bloque 'LOGRO / REPROGRAMACIÓN PLAN DE ACCIÓN' de Drive). Por confirmar. |
| 40 | `2027` | `valor_2027` | valor_np (2 columnas) | no | Valor 2027 (reprogramado). | Valor por vigencia. Vigencia cerrada: logro alcanzado; vigencia en curso: meta reprogramada (coincide 100 % con el bloque 'LOGRO / REPROGRAMACIÓN PLAN DE ACCIÓN' de Drive). Por confirmar. |
| 41 | `VERIFICACIÓN DEL COMPORTAMIENTO DE META EN REPROGRAMACIÓN` | `verificacion_comportamiento` | texto | sí | Comportamiento verificado por fórmula del libro (ACUMULADO, FLUJO…). | Puede contener 'ERROR' (fórmula fallida). |
| 42 | `EDT…` | `edt` | si_no | sí | ¿Meta con EDT? (el encabezado trae la fecha de corte). |  |
| 43 | `ESTADO DE LA META DE PRODUCTO` | `estado_meta` | texto | sí | EN EJECUCIÓN / CUMPLIDA. |  |
| 55 | `TOTAL RECURSO 2024` | `recurso_total_2024` | moneda | sí | Total de recursos programados 2024 (COP). |  |
| 67 | `TOTAL RECURSO 2025` | `recurso_total_2025` | moneda | sí | Total de recursos programados 2025 (COP). |  |
| 79 | `TOTAL RECURSO 2026` | `recurso_total_2026` | moneda | sí | Total de recursos programados 2026 (COP). |  |
| 91 | `TOTAL RECURSO 2027` | `recurso_total_2027` | moneda | sí | Total de recursos programados 2027 (COP). |  |
| 103 | `TOTAL RECURSO 2024-2027` | `recurso_total_pg` | moneda | sí | Total de recursos del cuatrienio (COP). |  |

## Drive · Plan Indicativo (hoja MR)

Libro maestro: todas las metas de resultado de TODAS las entidades.

- **Origen:** Mismo libro de Drive, hoja 'MR'.
- **Hoja:** `MR` · **Encabezados en la fila:** 2
- **Llave:** `codigo_mr`
- **Lector:** `leer_pi_drive_mr()`

> Encabezados repetidos (PG, 2024…2027 aparecen dos veces): por eso se lee por posición.

| Col. | Encabezado original | Campo canónico | Tipo | ¿Vacío? | Descripción | Notas |
|---|---|---|---|---|---|---|
| 1 | `COD MR` | `codigo_mr` | codigo | no | 'MR99001' → se guarda '99001'. |  |
| 2 | `Meta resultado` | `meta_resultado` | codigo_nombre (2 columnas) | no | '99001 - 99001-TEXTO': el código aparece duplicado; se corrige. |  |
| 3 | `Entidad` | `entidad` | codigo_nombre (2 columnas) | no | Código y nombre de la entidad. |  |
| 4 | `Nombre del Indicador` | `nombre_indicador` | texto | sí | Indicador de resultado. |  |
| 5 | `Linea Estratégica` | `linea_estrategica` | codigo_nombre (2 columnas) | no | Línea estratégica. |  |
| 6 | `Programa Plan` | `programa` | codigo_nombre (2 columnas) | no | Programa. |  |
| 13 | `Unidad de medida` | `unidad_medida` | texto | no | Unidad de medida. |  |
| 14 | `Valor linea Base` | `linea_base` | decimal | sí | Línea base. |  |
| 15 | `Año linea Base` | `anio_linea_base` | entero | sí | Año de línea base. |  |
| 16 | `Comportamiento del indicador` | `comportamiento` | texto | no | Tipo de indicador. | Incluye 'Reducción Anual', que no existe en metas de producto. |
| 17 | `Meta PG` | `meta_pg_original` | decimal | sí | PG original. |  |
| 18 | `Periodicidad de medición` | `periodicidad` | texto | no | Periodicidad. | Contiene el error de digitación 'Semetral'. |
| 19 | `Fecha Actualización Indicador` | `fecha_actualizacion_indicador` | fecha | sí | Última actualización. |  |
| 20 | `VARIABLES` | `variables` | texto | sí | Variables. |  |
| 21 | `FORMULA` | `formula` | texto | sí | Fórmula. |  |
| 22 | `PG` | `pi_pg` | valor_np (2 columnas) | no | PG original. |  |
| 23 | `2024` | `pi_2024` | valor_np (2 columnas) | no | Programación original 2024. |  |
| 24 | `2025` | `pi_2025` | valor_np (2 columnas) | no | Programación original 2025. |  |
| 25 | `2026` | `pi_2026` | valor_np (2 columnas) | no | Programación original 2026. |  |
| 26 | `2027` | `pi_2027` | valor_np (2 columnas) | no | Programación original 2027. |  |
| 27 | `PG` | `valor_pg` | valor_np (2 columnas) | no | PG vigente (reprogramado). |  |
| 28 | `VAL ALC 2024` | `valor_2024` | valor_np (2 columnas) | no | Valor 2024 (logro). |  |
| 29 | `2025` | `valor_2025` | valor_np (2 columnas) | no | Valor 2025. |  |
| 30 | `2026` | `valor_2026` | valor_np (2 columnas) | no | Valor 2026. |  |
| 31 | `2027` | `valor_2027` | valor_np (2 columnas) | no | Valor 2027. |  |
| 32 | `VERIFICACIÓN DEL COMPORTAMIENTO DE META EN REPROGRAMACIÓN` | `verificacion_comportamiento` | texto | sí | Comportamiento verificado. | 27 de 75 filas en 'ERROR'. |

## Vocabularios controlados

Valores esperados en columnas categóricas. Un valor fuera de la lista debe revisarse, no ignorarse.

### Comportamiento del indicador

| Valor | Significado |
|---|---|
| `Incremento Acumulado` | El PG es la SUMA de las metas anuales. |
| `Incremento Capacidad` | Observado: el PG es la SUMA de las metas anuales (por confirmar). |
| `Incremento Flujo` | El PG es el valor del ÚLTIMO año (2027); cada año se mide por separado. |
| `Mantenimiento Stock` | Se mantiene un nivel: todos los años igualan al PG. |
| `Reducción Anual` | Solo en Metas de Resultado: el indicador debe bajar (por confirmar regla del PG). |

### Estado de la actividad (Centralizadas)

| Valor | Significado |
|---|---|
| `CON EJECUCION` | Tiene obligaciones (> 0). |
| `SIN EJECUCION` | Sin obligaciones. |

### Estado de la meta de producto (Drive)

| Valor | Significado |
|---|---|
| `EN EJECUCIÓN` | Meta vigente. |
| `CUMPLIDA` | Meta de producto ya cumplida. |

### Verificación del comportamiento (Drive)

| Valor | Significado |
|---|---|
| `ACUMULADO` | — |
| `FLUJO` | — |
| `MANTENIMIENTO` | — |
| `CAPACIDAD` | — |
| `REDUCCIÓN` | — |
| `ERROR` | La fórmula de verificación del libro falló (revisar la fila en Drive). |

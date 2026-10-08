# Análisis de las fuentes de información (2 de octubre de 2026)

Primer análisis de las descargas de EVAPLAN y del Plan Indicativo en Drive. **Muestra:** los archivos de UNA
entidad (3 exports de EVAPLAN) contra el libro maestro de Drive (447 metas de producto, 75 metas de resultado,
49 entidades). Los datos reales no se incluyen en el repositorio (es público); los ejemplos ficticios que reproducen
estas rarezas están en `data/ejemplos/`.

Estado de cada afirmación: **✅ verificada** con los archivos · **❓ por confirmar** con el equipo (ver
[PREGUNTAS_ABIERTAS.md](PREGUNTAS_ABIERTAS.md)).

## 1. Qué fuentes hay y cómo se relacionan

```
Plan Indicativo (Drive)  ──────────────── libro maestro, TODAS las entidades, 10 hojas (usamos MP y MR)
        │
EVAPLAN (descargas por entidad)
  ├─ Informe de Plan Indicativo MR   metas de resultado + resultado reportado
  ├─ Informe de Plan Indicativo MP   metas de producto  + resultado reportado
  └─ Centralizadas                   actividades de proyectos: presupuesto y avance de la vigencia

Jerarquía de llaves (✅):
  Meta de resultado (MR, 5 dígitos: 99002)
    └─ Meta de producto (MP, 18 caracteres) = "MP" + MR(5) + subprograma(2) + consecutivo(2) + producto MGA(7)
         └─ Proyecto de inversión (PI99-000001; un solo BPIN)
              └─ Actividad (PI99-000001/1/1/01/07: el código empieza por el del proyecto)
```

El código MP contiene el MR, el programa, el subprograma y el producto MGA; en los archivos analizados esas
partes coincidieron con las columnas correspondientes en todas las filas. **La llave de entidad es el código
(`9999`), no el nombre**: el nombre llega de tres formas distintas (completo, `código - nombre` en una celda, y
abreviado con caracteres perdidos en Centralizadas).

## 2. Hallazgos

### H1 · El export de EVAPLAN coincide con el bloque vigente de Drive, no con el Plan Indicativo original ✅ (confirmado por el equipo)
Para las 10 metas comunes, los 5 valores (PG y 2024-2027) del export de EVAPLAN son **idénticos** a las columnas
`PG 2024-2027`, `VAL ALC 2024`, `VAL ALC 2025`, `2026`, `2027` de Drive (bloque *LOGRO / REPROGRAMACIÓN PLAN DE
ACCIÓN*), incluidas las celdas `NP`. En cambio, frente al bloque original (`PLAN INDICATIVO - PI`) **3 de las 10
metas difieren**: son metas reprogramadas.
- *Implicación:* para seguimiento hay que comparar contra el bloque vigente. El PI original sirve solo para
  auditar reprogramaciones.
- ✅ **Confirmado:** en las vigencias cerradas esos valores son *logro alcanzado*; en las pendientes, la *meta*, que se
  modifica si se reprograma. El técnico **renombra el encabezado** de la columna del año que cierra (`2025` →
  `VAL ALC 2025`) en las columnas `AK:AN` de la hoja MP. Por eso el lector acepta ambos nombres y la vigencia en
  curso se detecta sola: es el primer año **sin** `VAL ALC` (hoy, 2026). Respaldo en los datos: la regla de
  Mantenimiento Stock se rompe 17 veces en este bloque (logros menores a la meta) y ninguna en el original.
- ⚠️ En la hoja **MR** solo `2024` está marcado; `2025` ya cerró pero conserva el encabezado simple. La herramienta
  lo reporta (`vigencia_cerrada_sin_marca_logro`): puede que el logro 2025 de las metas de resultado no se haya
  cargado.

### H2 · Faltaban 2 de 12 metas de la entidad en el export: son metas SIN REPORTE ✅/❓
Drive tiene 12 metas de la entidad; el export de EVAPLAN, 10. Según el equipo, la causa más probable es que la
dependencia **no reportó** esas metas (EVAPLAN solo exporta lo reportado). En los valores no hubo diferencias hoy;
la diferencia está en la cobertura.
- *Implicación:* el universo de metas de una dependencia es **el Plan Indicativo de Drive**, no el export. La
  página lo usa así y muestra las metas sin reporte como resultado de seguimiento (`sin_reporte`).

### H3 · Las reglas del comportamiento del indicador casi siempre se cumplen en la programación original ✅/❓
Prueba sobre el **PI original** de las 447 metas de producto del libro (`pg_vs_anios`):

| Comportamiento | Regla observada | Metas | Incumplen |
|---|---|---|---|
| Incremento Acumulado | PG = suma de los 4 años | 250 | 7 |
| Incremento Capacidad | PG = valor de 2027: nivel alcanzado (✅ confirmado 8-oct; guía DNP) | 4 | 2 |
| Incremento Flujo | PG = valor de 2027 | 114 | 5 (p. ej. 2027 = 0 con PG > 0) |
| Mantenimiento Stock | todos los años = PG | 79 | 0 |
| Reducción Anual (solo MR) | ❓ | — | no se valida |

Son **14 metas** (3 % del libro) que no cumplen; una de ellas es de la entidad analizada (un acumulado cuyos años
suman 2,5 veces el PG y que luego fue reprogramado). Pueden ser errores de digitación o que la regla no aplique
a esos casos. Por eso la regla se reporta como *advertencia*, no como error.

*Actualización 8-oct:* la tabla de arriba usaba la regla anterior para Capacidad (suma). Con la regla confirmada (PG =
nivel de 2027) son 2 las metas de Capacidad del PI original que no cumplen (escritas como incrementos que se suman). La
reprogramación vigente corrigió las 7 de Acumulado y las 5 de Flujo, y las 4 de Capacidad están escritas como nivel
alcanzado con 2027 = PG: el plan original tenía errores de digitación y la regla queda confirmada.

**La regla solo es válida sobre programación.** Aplicada al bloque vigente (que trae logros en vigencias
cerradas) produce 27 falsas alarmas, 17 de ellas de Mantenimiento Stock: es otra señal de que ese bloque mezcla
logro y meta (H1).

### H4 · Señales de seguimiento en Centralizadas ✅
- **19 de 19** actividades cumplen: obligaciones ≤ definitivo; disponible ≤ definitivo − obligaciones;
  `% avance = ejecutada / programada × 100`; `CON EJECUCION` ⇔ obligaciones > 0.
- **2 actividades con obligaciones y sin ningún avance físico reportado** (una con una cifra muy significativa).
  Es el tipo de hallazgo que debe salir automáticamente (`financiero_sin_fisico`).
- **4 de 10 metas no tienen actividades** en Centralizadas (`meta_sin_actividades`, informativo).
- **2 metas con presupuesto definitivo mayor a los recursos 2026 programados en el PI** (112 % y 148 %). No es
  un invariante (Centralizadas no cubre todas las fuentes de financiación ❓), pero es una señal de revisión.

### H5 · El resultado de la meta no se puede derivar de las actividades ❓
En una meta de producto, el `Resultado` de EVAPLAN no coincide con la cantidad ejecutada de sus actividades
(es mayor que la de cada una y que su suma); en otra, el resultado está en porcentaje y las actividades en
número de personas. Las
actividades miden su propia unidad; la meta mide el indicador de producto. **No se puede calcular el
cumplimiento de la meta sumando actividades**: se necesita el `Resultado` reportado y compararlo con lo programado
en el periodo. Pregunta 1 y 6.

### H6 · Rarezas de formato que el lector ya absorbe ✅
| Fuente | Rareza | Tratamiento |
|---|---|---|
| EVAPLAN (todos) | Fila 1 es un título (`EvaPlan`), encabezados en la fila 2 | `fila_encabezado = 1` |
| EVAPLAN | Años como encabezado numérico (`2026.0`) | se normalizan a `2026` |
| EVAPLAN | `'.'` como "vacío" en observaciones y análisis | → nulo |
| EVAPLAN Centralizadas | Dinero como texto `'2.339.400.000'` y entero `0` en la misma columna | `moneda()` |
| EVAPLAN Centralizadas | Códigos numéricos (BPIN, producto MGA) | se guardan como texto |
| EVAPLAN Centralizadas | Nombre de entidad truncado y sin tildes | no se usa como llave |
| Drive | `NP` (No Programado) dentro de columnas numéricas (136 celdas en el libro) | columna `<campo>_np`; **NP ≠ 0** |
| Drive | `NO DISPONIBLE` en línea base; rangos `2020-2023` en año de línea base | → nulo |
| Drive | `Incremento flujo` (minúscula), `ANUAL` vs `Anual` en EVAPLAN, `Semetral` (error de digitación) | se normaliza el comportamiento; el resto se documenta |
| Drive | Celda `ERROR` en *VERIFICACIÓN DEL COMPORTAMIENTO* (1 de 447 MP, **27 de 75 MR**) | se conserva y se reporta |
| Drive | Encabezados con punto final (`2024.`) o salto de línea (`VAL ALC 2024\n`); encabezados repetidos en MR | lectura por **posición** + verificación del encabezado |
| Drive | Entidad como `9999 - NOMBRE`; MR como `MR99001` y meta `99001 - 99001-TEXTO` (código duplicado) | se separan y limpian |
| Drive | Fechas como texto; filas vacías al final | se convierten / descartan |

### H7 · La estructura del libro de Drive es frágil ✅
El libro tiene 276 columnas en la hoja MP, encabezados repetidos, y columnas con fecha de corte en el nombre
(`EDT (corte 02/03/2026)`). Si alguien inserta una columna, una lectura "por nombre" se corrompería sin avisar. El
lector valida el encabezado esperado en cada posición y falla con un mensaje claro (`EsquemaError`).

## 2b. Prueba con 10 dependencias reales (2 de octubre de 2026)
Tras la primera versión de la página se probó con los exports de 10 dependencias (Mujer, Paz, Rentas, Vivienda,
Desarrollo Social, Turismo, Transparencia, DADI, Tecnologías y General; cortes de junio, contra el Plan Indicativo de
Drive de octubre). Ninguna rompió la lectura. Las cifras se verificaron de forma independiente (pandas puro) y
coinciden. Lo que mostraron y se corrigió:

### H8 · Cada fila de Centralizadas es un REGISTRO presupuestal, no una actividad ✅
El `ID` es único; el código de actividad se repite (hasta 4 filas) con distinto presupuesto y, a veces, distinto estado,
avance y observación. Se había asumido `codigo_actividad` único y daba falsos **errores** en Paz y Vivienda. Ahora la
llave es `ID`, se cuentan actividades y registros por separado y los presupuestos se suman.
- ✅ **Decisión del equipo:** no hay forma sencilla de agrupar por actividad (el código no coincide siempre y a veces
  difiere a propósito por una palabra o un punto). La unidad de análisis es el **registro presupuestal**; el avance se
  promedia por registro, como la página original.

### H9 · PA y PI tienen responsables distintos: hay metas compartidas ✅ (nota SODR del 1-oct)
El PA (actividades) lo reporta el centro gestor del proyecto; el PI (metas) solo el coordinador de la meta, aunque la
ejecute otra dependencia. Por eso, en el archivo de una dependencia: (a) sus metas pueden recibir aportes de proyectos
**ajenos** y (b) sus proyectos pueden aportar a metas de **otra** dependencia. Consecuencias: "meta sin actividades" y
"avance sin obligaciones" son señales para validar con la otra dependencia, no necesariamente errores; y "actividad sin
meta en el PI" pasó de error a advertencia. Una integración con el Z023 consolidado resolvería el cruce completo.

### H10 · Las observaciones ya explican muchas "obligaciones sin avance" ✅
En Mujer, 30 de 31 registros con obligaciones y sin avance traen una observación del tipo "el entregable está para el
mes de octubre". Se separaron: **sin observación = advertencia; con observación = informativo**. Y solo cuentan si la
actividad tiene cantidad programada en la vigencia (24 de 67 registros de Mujer no la tienen).

### H11 · La justificación de un avance 0: criterio de la líder y práctica real ✅
Según la líder del equipo debe estar en *Dificultades* (a veces se es flexible, pero esa decisión es posterior). En los
datos: Mujer la escribe en *Análisis del logro* (7 de 7 metas con resultado 0; ninguna en Dificultades) y Vivienda en
*Dificultades* (10 de 12). Por eso el criterio **estricto es el valor por defecto** y existe una casilla "criterio
flexible" que también acepta el Análisis. Efecto en Mujer: 7 metas con alertas en estricto, 1 en flexible.

### H12 · Con exports de junio y Drive de octubre aparecen diferencias reales de programación ✅
En Vivienda, 2 metas tienen una meta 2026 distinta entre el export (junio) y Drive (octubre): el escenario de "export
desactualizado". La app calcula con Drive y ahora lo avisa en la tabla principal (`meta_vigencia_difiere_del_export`).

### H13 · Otros hallazgos de calidad reales
- DADI: 2 registros con obligaciones (598 y 17 millones) y presupuesto definitivo 0.
- Vivienda: el producto MGA de Centralizadas difiere en 1 dígito del que lleva el código de la meta (2 registros).
- Las validaciones del libro de Drive se aplicaban a las 49 entidades; ahora solo a las de los archivos cargados.

## 3. Decisiones tomadas
1. **Un diccionario único en código** (`src/evaplan/esquemas.py`) del que salen los lectores y esta
   documentación (`docs/DICCIONARIO_DE_DATOS.md`).
2. **Nombres canónicos** en `snake_case` y tipos explícitos; `NP` y vacío se distinguen; los códigos son texto.
3. **Los lectores fallan fuerte** si cambia la estructura; las validaciones **reportan, nunca corrigen** datos.
4. **Severidades:** `error` (integridad rota), `advertencia` (revisar), `info`. Lo que está "por confirmar" nunca
   es `error`.
5. **Comparar siempre contra el bloque vigente de Drive**, y usar el original solo para auditar reprogramaciones.

## 4. Lo que aún no se ha analizado
- Resto de hojas del libro de Drive (`Reprogramaciones`, `Metas Totales`, `DATA`, `Desglose PP…`, etc.).
- Bloques de fuentes de recurso por año, enfoques poblacionales/territoriales y políticas públicas (columnas
  103-275 de la hoja MP).
- Export de MR de EVAPLAN con más de 4 filas; Centralizadas de más de una entidad.
- Los otros insumos de la página POAI 2027 (Cadena de Valor `.docx`, MGA `.xml`, Z023).

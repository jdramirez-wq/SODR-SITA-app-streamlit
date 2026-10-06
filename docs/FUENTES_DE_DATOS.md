# Fuentes de datos

Resumen de cada fuente. El detalle columna por columna está en [DICCIONARIO_DE_DATOS.md](DICCIONARIO_DE_DATOS.md)
y los hallazgos en [ANALISIS_FUENTES_EVAPLAN.md](ANALISIS_FUENTES_EVAPLAN.md).

| Fuente | Origen | Alcance | Llave | Lector | Ejemplo ficticio |
|---|---|---|---|---|---|
| Plan Indicativo MR | Descarga EVAPLAN | Una entidad | `codigo_mr` | `leer_pi_mr_evaplan` | `ejemplo_PI_MR_evaplan.xlsx` |
| Plan Indicativo MP | Descarga EVAPLAN | Una entidad | `codigo_mp` | `leer_pi_mp_evaplan` | `ejemplo_PI_MP_evaplan.xlsx` |
| Centralizadas | Descarga EVAPLAN | Una entidad | `codigo_actividad` | `leer_centralizadas` | `ejemplo_Centralizadas.xlsx` |
| Plan Indicativo (hoja MP) | Libro maestro en Drive | Todas las entidades | `codigo_mp` | `leer_pi_drive_mp` | `ejemplo_PI_Drive.xlsx` |
| Plan Indicativo (hoja MR) | Libro maestro en Drive | Todas las entidades | `codigo_mr` | `leer_pi_drive_mr` | `ejemplo_PI_Drive.xlsx` |

## Papel de cada fuente
- **Drive (libro maestro):** es la referencia de programación y logros del Plan Indicativo. Se actualiza en el
  propio libro; el bloque vigente (*LOGRO / REPROGRAMACIÓN*) es el que debe usarse para seguimiento.
- **EVAPLAN:** aporta lo que las entidades **reportan** en cada corte (`Resultado`, narrativas) y el plan de
  acción con presupuesto y avance (Centralizadas). Su export de PI puede venir incompleto.
- **Cruce:** MR → MP → proyecto → actividad (ver análisis, sección 1).

## Cómo se leen
```python
from src.evaplan import lectura as L, validaciones as V

pi   = L.leer_pi_mp_evaplan(archivo_subido)         # ruta, URL o st.file_uploader
ce   = L.leer_centralizadas(otro_archivo)
dmp  = L.leer_pi_drive_mp(archivo_o_bytes)          # el enlace de Drive va en el secreto URL_DRIVE_PLAN_INDICATIVO
hallazgos = V.validar_todo(pi_mp_evaplan=pi, centralizadas=ce, drive_mp=dmp)

# o, todo junto (lo que usa la página):
from src.evaplan import pipeline
res = pipeline.ejecutar(archivo_pi, archivo_centralizadas, drive=bytes_del_libro)   # res.matriz, res.hallazgos, res.calidad
```
Si la estructura de un archivo cambia, el lector lanza `EsquemaError` indicando qué columna falló.

## Otros insumos (página POAI 2027, aún sin contrato de datos)
- Cadena de Valor (`.docx`) y reporte MGA (`.xml`). Pendiente analizarlos y añadirlos al diccionario. (El Z023 ya
  tiene contrato de datos, ver abajo.)

## Z023 consolidado (cuarto cuadro opcional de la página)
**Qué es:** repositorio maestro curado que unifica los Z023 de SAP (módulo PPM) del PDD 2024-2027 y corrige los errores de
formulación (metas faltantes, códigos MGA erróneos, área funcional). Libro `Z023_PDD2024-2027_Cons` con 11 hojas; los
datos están en **`Hoja1`** (73 columnas, una fila por actividad y vigencia; ~6.400 filas en 2024-2026).
**Es información no pública**: no va al repositorio ni a una carpeta de lectura abierta. Se sube por sesión con
`st.file_uploader` (cuarto cuadro, `.xlsx` o `.xlsm`) y se usa solo en memoria. El contrato de datos está en
[DICCIONARIO_DE_DATOS.md](DICCIONARIO_DE_DATOS.md) (esquema `z023`, 17 de las 73 columnas) y el lector es `lectura.leer_z023`.

**Qué hace con él la página** (`src/evaplan/aportes.py`):
- Por meta y vigencia lista los **proyectos que le aportan**, separando los de la propia dependencia de los de otras
  dependencias y entidades descentralizadas (metas compartidas). Sale en la ficha de la meta, en el Resumen y en la hoja
  `Aportes_Z023` del Excel.
- Valida el propio Z023 (MP faltante o mal formada, BPIN no válido) y lo cruza con Centralizadas (actividad ausente del
  Z023, meta distinta).

**Llaves comprobadas con el archivo real** (Hoja1, 6.409 filas):
- `PPM: Actividad` es única por fila (llave de la tabla); `PS: Actividad` se repite en pocos casos y falta en ~15 %.
- `PS: Actividad` = `Cód. Actividad` de Centralizadas: las 31 actividades de una dependencia de prueba existen en el Z023.
- `Dependencia` = `Cod.Entidad` de EVAPLAN (centro gestor del proyecto). Hay 48 distintas: 29 dependencias centrales y
  19 entidades descentralizadas (códigos `00xx`).
- Las **entidades descentralizadas no tienen código PS** (el 100 % de sus filas) y **sí aportan a metas** de dependencias
  centrales (p. ej. de Educación): no se excluyen del cruce, se marcan como "Descentralizada" y "sin código PS".
- Una meta puede recibir aportes de varios proyectos (147 de 419 metas) y de varias dependencias (39 metas).
- El código de proyecto de PPM (`PI-102402`) no es el de PS (`PI44-102402`, prefijo de `PS: Actividad`).
- Varias columnas del libro son **fórmulas** (Centro Gestor de la MP, código de producto DNP, llaves DNP, objetivos…). Al
  convertirlo a Hoja de Google llegan como `#ERROR!`; en el `.xlsx` original traen valores. Los errores de fórmula se
  tratan como vacío.
- `Valor de Actividad` llega numérico en el Excel; en una exportación de texto puede venir `' $  3,200,000 '` (se acepta).

**Qué falta:** el DNP cruza con `BPIN + Producto MGA`; la columna del código de producto DNP viene de fórmula y no se
pudo ver con datos reales. Se leerá cuando se confirme que llega con valores en el Excel.

## Insumos candidatos a leerse desde Drive (en lugar de descarga manual)
- Plan Indicativo (ya se lee de Drive en la página POAI).
- Por definir con el equipo: ver [PREGUNTAS_ABIERTAS.md](PREGUNTAS_ABIERTAS.md).

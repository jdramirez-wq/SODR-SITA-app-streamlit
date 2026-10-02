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
- Cadena de Valor (`.docx`), reporte MGA (`.xml`) y Z023 (`.xlsx`, hoja `Hoja1`). Pendiente analizarlos y
  añadirlos al diccionario.

## Z023 consolidado (pendiente de contrato de datos)
**Qué es** (según las notas del equipo del 1-oct): repositorio maestro curado (> 6000 filas) que unifica los Z023 de SAP
(módulo PPM) del PDD 2024-2027 y corrige los errores de formulación (metas faltantes, códigos MGA erróneos, área
funcional). **Es información no pública**: no va al repositorio ni a una carpeta de lectura abierta; se subiría por
sesión con `st.file_uploader` y se usaría solo en memoria.

**Por qué serviría:** liga cada proyecto con su meta de producto y distingue el *Centro Gestor* (dueño del proyecto)
de la *Dependencia responsable* de la meta. Con eso la página podría mostrar, para cada meta, **qué proyectos de otras
dependencias le aportan**, que es justo lo que hoy no se ve en un solo Centralizadas (metas compartidas).

**Llaves probables** (a confirmar con la muestra):
- Código PS de la actividad = `<proyecto>/1/<objetivo específico>/<producto>/<actividad>`, el mismo formato que
  `Cód. Actividad` de Centralizadas.
- DNP cruza con `BPIN + Producto MGA`.
- Los proyectos de entidades descentralizadas solo llegan a PPM (no tienen código PS).

**Para poder hacerlo** hace falta una muestra legible:
1. Abrir `Z023_PDD2024-2027_Cons.xlsm` y guardar una copia como **`.xlsx`** (sin macros) de nombre
   `Z023_muestra.xlsx` en la carpeta `Fuentes EVAPLAN`.
2. Dejar los encabezados y unas 50-100 filas (borrar el resto) de la hoja con los datos consolidados.
3. Opcional: si hay datos sensibles, cambiar nombres de personas o cifras; solo importa la estructura.

## Insumos candidatos a leerse desde Drive (en lugar de descarga manual)
- Plan Indicativo (ya se lee de Drive en la página POAI).
- Por definir con el equipo: ver [PREGUNTAS_ABIERTAS.md](PREGUNTAS_ABIERTAS.md).

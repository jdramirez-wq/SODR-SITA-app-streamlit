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
dmp  = L.leer_pi_drive_mp(url_de_exportacion_xlsx)  # URL en st.secrets, no en el código
hallazgos = V.validar_todo(pi_mp_evaplan=pi, centralizadas=ce, drive_mp=dmp)
```
Si la estructura de un archivo cambia, el lector lanza `EsquemaError` indicando qué columna falló.

## Otros insumos (página POAI 2027, aún sin contrato de datos)
- Cadena de Valor (`.docx`), reporte MGA (`.xml`) y Z023 (`.xlsx`, hoja `Hoja1`). Pendiente analizarlos y
  añadirlos al diccionario.

## Insumos candidatos a leerse desde Drive (en lugar de descarga manual)
- Plan Indicativo (ya se lee de Drive en la página POAI).
- Por definir con el equipo: ver [PREGUNTAS_ABIERTAS.md](PREGUNTAS_ABIERTAS.md).

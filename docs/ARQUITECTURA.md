# Arquitectura

```
Usuario ──> Streamlit Cloud (app.py + pages/)           ← interfaz (delgada)
                 │
                 ▼
            src/evaplan/                                  ← lógica, sin Streamlit
              esquemas.py      diccionario de datos (única fuente de verdad)
              limpieza.py      celdas sucias → valores tipados
              lectura.py       Excel → DataFrames tipados (EsquemaError si cambia la estructura)
              validaciones.py  integridad y cruces → tabla de hallazgos
                 ▲
   Fuentes: descargas de EVAPLAN (file_uploader) + libro del Plan Indicativo en Drive (URL en st.secrets)

scripts/generar_diccionario.py   esquemas.py → docs/DICCIONARIO_DE_DATOS.md
scripts/generar_ejemplos.py      archivos FICTICIOS en data/ejemplos/ (mismas rarezas que los reales)
tests/                           pytest sobre los ejemplos ficticios
```

## Principios
1. **Contrato de datos explícito:** nada se lee "a ojo"; cada columna tiene nombre canónico, tipo y significado.
2. **Fallar fuerte, reportar claro:** una estructura distinta detiene la lectura con un mensaje accionable.
3. **Validar sin corregir:** las reglas devuelven hallazgos (`error`/`advertencia`/`info`) con la fila de origen;
   nunca alteran el dato.
4. **Lógica fuera de la interfaz:** `pages/` solo llama a `src/`. Así se prueba sin abrir la app.
5. **Datos reales fuera del repo** (público): ejemplos ficticios + pruebas.

## Estado de la migración
- ✅ `src/evaplan/`: contrato de datos y validaciones de EVAPLAN + Plan Indicativo.
- ⏳ `pages/1_Auditoria_EVAPLAN.py` y `pages/2_POAI_2027.py` aún tienen su lógica propia; se migrarán de a una
  página, reproduciendo primero sus resultados actuales (ver HOJA_DE_RUTA).

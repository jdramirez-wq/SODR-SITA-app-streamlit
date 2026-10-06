# Arquitectura

```
Usuario ──> Streamlit Cloud (app.py + paginas/)           ← interfaz (delgada)
                 │
                 ▼
            src/evaplan/                                  ← lógica, sin Streamlit
              esquemas.py      diccionario de datos (única fuente de verdad)
              limpieza.py      celdas sucias → valores tipados
              lectura.py       Excel → DataFrames tipados (EsquemaError si cambia la estructura)
              validaciones.py  integridad y cruces entre fuentes → tabla de hallazgos
              seguimiento.py   matriz por meta (hechos objetivos) + hallazgos de seguimiento
              reportes.py      Excel integrado y PDF por meta
              prompts.py       prompt del auditor (texto original, vigencia parametrizada)
              pipeline.py      orquestador: archivos → Resultado (lo que usa la página)
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
4. **Lógica fuera de la interfaz:** `paginas/` solo llama a `src/`. Así se prueba sin abrir la app.
5. **Datos reales fuera del repo** (público): ejemplos ficticios + pruebas.

## Estado de la migración
- ✅ `src/evaplan/`: contrato de datos y validaciones de EVAPLAN + Plan Indicativo.
- ✅ `paginas/1_Auditoria_EVAPLAN.py` (Seguimiento EVAPLAN) ya es una interfaz delgada sobre `pipeline.ejecutar`.
- ⏳ `paginas/2_POAI_2027.py` conserva su lógica propia; se migrará después (ver HOJA_DE_RUTA).

# Arquitectura

```
Usuario ──> Streamlit Cloud (app.py + pages/)
                 ├── Carga de archivos (st.file_uploader): descargas de otras plataformas
                 ├── Lectura de Drive (Google Sheets exportado como xlsx): fuentes organizadas
                 ├── Procesamiento con pandas (limpieza, normalización de códigos, cruces)
                 └── Salidas: tablas en pantalla, Excel, PDF, prompts para el bot auditor
```

## Objetivo de diseño (próximo)
Separar **interfaz** (`pages/`) de **lógica** (`src/`):
- `src/lectura/`  — lectores por fuente (un archivo por plataforma/formato).
- `src/cruces/`   — normalización de llaves y cruces entre fuentes.
- `src/reportes/` — generación de Excel/PDF/prompts.
- `tests/`        — pruebas con archivos de `data/ejemplos/`.

## Llaves de cruce conocidas
- Meta de producto: código `MPxx` (se extrae del texto con `extraer_codigo_numerico`).
- Proyecto: `Cód. Proyecto` + `Nombre Proyecto` (EVAPLAN).

# CLAUDE.md — Contexto del proyecto

## Qué es
Plataforma web en **Streamlit** (código en GitHub, despliegue en Streamlit Cloud) de la
**Subdirección de Ordenamiento y Desarrollo Regional (SODR)** para facilitar el **seguimiento del
Plan de Desarrollo Departamental**: cruzar información de varias plataformas, auditarla y generar
reportes. La usan compañeros del área (no programadores). Se mejora de forma incremental.

## Reglas críticas
- **El repositorio es PÚBLICO.** Nunca commitear datos reales (planes, proyectos, presupuestos,
  personas), credenciales ni enlaces privados. Datos reales → Drive o `st.file_uploader`.
  Archivos de ejemplo ficticios/anonimizados → `data/ejemplos/`. Secretos → `st.secrets`
  (ver `.streamlit/secrets.toml.example`).
- Idioma: interfaz, comentarios, documentación y commits **en español**.
- Trabajar en ramas; `main` es lo que ven los usuarios. Cambios a `main` por Pull Request.
- Herramientas **gratuitas** únicamente (GitHub, Streamlit Cloud, Drive, GitHub Actions).
- El usuario no es desarrollador: explicar decisiones en lenguaje del trámite, no solo técnico.

## Estructura
```
app.py                       Portada y menú de trámites
pages/1_Auditoria_EVAPLAN.py Consolida Plan Indicativo (PI) + Plan de Acción (Centralizadas.xlsx),
                             genera Excel/PDF y un prompt para un bot auditor
pages/2_POAI_2027.py         Control previo de proyectos: Cadena de Valor (.docx), MGA (XML),
                             cruce con PI desde Drive (hoja "MP"), auditoría Z023, prompt IA
data/                        Solo ejemplos ficticios (ver data/README.md)
docs/                        Arquitectura, flujo de trabajo, fuentes de datos, hoja de ruta
.github/                     CI (ruff + compilación + pytest), plantillas de PR e issues
```

## Cómo ejecutar
```
pip install -r requirements-dev.txt
streamlit run app.py
ruff check .        # lint
pytest              # cuando existan pruebas en tests/
```

## Convenciones de código
- Código **por trámite** en `pages/`; lógica reutilizable (limpieza, cruces, reportes) debe ir a
  `src/` como funciones puras sin Streamlit, con pruebas en `tests/`. *Pendiente: las páginas
  actuales mezclan interfaz y lógica; refactorizar de a una página, con archivos de ejemplo.*
- Códigos de cruce: normalizar con `extraer_codigo_numerico` (ej. "MP24 - Nombre" → "MP24").
- Cachear lecturas pesadas con `st.cache_data`; estado entre interacciones con `st.session_state`.
- Dependencias nuevas: añadir a `requirements.txt` y justificarlas en el PR.

## Deuda técnica conocida
- `pages/2_POAI_2027.py` (~1070 líneas) y `pages/1_Auditoria_EVAPLAN.py` (~460) son monolíticos.
- El enlace de Drive del Plan Indicativo está escrito en `pages/2_POAI_2027.py` (`URL_DRIVE_EXCEL`);
  debe pasar a `st.secrets` y la hoja debe tener permisos acordes (ver docs/HOJA_DE_RUTA.md).
- Sin pruebas automáticas; `requirements.txt` sin versiones fijadas.
- Lint de CI limitado a errores reales; ampliar al ordenar el código.

## Qué necesito del usuario para avanzar
Estructura (hojas/columnas/llaves de cruce) de los Excel de cada plataforma — mejor un ejemplo
anonimizado — documentada en `docs/FUENTES_DE_DATOS.md`.

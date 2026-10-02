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
pages/1_Auditoria_EVAPLAN.py SEGUIMIENTO EVAPLAN (página en foco): cruza Plan Indicativo (Drive + EVAPLAN) con
                             Centralizadas; matriz por meta, hallazgos, Excel/PDF y prompt del auditor. Interfaz
                             delgada sobre src/evaplan/pipeline.py
pages/2_POAI_2027.py         (CONGELADA por ahora) Control previo de proyectos: Cadena de Valor (.docx), MGA (XML),
                             cruce con PI desde Drive (hoja "MP"), auditoría Z023, prompt IA
src/evaplan/                 Contrato de datos (SIN Streamlit): esquemas.py (diccionario), limpieza.py,
                             lectura.py (lectores tipados), validaciones.py (reglas y cruces), seguimiento.py
                             (matriz por meta), reportes.py (Excel/PDF), prompts.py, pipeline.py (orquestador)
scripts/                     generar_diccionario.py (docs desde esquemas), generar_ejemplos.py (datos ficticios)
tests/                       pytest sobre los ejemplos ficticios de data/ejemplos/
data/                        Solo ejemplos ficticios (ver data/README.md)
docs/                        DICCIONARIO_DE_DATOS (generado), ANALISIS_FUENTES_EVAPLAN, REGLAS_DE_NEGOCIO,
                             PREGUNTAS_ABIERTAS, FUENTES_DE_DATOS, ARQUITECTURA, FLUJO_DE_TRABAJO, HOJA_DE_RUTA
.github/                     CI (ruff + compilación + pytest), plantillas de PR e issues
```

## Cómo ejecutar
```
pip install -r requirements-dev.txt
streamlit run app.py
ruff check .        # lint
pytest              # pruebas (usan data/ejemplos, no datos reales)
python scripts/generar_diccionario.py   # tras cambiar src/evaplan/esquemas.py (una prueba lo exige)
python scripts/generar_ejemplos.py      # regenera los archivos ficticios
```

## Convenciones de código
- Código **por trámite** en `pages/` (interfaz delgada); lógica reutilizable en `src/` como funciones puras
  sin Streamlit, con pruebas en `tests/`. *Pendiente: las 2 páginas actuales aún mezclan interfaz y lógica;
  migrarlas de a una a `src/evaplan`, reproduciendo primero sus resultados.*
- **Contrato de datos:** toda columna de una fuente se define en `src/evaplan/esquemas.py` (nombre canónico,
  tipo, significado). Para leer un archivo se usa `lectura.leer_*`; nunca `pd.read_excel` suelto. Si cambia un
  archivo fuente, se cambia el esquema, se regenera el diccionario y se actualiza el ejemplo ficticio.
- Los lectores **fallan fuerte** (`EsquemaError`); las validaciones **reportan, no corrigen**. Lo "por
  confirmar" (docs/REGLAS_DE_NEGOCIO.md) nunca es `error`.
- Tipos: códigos como **texto**; `NP` (No Programado) ≠ 0 (columna `<campo>_np`); `'.'` = vacío; dinero es-CO
  con `moneda()` (el punto es miles) e indicadores con `decimal()` (el punto es decimal).
- **Hechos, no juicios:** no hay umbrales únicos de cumplimiento (se desconoce el cronograma de ejecución). El código
  calcula cifras y detecta incoherencias objetivas; el veredicto (suficiente / devolver) lo da la persona o el LLM.
  No agregar semáforos con umbrales inventados.
- Drive: el técnico renombra el encabezado del año cerrado (`2025` → `VAL ALC 2025`, columnas AK:AN de la hoja MP).
  La vigencia en curso es el primer año sin `VAL ALC`. Nunca fijar el año en el código (usar `vigencia`).
- El universo de metas de una dependencia es el **Plan Indicativo de Drive**; las que no están en el export de EVAPLAN
  son metas **sin reporte**. El enlace de Drive va en el secreto `URL_DRIVE_PLAN_INDICATIVO`.
- Avance de actividades: promediar **por proyecto de inversión** (lo exige el prompt), además del global.
- Llave de entidad = **código** (9999), nunca el nombre. Llave de meta: `codigo_mp` (18 caracteres) /
  `codigo_mr` (5 dígitos). Para seguimiento comparar contra el bloque **vigente** de Drive, no el original.
- Cachear lecturas pesadas con `st.cache_data`; estado entre interacciones con `st.session_state`.
- Dependencias nuevas: añadir a `requirements.txt` y justificarlas en el PR.

## Deuda técnica conocida
- `pages/2_POAI_2027.py` (~1070 líneas) y `pages/1_Auditoria_EVAPLAN.py` (~460) son monolíticos.
- El enlace de Drive del Plan Indicativo está escrito en `pages/2_POAI_2027.py` (`URL_DRIVE_EXCEL`);
  debe pasar a `st.secrets` y la hoja debe tener permisos acordes (ver docs/HOJA_DE_RUTA.md).
- `pages/2_POAI_2027.py` no usa aún `src/evaplan`; `requirements.txt` sin versiones fijadas.
- Las páginas usan `use_container_width` (obsoleto en Streamlit reciente; sigue funcionando con aviso).
- Pendiente revisar el script del compañero al cerrar la primera versión de Seguimiento EVAPLAN.
- Lint de CI limitado a errores reales; ampliar al ordenar el código.

## Qué necesito del usuario para avanzar
Responder `docs/PREGUNTAS_ABIERTAS.md` (confirmaciones rápidas y decisiones de producto). Los archivos reales se analizan desde Drive o adjuntos al chat, nunca se suben al repo.

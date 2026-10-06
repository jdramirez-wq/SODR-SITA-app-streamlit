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
app.py                       Navegación (st.navigation, barra superior): Inicio, Seguimiento EVAPLAN (/Auditoria_EVAPLAN),
                             POAI 2027 (/POAI_2027). Rutas absolutas en interfaz/rutas.py
pages/                       SOLO compatibilidad: la app de prueba de Streamlit Cloud arranca desde pages/1_Auditoria_EVAPLAN.py;
                             estos archivos cargan app.py. Las url_path coinciden con estos nombres para evitar 'Page not found'.
                             No poner páginas reales aquí
paginas/1_Auditoria_EVAPLAN.py SEGUIMIENTO EVAPLAN (página en foco): cruza Plan Indicativo (Drive + EVAPLAN) con
                             Centralizadas; matriz por meta, hallazgos, Excel/PDF y prompt del auditor. Interfaz
                             delgada sobre src/evaplan/pipeline.py
paginas/2_POAI_2027.py         (CONGELADA por ahora) Control previo de proyectos: Cadena de Valor (.docx), MGA (XML),
                             cruce con PI desde Drive (hoja "MP"), auditoría Z023, prompt IA
interfaz/                    Componentes visuales de Streamlit: estilos.py (paleta, tarjetas, alertas), portada.py, logo/icono SVG
                             y seguimiento.py (vistas de la
                             página). Solo dibujan; qué se muestra lo decide src/evaplan/vista.py (probado). Tema en .streamlit/config.toml
src/evaplan/                 Contrato de datos (SIN Streamlit): esquemas.py (diccionario), limpieza.py,
                             lectura.py (lectores tipados), validaciones.py (reglas y cruces), seguimiento.py
                             (matriz por meta), aportes.py (proyectos por meta desde el Z023), recordatorios.py (cierre de año), periodo.py,
                             reportes.py (Excel/PDF), prompts.py, pipeline.py (orquestador)
scripts/                     generar_diccionario.py (docs desde esquemas), generar_ejemplos.py (datos ficticios)
tests/                       pytest sobre los ejemplos ficticios de data/ejemplos/
data/                        Solo ejemplos ficticios (ver data/README.md)
docs/                        DICCIONARIO_DE_DATOS (generado), ANALISIS_FUENTES_EVAPLAN, REGLAS_DE_NEGOCIO,
                             PREGUNTAS_ABIERTAS, FUENTES_DE_DATOS, ARQUITECTURA, FLUJO_DE_TRABAJO, HOJA_DE_RUTA, PASO_A_MAIN
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
- Código **por trámite** en `paginas/` (interfaz delgada; no se usa `pages/` porque choca con la navegación de app.py); lógica reutilizable en `src/` como funciones puras
  sin Streamlit, con pruebas en `tests/`. *Pendiente: las 2 páginas actuales aún mezclan interfaz y lógica;
  migrarlas de a una a `src/evaplan`, reproduciendo primero sus resultados.*
- **Contrato de datos:** toda columna de una fuente se define en `src/evaplan/esquemas.py` (nombre canónico,
  tipo, significado). Para leer un archivo se usa `lectura.leer_*`; nunca `pd.read_excel` suelto. Si cambia un
  archivo fuente, se cambia el esquema, se regenera el diccionario y se actualiza el ejemplo ficticio.
- Los lectores **fallan fuerte** (`EsquemaError`); las validaciones **reportan, no corrigen**. Lo "por
  confirmar" (docs/REGLAS_DE_NEGOCIO.md) nunca es `error`.
- **Formato único de cifras** (`src/evaplan/formato.py`) en pantalla, PDF, Excel y textos de alertas: porcentajes SIEMPRE 0-100
  con `%` (`22,3 %`), pesos `$ 3.884.965.483`, coma decimal, "sin dato" ≠ 0. Internamente las razones son fracciones 0-1
  (`COLUMNAS_PORCENTAJE`); se convierten solo al mostrar/exportar (`reportes.matriz_legible`). Nada de emojis en el PDF.
- **PDF para IA:** guía de lectura al inicio, bloque por meta con secciones numeradas e INICIO/FIN, y las condiciones objetivas de
  las Alertas Tipo 1-3 del prompt (`condiciones.py`, umbrales del propio prompt). Probado con un modelo sencillo (Haiku).
- Tipos: códigos como **texto**; `NP` (No Programado) ≠ 0 (columna `<campo>_np`); `'.'` = vacío; dinero es-CO
  con `moneda()` (el punto es miles) e indicadores con `decimal()` (el punto es decimal).
- **Hechos, no juicios:** no hay umbrales únicos de cumplimiento (se desconoce el cronograma de ejecución). El código
  calcula cifras y detecta incoherencias objetivas; el veredicto (suficiente / devolver) lo da la persona o el LLM.
  No agregar semáforos con umbrales inventados.
- Drive: el técnico renombra el encabezado del año cerrado (`2025` → `VAL ALC 2025`, columnas AK:AN de la hoja MP).
  La vigencia en curso es el primer año sin `VAL ALC`. Nunca fijar el año en el código (usar `vigencia`).
- El universo de metas de una dependencia es el **Plan Indicativo de Drive**; las que no están en el export de EVAPLAN
  son metas **sin reporte**. El enlace de Drive va en el secreto `URL_DRIVE_PLAN_INDICATIVO`.
- `Resultado` = último reporte **acumulado de la vigencia**. `Valor Proyectado` = proyección de cierre de la
  dependencia (campo creado nov-2025; puede venir vacío; misma escala que la meta de la vigencia).
- Alcance actual: solo **metas de producto** (MP). Las metas de resultado (MR) quedan fuera por ahora.
- **Centralizadas:** cada fila es un REGISTRO presupuestal (llave `id_registro`); el código de actividad se repite. Los
  presupuestos se suman y el avance se promedia por registro.
- **PA ≠ PI:** el PA (Centralizadas) lo reporta el centro gestor del proyecto; el PI (metas) solo el coordinador de la meta.
  Hay metas compartidas: "meta sin actividades"/"avance sin obligaciones" pueden deberse a proyectos de otra dependencia.
- Un avance 0 se justifica en *Dificultades* (lineamiento de la líder del equipo). Existe `criterio_flexible` (casilla en la
  página, apagada por defecto) que también acepta *Análisis del logro*; esa decisión es del equipo, no se cambia sola.
- **Drive prevalece** sobre el export de EVAPLAN (el operador a veces no lo tiene actualizado).
- **No agrupar por actividad**: el código de actividad no es confiable (varía a propósito). La unidad es el registro.
- Quien reporta una meta compartida debe conocer el avance de las otras dependencias: los avisos no se excusan.
- **Z023 consolidado:** cuarto cuadro opcional (`leer_z023`, hoja `Hoja1`, `.xlsx`/`.xlsm`). Muestra por meta los proyectos que
  le aportan (propios y de otras entidades, incluidas descentralizadas `00xx`, que no tienen código PS). Llave de la fila =
  `ppm_actividad`; `ps_actividad` = `Cód. Actividad` de Centralizadas. Los errores de fórmula (`#ERROR!`) son vacío.
- **Descentralizadas:** misma estructura de archivos que las centrales, pero su código de entidad difiere entre EVAPLAN (1216)
  y el Z023 (0006): se enlazan por nombre (`aportes.equivalencias_z023`). Su actividad es el código PPM (sin `/`) y su Plan de
  Acción incluye proyectos de otras dependencias. Lo propio/ajeno se decide por el código en el Z023.
- **Periodo de revisión** (`periodo.py`): tipo (`parcial`, `proyectado`, `cierre`) + mes de corte (1-12; por defecto el último mes
  cerrado). El bloque de temporalidad del prompt se arma con ellos (conserva los textos del equipo para junio y cortes tempranos).
  Los nombres de periodo anteriores se aceptan por compatibilidad (`como_periodo`).
- **Recordatorios de cierre** (`recordatorios.py`): solo en revisiones de cierre (proyectado o definitivo). Certificado financiero de descentralizadas y
  certificado del avance por gestión (todas). No son hallazgos: van a la página y al prompt como advertencia.
- **Información no pública:** no guardar el Z023 consolidado ni datos similares en el repo ni en carpetas de lectura
  abierta; se subirían por sesión (`st.file_uploader`) y solo se usan en memoria.
- El indicador "con alertas" cuenta solo advertencias y errores; lo informativo no suma.
- Avance de actividades: promediar **por proyecto de inversión** (lo exige el prompt), además del global. Hay DOS promedios:
  el de TODAS las actividades (**prima** para el análisis; era el de la versión original) y el de las que tienen obligaciones
  (complementario, `avance_actividades_con_obligaciones`). Se entregan ambos y el prompt dice cuál prima. Un % de avance vacío
  con cantidad programada cuenta como 0. Sumas totalmente vacías = "sin dato" (no 0).
- Llave de entidad = **código** (9999), nunca el nombre. Llave de meta: `codigo_mp` (18 caracteres) /
  `codigo_mr` (5 dígitos). Para seguimiento comparar contra el bloque **vigente** de Drive, no el original.
- **Interfaz:** lo urgente primero y lo informativo a un clic (expanders cerrados). Una sola pantalla de resultados (cifras →
  lista de metas → ficha), sin pestañas obligatorias; detalle técnico plegado. En Markdown escapar `$` (si no, se vuelve fórmula).
- Cachear lecturas pesadas con `st.cache_data`; estado entre interacciones con `st.session_state`.
- **F5 no borra:** `interfaz/memoria.py` copia lo listado en `MEMORIA` (resultados y configuración) a la memoria del
  servidor bajo una clave aleatoria en la dirección (`?sesion=`). Vence a las 8 h sin uso o al reiniciar la app; "Borrar
  resultados" la elimina. Nunca en disco. Los controles que se recuperan usan `key=` y valor inicial con `setdefault`
  (no `value=`). POAI (congelada) aún no la usa.
- Dependencias nuevas: añadir a `requirements.txt` y justificarlas en el PR.

## Deuda técnica conocida
- `paginas/2_POAI_2027.py` (~1070 líneas) y `paginas/1_Auditoria_EVAPLAN.py` (~460) son monolíticos.
- El enlace de Drive del Plan Indicativo está escrito en `paginas/2_POAI_2027.py` (`URL_DRIVE_EXCEL`);
  debe pasar a `st.secrets` y la hoja debe tener permisos acordes (ver docs/HOJA_DE_RUTA.md).
- `paginas/2_POAI_2027.py` no usa aún `src/evaplan`; `requirements.txt` solo fija la versión mínima de Streamlit.
- `paginas/2_POAI_2027.py` aún usa `use_container_width` (obsoleto; las vistas nuevas usan `width="stretch"`).
- Pendiente revisar el script del compañero al cerrar la primera versión de Seguimiento EVAPLAN.
- Lint de CI limitado a errores reales; ampliar al ordenar el código.

## Qué necesito del usuario para avanzar
Responder `docs/PREGUNTAS_ABIERTAS.md` (confirmaciones rápidas y decisiones de producto). Los archivos reales se analizan desde Drive o adjuntos al chat, nunca se suben al repo.

# Preguntas abiertas

Cuando se resuelva una, se mueve a [REGLAS_DE_NEGOCIO.md](REGLAS_DE_NEGOCIO.md) o a una decisión y se borra de aquí.

## Resueltas (2 de octubre de 2026)
| Tema | Respuesta | Dónde quedó |
|---|---|---|
| ¿Qué es `Resultado`? | El **último reporte acumulado** de la dependencia. En los datos es el acumulado de la **vigencia** en curso (es menor que los logros previos sumados en metas acumuladas) | Diccionario, campo `resultado` |
| Bloque vigente de Drive (`AK:AN`) | Vigencia cerrada = logro (el técnico renombra el encabezado a `VAL ALC AAAA`); pendiente = meta, que se modifica si se reprograma | Análisis H1; lector tolerante; vigencia autodetectada |
| Metas ausentes en el export | Probablemente la dependencia **no reportó** | Análisis H2; hallazgo `sin_reporte` |
| ¿Quién usa la herramienta? | Compañeros de la SODR, que reciben los reportes **por dependencia** en EVAPLAN, los descargan y analizan | Página: una dependencia por corrida |
| Umbrales de cumplimiento | **No hay umbrales únicos** (se desconoce el cronograma de ejecución del presupuesto); el juicio lo hace el LLM | Principio de diseño: el código calcula hechos, no semáforos |
| Prompts | Están en el repositorio | `src/evaplan/prompts.py` |
| Script del compañero | Se revisa **al final de la primera versión** | Hoja de ruta, Fase 3 |
| `Resultado` ¿de la vigencia o del cuatrienio? | **Acumulado de la vigencia** | Avance del cuatrienio = logro de vigencias cerradas + resultado |
| `Valor Proyectado` | Campo creado por el operador de EVAPLAN hacia nov-2025 para que la Gobernación anticipara el cierre de las MP; sigue en 2026, puede venir vacío y quizá se retome el próximo mes | Columnas `% proyectado vs meta`, alertas `proyeccion_bajo_meta` y `proyeccion_menor_que_resultado` |
| ¿Incluir metas de resultado (MR)? | **No por ahora**: solo metas de producto | Hoja de ruta (fuera de alcance) |

## Para confirmar (rápidas)
1. **MR 2025:** en la hoja MR del Drive el encabezado 2025 no dice `VAL ALC`. ¿Falta cargar el logro 2025 de las
   metas de resultado, o solo falta renombrar el encabezado? (No afecta a la página mientras solo se usen MP.)
2. **Reglas del PG** para Incremento Flujo, Capacidad y Reducción Anual: 14 metas del PI original no cumplen la regla
   (por ejemplo, Flujo con 2027 = 0 y PG > 0). ¿Son errores de digitación o la regla es otra?

## Surgidas al probar con 10 dependencias reales
3. **Promedio de avance con varios registros por actividad:** una actividad puede tener varios registros (ID) con distinto
   avance (p. ej. 0 % y 7.7 %). Hoy el promedio cuenta cada registro (como la página original). ¿Debe promediarse por
   actividad? ¿Qué valor se toma si los registros difieren?
4. **Justificación del avance 0:** el prompt la pide en *Dificultades* y la circular del 3.er trimestre en *Análisis del
   logro*; en los datos, Mujer usa Análisis y Vivienda Dificultades. La herramienta acepta cualquiera de los dos. ¿Se
   mantiene así?
5. **Actividades con avance 0 y observación vacía (`.`):** la circular prohíbe los vacíos. ¿Activamos una alerta por
   actividad? Hoy solo se alerta si además hay obligaciones.
6. **Metas compartidas:** ¿integramos el *Z023 consolidado* para saber qué proyectos de otras dependencias aportan a
   cada meta? Eliminaría los falsos avisos de "avance sin obligaciones" y "meta sin actividades".

## Decisiones de producto
7. **Prompt:** el bloque opcional "Hechos verificados" queda **activado por defecto** (se puede desmarcar en la barra
   lateral). Se revisa cuando el equipo compare respuestas del LLM con y sin el bloque.
8. **Periodo de revisión:** hoy solo cambia el texto del prompt. ¿Se muestra además una referencia neutral de
   tiempo transcurrido (25 %, 50 %…) junto al avance? No sería umbral: solo contexto.
9. **Histórico:** ¿interesa guardar cada corte para ver la evolución de una dependencia?

## Seguridad
10. **Repo público:** Streamlit Community Cloud indica que **sí admite repos privados** (pide un permiso adicional de
   GitHub, `repo`), aunque no pude abrir su documentación oficial para confirmarlo ni sus límites vigentes.
   ¿Pueden probar a pasar el repo a privado en `share.streamlit.io` (Settings → Repository)?
11. **Libro de Drive:** ¿está compartido como "cualquiera con el enlace"? Su ID sigue en `pages/2_POAI_2027.py`.
    La página de seguimiento ya lee el enlace de un secreto (`URL_DRIVE_PLAN_INDICATIVO`), no del código.

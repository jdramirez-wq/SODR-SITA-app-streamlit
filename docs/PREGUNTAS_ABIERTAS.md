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

## Para confirmar (rápidas)
1. **`Resultado` es acumulado de la vigencia, no del cuatrienio.** Los datos lo sugieren con fuerza (en las metas
   acumuladas, el logro de las vigencias cerradas ya supera al resultado). ¿Es correcto? La herramienta suma
   `logro de vigencias cerradas + resultado` para estimar el avance frente al PG.
2. **`Valor Proyectado`:** ¿es la proyección de la dependencia a cierre de vigencia?
3. **MR 2025:** en la hoja MR del Drive el encabezado 2025 no dice `VAL ALC`. ¿Falta cargar el logro 2025 de las
   metas de resultado, o solo falta renombrar el encabezado?
4. **Reglas del PG** para Incremento Flujo, Capacidad y Reducción Anual: 14 metas del PI original no cumplen la regla
   (por ejemplo, Flujo con 2027 = 0 y PG > 0). ¿Son errores de digitación o la regla es otra?

## Decisiones de producto
5. **Metas de resultado (MR):** ¿la página debe incluirlas ya, o la primera versión se queda en metas de producto?
6. **Prompt:** se añadió un bloque opcional "Hechos verificados" (avisa al LLM que las cifras ya están calculadas
   y que no las recalcule). ¿Lo dejamos activado por defecto?
7. **Periodo de revisión:** hoy solo cambia el texto del prompt. ¿Se muestra además una referencia neutral de
   tiempo transcurrido (25 %, 50 %…) junto al avance? No sería umbral: solo contexto.
8. **Histórico:** ¿interesa guardar cada corte para ver la evolución de una dependencia?

## Seguridad
9. **Repo público:** Streamlit Community Cloud indica que **sí admite repos privados** (pide un permiso adicional de
   GitHub, `repo`), aunque no pude abrir su documentación oficial para confirmarlo ni sus límites vigentes.
   ¿Pueden probar a pasar el repo a privado en `share.streamlit.io` (Settings → Repository)?
10. **Libro de Drive:** ¿está compartido como "cualquiera con el enlace"? Su ID sigue en `pages/2_POAI_2027.py`.
    La página de seguimiento ya lee el enlace de un secreto (`URL_DRIVE_PLAN_INDICATIVO`), no del código.

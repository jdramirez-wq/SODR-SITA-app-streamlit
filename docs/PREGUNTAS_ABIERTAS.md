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
| Justificación de un avance 0 | Según la líder del equipo debe estar en **Dificultades**; a veces se es flexible, pero esa decisión es posterior | Criterio **estricto por defecto**; casilla "criterio flexible" (también acepta Análisis del logro) |
| Metas compartidas | La suposición de base es que **quien reporta está enterado** del avance de las dependencias con las que comparte la meta | El aviso se mantiene: quien reporta debe indicarlo en la narrativa (no se excusa) |
| Meta distinta entre el export y Drive | **Prevalece Drive**: el operador de EVAPLAN a veces no lo tiene actualizado | Ya funciona así; el aviso lo dice |
| Varios registros por actividad | Son registros presupuestales; **no hay forma sencilla de agrupar por actividad** (el código no coincide siempre y a veces difiere a propósito por una palabra o un punto) | La unidad es el **registro**; se quitó el conteo de "actividades" |
| ¿Z023 consolidado en una carpeta que la app lea? | **No**: contiene información que no debe ser pública | Ver "Z023" abajo |

## Para confirmar (rápidas)
1. **MR 2025:** en la hoja MR del Drive el encabezado 2025 no dice `VAL ALC`. ¿Falta cargar el logro 2025 de las
   metas de resultado, o solo falta renombrar el encabezado? (No afecta a la página mientras solo se usen MP.)
2. **Reglas del PG** para Incremento Flujo, Capacidad y Reducción Anual: 14 metas del PI original no cumplen la regla
   (por ejemplo, Flujo con 2027 = 0 y PG > 0). ¿Son errores de digitación o la regla es otra?

## Surgidas al probar con 10 dependencias reales
3. **Actividades con avance 0 y observación vacía (`.`):** la circular prohíbe los vacíos. ¿Activamos una alerta por
   registro? Hoy solo se alerta si además hay obligaciones.
4. ~~**Z023 consolidado:** muestra~~ **Resuelto (6-oct):** se leyó la estructura (Hoja de Google convertida, 6.409 filas) y
   está en el diccionario. **Decisión tomada con los datos:** las entidades descentralizadas (19, códigos `00xx`) no tienen
   código PS pero **sí aportan a metas** de dependencias centrales, así que **no se excluyen** del cruce: se muestran como
   "Descentralizada · sin código PS". Si prefieren excluirlas, es un cambio de una línea.
   *Para confirmar:* en el `.xlsx` original, ¿las columnas calculadas (Centro Gestor de la MP, código de producto DNP,
   llaves DNP) traen valores o también quedan vacías?

## Decisiones de producto
5. **Prompt:** el bloque opcional "Hechos verificados" queda **activado por defecto** (se puede desmarcar en la barra
   lateral). Se revisa cuando el equipo compare respuestas del LLM con y sin el bloque.
6. **Periodo de revisión:** hoy solo cambia el texto del prompt. ¿Se muestra además una referencia neutral de
   tiempo transcurrido (25 %, 50 %…) junto al avance? No sería umbral: solo contexto.
7. **Histórico:** ¿interesa guardar cada corte para ver la evolución de una dependencia?

## Seguridad
8. **Repo público:** Streamlit Community Cloud indica que **sí admite repos privados** (pide un permiso adicional de
   GitHub, `repo`), aunque no pude abrir su documentación oficial para confirmarlo ni sus límites vigentes.
   ¿Pueden probar a pasar el repo a privado en `share.streamlit.io` (Settings → Repository)?
9. ~~**Libro de Drive del Plan Indicativo:** ¿puede estar compartido por enlace?~~ **Resuelto (2-oct):** de momento no hay
   problema en que esté abierto por enlace. Si cambia, la alternativa es una cuenta de servicio de Google.

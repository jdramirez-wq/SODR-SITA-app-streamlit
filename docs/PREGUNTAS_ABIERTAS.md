# Preguntas abiertas

Responder estas preguntas desbloquea las reglas marcadas ❓ y el diseño de la herramienta. Cuando se
resuelva una, se mueve a `docs/REGLAS_DE_NEGOCIO.md` (o a la decisión que corresponda) y se borra de aquí.

## Alta prioridad
1. **¿Qué es exactamente `Resultado` en el export de EVAPLAN?** ¿Acumulado de la vigencia al corte, valor del
   periodo, o acumulado del cuatrienio? ¿Y `Valor Proyectado` (¿proyección a cierre de vigencia?)?
2. **Bloque vigente de Drive:** ¿`VAL ALC 2024/2025` es el logro alcanzado y `2026/2027` la meta reprogramada?
   ¿`PG 2024-2027` (sin punto) es el PG reprogramado y `PG 2024-2027.` (con punto) el original?
3. **Metas ausentes en el export de EVAPLAN:** faltaron 2 de 12 metas de la entidad. ¿Por qué? ¿Cuándo ha visto
   usted diferencias reales entre el export y el Drive (valores, metas, fechas)?
4. **Reglas del PG:** ¿en Flujo el PG es siempre el valor de 2027? ¿Y en Capacidad y Reducción Anual? Hay 14
   metas en el PI original que no cumplen la regla: ¿son errores de digitación?
5. **Alcance de uso:** ¿cada secretaría sube sus propios archivos, o la oficina consolida varias entidades a la
   vez? (cambia el diseño: una entidad vs. todas).
6. **Cumplimiento:** ¿cómo calculan hoy el % de cumplimiento de una meta en un corte (trimestre/semestre/
   cierre)? ¿Qué umbrales usan para decir "en riesgo" o "incumplida"?

## Media prioridad
7. **Centralizadas:** ¿qué cubre exactamente (¿solo ciertas fuentes de financiación?)? ¿Por qué el presupuesto del
   plan de acción puede superar los recursos del PI? ¿Las actividades de una misma meta repiten la meta o la
   fraccionan (hay metas con 2 actividades que programan lo mismo)?
8. **Periodicidad y archivo histórico:** ¿cada cuánto se descargan los archivos? ¿Interesa guardar cada corte para
   ver la evolución, o solo el último?
9. **El bot auditor:** ¿puede compartir un ejemplo de prompt y de respuesta? Las reglas que aplica el bot que
   sean determinísticas conviene convertirlas en código (más rápido, gratis y reproducible).
10. **Productos finales:** ¿qué reportes (Excel/PDF) entregan hoy y a quién? Los reproducimos primero.

## Seguridad
11. **¿El libro de Drive está compartido como "cualquiera con el enlace"?** El ID está en el código del
    repositorio público. Si es así, conviene restringirlo o publicar solo una copia sin datos sensibles.
12. **¿Quién debe poder abrir la app?** (Streamlit Cloud permite limitar por correo institucional).

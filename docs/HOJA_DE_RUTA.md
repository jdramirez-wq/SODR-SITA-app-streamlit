# Hoja de ruta

Foco actual: **una sola página, Seguimiento EVAPLAN** (`paginas/1_Auditoria_EVAPLAN.py`). POAI 2027 queda congelada.

## Fase 0 — Orden del proyecto ✅
Estructura, `CLAUDE.md`, README, CI, plantillas, reglas de privacidad.

## Fase 1 — Contrato de datos ✅
- [x] Análisis de las fuentes → [ANALISIS_FUENTES_EVAPLAN.md](ANALISIS_FUENTES_EVAPLAN.md)
- [x] Diccionario de datos tipado y generado desde código → [DICCIONARIO_DE_DATOS.md](DICCIONARIO_DE_DATOS.md)
- [x] Lectores tolerantes a los cambios habituales (`VAL ALC`), validaciones y pruebas con ejemplos ficticios

## Fase 2 — Página de Seguimiento EVAPLAN, primera versión ✅ (pendiente de revisión del equipo)
- [x] Cruce Plan Indicativo (Drive) + Plan Indicativo MP (EVAPLAN) + Centralizadas
- [x] Metas sin reporte, hechos objetivos por meta, avance de actividades **por proyecto**
- [x] Excel integrado y PDF por meta (mismos contenidos que antes + hechos), prompt con vigencia automática
- [x] Vigencia detectada por los encabezados `VAL ALC`; enlace de Drive en secretos
- [ ] **Configurar el secreto `URL_DRIVE_PLAN_INDICATIVO` en Streamlit Cloud antes de publicar** (guía: [COMO_PROBAR_LA_RAMA.md](COMO_PROBAR_LA_RAMA.md))
- [ ] Revisión con los compañeros de la SODR con una dependencia real

## Fase 3 — Pulir la primera versión
- [x] Probada en navegador real con 10 dependencias reales; cifras verificadas de forma independiente (ver análisis 2b)
- [x] **Z023 consolidado** subido por sesión (cuarto cuadro opcional; nunca guardado): proyectos que aportan a cada meta
      (propios y de otras entidades), validaciones y hoja `Aportes_Z023` en el Excel
- [x] Entidades descentralizadas (ejemplo INDERVALLE): equivalencia de código con el Z023, actividades por código PPM
- [x] Recordatorios de cierre de vigencia (certificados financieros de descentralizadas y de avance por gestión) en la
      página y en el prompt
- [ ] Detallar con el equipo los certificados de cierre (ver pregunta 4c)
- [ ] Probar el cuarto cuadro con el Z023 real (`.xlsx` original con fórmulas calculadas) y revisar tiempos de lectura
- [ ] Leer el código de producto DNP (`BPIN + Producto MGA`) del Z023 cuando se confirme que llega con valores
- [x] Avance por registro (no hay forma sencilla de agrupar por actividad)
- [x] Criterio estricto por defecto para el avance 0 (Dificultades), con casilla flexible
- [ ] Resolver lo que queda en [PREGUNTAS_ABIERTAS.md](PREGUNTAS_ABIERTAS.md) (reglas del PG, periodo, histórico)
- [ ] **Revisar el script del compañero** y rescatar lo útil
- [ ] ~~Metas de resultado (MR) en la página~~ — fuera de alcance por ahora (solo MP)
- [ ] Fijar versiones en `requirements.txt`; quitar `use_container_width` (obsoleto en Streamlit reciente)

## Fase 4 — Seguridad (repo público)
- [ ] Probar el paso del repo a privado en Streamlit Community Cloud
- [ ] Mover `URL_DRIVE_EXCEL` de `paginas/2_POAI_2027.py` a secretos y revisar permisos del libro en Drive
- [ ] Decidir quién puede abrir la app (limitar por correo institucional)
- [x] Plan Indicativo abierto por enlace: aceptado por el equipo de momento (si cambia: cuenta de servicio de Google)

## Fase 5 — Evolución
- [ ] Guardar cortes históricos para ver la evolución de una dependencia (si se confirma que interesa)
- [ ] Migrar POAI 2027 a `src/` con su propio contrato de datos (Cadena de Valor, MGA, Z023)

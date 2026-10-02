# Hoja de ruta

## Fase 0 — Orden del proyecto ✅
Estructura, `CLAUDE.md`, README, CI, plantillas, reglas de privacidad.

## Fase 1 — Entender los datos ✅ (primera pasada)
- [x] Analizar los 3 exports de EVAPLAN y el libro del Plan Indicativo → [ANALISIS_FUENTES_EVAPLAN.md](ANALISIS_FUENTES_EVAPLAN.md)
- [x] Diccionario de datos tipado, generado desde código → [DICCIONARIO_DE_DATOS.md](DICCIONARIO_DE_DATOS.md)
- [x] Lectores tipados, validaciones y pruebas con ejemplos ficticios
- [ ] **Resolver [PREGUNTAS_ABIERTAS.md](PREGUNTAS_ABIERTAS.md)** (bloquea Fase 3)
- [ ] Analizar el resto: otras hojas del libro, columnas 103-275 de MP, otras entidades, Cadena de Valor/MGA/Z023

## Fase 2 — Seguridad básica (repo público)
- [ ] Mover `URL_DRIVE_EXCEL` (`pages/2_POAI_2027.py`) a `st.secrets`.
- [ ] Revisar permisos del libro de Drive (el ID ya está en el historial de Git).
- [ ] Decidir quién puede abrir la app (Streamlit Cloud permite limitar por correo).

## Fase 3 — Motor de seguimiento
- [ ] Cálculo de cumplimiento por meta y periodo según el comportamiento del indicador (reglas pendientes).
- [ ] Semáforos / umbrales de alerta.
- [ ] Nueva página "Seguimiento al Plan" que use `src/evaplan` y muestre el panel de hallazgos.
- [ ] Reportes (Excel/PDF) reproduciendo los actuales.

## Fase 4 — Migrar las páginas existentes
- [ ] Auditoría EVAPLAN → `src/evaplan` (comparar resultados antes/después con archivos de ejemplo).
- [ ] POAI 2027 → `src/` (incluye contratos de datos para Cadena de Valor, MGA y Z023).
- [ ] Fijar versiones en `requirements.txt`.

## Fase 5 — Más fuentes en Drive y evolución en el tiempo
- [ ] Sustituir descargas manuales por lecturas desde Drive donde sea posible.
- [ ] Guardar cortes históricos para ver evolución (si se confirma que interesa).

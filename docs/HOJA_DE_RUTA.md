# Hoja de ruta

## Fase 0 — Orden del proyecto (hecho)
Estructura, `CLAUDE.md`, README, CI, plantillas, reglas de privacidad.

## Fase 1 — Entender los datos
- [ ] Documentar cada Excel/fuente en `docs/FUENTES_DE_DATOS.md` (hojas, columnas, llaves).
- [ ] Crear ejemplos anonimizados en `data/ejemplos/`.
- [ ] Mapear el cruce: qué fuentes, con qué llave, qué se espera detectar.

## Fase 2 — Seguridad básica (repo público)
- [ ] Mover `URL_DRIVE_EXCEL` a `st.secrets`.
- [ ] Revisar permisos de la hoja de Drive ("cualquiera con el enlace" = accesible a cualquiera
      que tenga el ID; el ID ya está en el historial de Git, así que el control real son los permisos).
- [ ] Decidir quién puede abrir la app (Streamlit Cloud permite restringir por correo).

## Fase 3 — Refactorización
- [ ] Extraer lógica a `src/` página por página, con pruebas.
- [ ] Fijar versiones en `requirements.txt`.

## Fase 4 — Seguimiento al plan
- [ ] Tablero de avance del Plan de Desarrollo (indicadores por meta/proyecto/vigencia).
- [ ] Fuentes en Drive sustituyendo descargas manuales donde sea posible.

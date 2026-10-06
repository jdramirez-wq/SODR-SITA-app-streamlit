# Paso a `main`: publicar la nueva versión para los compañeros

`main` es la versión que ven los usuarios. Hoy la rama `claude/determined-thompson-6vlmqe` tiene todo el trabajo nuevo
(Seguimiento EVAPLAN rediseñado, Z023, descentralizadas, reportes para IA, periodo flexible) y **no tiene conflictos**
con `main`. Pasarla a `main` se hace con un **Pull Request** (PR): una solicitud de fusión que GitHub revisa
automáticamente antes de aplicarla.

Hay dos apps en Streamlit Cloud:

| App | Rama | Archivo principal | Para qué |
|---|---|---|---|
| **Oficial** (la que usan los compañeros) | `main` | por confirmar (ver paso 5) | Uso diario |
| **De prueba** (`seguimiento-evaplan-prueba`) | rama de trabajo | `pages/1_Auditoria_EVAPLAN.py` | Probar antes de publicar |

---

## Paso 1. Última revisión en la app de prueba (10 minutos)
Con los archivos reales de **una** dependencia:
- [ ] Carga los dos archivos de EVAPLAN y procesa. Revisa que las cifras de 2 o 3 metas coincidan con EVAPLAN.
- [ ] Descarga el PDF y pégalo con el prompt en Gemini o ChatGPT (versión gratuita). La respuesta debe usar los mismos
      porcentajes del PDF.
- [ ] Prueba un periodo de cierre: deben aparecer los recordatorios de certificados.
- [ ] (Opcional) Carga el Z023 y revisa una meta compartida.

Si algo no cuadra, avísame antes de seguir.

## Paso 2. Abrir el Pull Request
**Opción fácil:** pídeme "abre el PR a main". Lo abro con la descripción completa (qué cambia y cómo se probó).

**Opción manual:** en GitHub, entra al repositorio → pestaña **Pull requests** → **New pull request** →
`base: main` ← `compare: claude/determined-thompson-6vlmqe` → **Create pull request**. Llena la plantilla.

## Paso 3. Esperar la revisión automática
En el PR aparece la sección **Checks**: GitHub instala la app y corre las 155 pruebas, el lint y la compilación
(tarda 2-3 minutos).
- ✅ Verde: sigue al paso 4.
- ❌ Rojo: no fusiones. Avísame y lo corrijo en la misma rama (el PR se actualiza solo).

## Paso 4. Fusionar
En el PR, botón **Merge pull request** → **Confirm merge**. Usa la opción por defecto ("Create a merge commit").
No hace falta borrar la rama después (GitHub lo ofrece; es opcional).

## Paso 5. Actualizar la app oficial
1. En [share.streamlit.io](https://share.streamlit.io), abre la app oficial → menú **⋮ → Logs**. En la primera línea dice
   `main module: '...'`: ese es su **archivo principal**.
   - Si dice `app.py`: perfecto.
   - Si dice `pages/1_Auditoria_EVAPLAN.py`: también funciona (dejé un archivo de compatibilidad), pero conviene
     cambiarlo a `app.py` en el paso 6.
2. **Secreto del Plan Indicativo de Drive.** Menú **⋮ → Settings → Secrets** y pega (con el enlace real, el mismo que
   tiene la app de prueba):
   ```
   URL_DRIVE_PLAN_INDICATIVO = "https://docs.google.com/spreadsheets/d/<ID>/export?format=xlsx"
   ```
   Sin este secreto la app funciona, pero no detecta las **metas sin reporte**.
3. Menú **⋮ → Reboot app**. Verifica:
   - [ ] La barra lateral muestra **Versión del código** con el número del último cambio de `main`.
   - [ ] Arriba aparece la barra **Inicio · Trámites** y se puede ir a POAI 2027 y volver.
   - [ ] En Seguimiento EVAPLAN, debajo de "Archivos de la dependencia", dice **"Plan Indicativo de Drive conectado por
         enlace"**.

## Paso 6 (recomendado). Dirección más seria y archivo principal correcto
Si quieres cambiar `mi-primera-app-streamlit.streamlit.app` por algo como `sodr-seguimiento.streamlit.app`:
- Primero busca en **⋮ → Settings → General** si deja editar la dirección (subdominio). Si se puede, cámbiala ahí
  y listo.
- Si no se puede (o si el archivo principal no es `app.py`), crea la app de nuevo:
  1. Copia los **Secrets** de la app oficial (paso 5.2) a un lugar seguro.
  2. **⋮ → Delete** la app oficial.
  3. **Create app** → **Deploy a public app from GitHub** → repositorio `mi-primera-app-streamlit`, rama `main`,
     **Main file path: `app.py`**, **App URL:** la dirección nueva.
  4. **Advanced settings:** Python 3.12 y pega los Secrets.
  5. **Deploy** y repite las verificaciones del paso 5.3.
- Comparte la dirección nueva con los compañeros. La anterior deja de funcionar si borraste la app.

## Paso 7 (opcional, después). Nombre del repositorio
El nombre `mi-primera-app-streamlit` solo lo ven quienes entran a GitHub. Si quieres cambiarlo (p. ej.
`sodr-plataforma`): GitHub → repositorio → **Settings → General → Repository name** → **Rename**.
Consecuencias:
- GitHub redirige los enlaces viejos, pero **las apps de Streamlit Cloud deben volver a crearse** apuntando al nombre
  nuevo (como en el paso 6).
- Avísame: mi acceso en estas sesiones está autorizado para el nombre actual y habrá que agregar el nuevo.
- Por eso conviene hacerlo **junto con el paso 6**, una sola vez.

## Paso 8. Limpieza (lo hago yo cuando me avises)
- Cuando la app oficial arranque desde `app.py`: borrar los archivos de compatibilidad de `pages/`
  (si la app de prueba sigue usándolos, la apunto también a `app.py` o la dejamos como está).
- La **app de prueba** se queda para futuras ramas: cada mejora se prueba ahí antes de un nuevo PR.
- Actualizar `CLAUDE.md` y `docs/COMO_PROBAR_LA_RAMA.md` con las direcciones definitivas.

---

### Si algo sale mal después de fusionar
`main` guarda el historial completo. En el PR fusionado, GitHub ofrece el botón **Revert**, que crea un PR para
volver a la versión anterior. También puedes pedírmelo.

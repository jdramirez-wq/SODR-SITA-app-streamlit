# Cómo probar una rama en Streamlit sin tocar lo que usan tus compañeros

> **App oficial:** <https://sodr-sita-app.streamlit.app/> (rama `main`). **Repositorio:** `jdramirez-wq/SODR-SITA-app-streamlit`.

Una **rama** de GitHub es una copia de trabajo del proyecto. La app que usan tus compañeros se publica desde `main`;
mientras los cambios estén en otra rama, **nada de lo publicado cambia**. Para probar, publicas una **segunda app**
(de prueba) que lee esa rama.

## Opción A (recomendada): app de prueba en Streamlit Community Cloud

1. Entra a <https://share.streamlit.io> con la cuenta de GitHub dueña del repositorio.
2. **Create app → Deploy a public app from GitHub** y completa:
   - **Repository:** `jdramirez-wq/SODR-SITA-app-streamlit`
   - **Branch:** la rama a probar (p. ej. `claude/determined-thompson-6vlmqe`)
   - **Main file path:** `app.py`
   - **App URL:** un nombre distinto al de la app oficial (p. ej. `seguimiento-evaplan-prueba`)
3. Antes de pulsar *Deploy*, abre **Advanced settings** y:
   - **Python version:** elige **3.12**. (La suite de pruebas pasa en 3.11, 3.12 y 3.13; 3.14 no se ha probado.)
   - **Secrets:** borra el texto de ejemplo (`DB_USERNAME`, `DB_TOKEN`… es solo una muestra en gris) y pega:
   ```toml
   URL_DRIVE_PLAN_INDICATIVO = "https://docs.google.com/spreadsheets/d/<ID_DEL_LIBRO>/export?format=xlsx"
   ```
   `<ID_DEL_LIBRO>` es el texto entre `/d/` y `/edit` en la dirección del libro del Plan Indicativo en Drive.
4. Pulsa **Deploy**. La primera vez tarda unos minutos mientras instala las librerías de `requirements.txt`.
5. Cada vez que se suba un cambio a esa rama, la app de prueba se actualiza sola.

> El enlace de despliegue directo (puede variar según la versión de Streamlit):
> `https://share.streamlit.io/deploy?repository=jdramirez-wq/SODR-SITA-app-streamlit&branch=<RAMA>&mainModule=app.py`

### Que el secreto funcione: el libro debe poder leerse sin iniciar sesión
Streamlit lee el libro **sin tu sesión de Google**. Compruébalo así: abre el enlace de exportación en una ventana de
incógnito.
- **Se descarga un `.xlsx`** → funciona.
- **Pide iniciar sesión o da error** → en Drive: *Compartir → Acceso general → "Cualquier persona con el enlace" →
  Lector*. (Si no quieres abrir el libro, deja el secreto vacío y súbelo a mano en "Agregar fuentes opcionales".)

### Qué ver en la app de prueba
En Seguimiento EVAPLAN, debajo de "Archivos de la dependencia", debe decir **"Plan Indicativo de Drive conectado por
enlace."** Si dice "Sin enlace al Plan Indicativo de Drive", el secreto no se guardó (Settings → Secrets en la app) o
tiene un error de comillas.

## Opción B: GitHub Codespaces (sin instalar nada)
1. En GitHub: botón verde **Code → Codespaces → Create codespace on `<rama>`**.
2. El proyecto ya trae `.devcontainer`: instala las librerías y abre la app en una vista previa (puerto 8501).
3. Para el secreto: crea `.streamlit/secrets.toml` con la misma línea de arriba. Ese archivo **no se sube** a GitHub
   (está en `.gitignore`).

## Opción C: en tu computador
```bash
git clone https://github.com/jdramirez-wq/SODR-SITA-app-streamlit && cd SODR-SITA-app-streamlit
git checkout <rama>
pip install -r requirements.txt
streamlit run app.py
```

## Probar primero sin datos reales
Archivos **ficticios** con el mismo formato, en `data/ejemplos/`: `ejemplo_PI_MP_evaplan.xlsx`,
`ejemplo_Centralizadas.xlsx` y `ejemplo_PI_Drive.xlsx` (este último va en "Agregar fuentes opcionales"). Con ellos la página debe
mostrar 5 metas, 1 sin reporte y 3 con alertas.

## Lista de comprobación con una dependencia real
- [ ] Dice "Plan Indicativo de Drive conectado por enlace" y la vigencia detectada es la correcta.
- [ ] Metas en el Plan Indicativo = metas de la dependencia en Drive; las "sin reporte" son las que no reportó.
- [ ] El `Resultado` y la meta de la vigencia de 2–3 metas coinciden con EVAPLAN.
- [ ] Avance de actividades **por proyecto** coincide con lo que se ve en Centralizadas.
- [ ] El Excel y el PDF descargados abren bien y el PDF trae la carátula de metas sin reporte.
- [ ] El prompt trae la vigencia correcta (no "2026" fijo) y, pegado en el LLM, responde bien con y sin el bloque
      de "hechos verificados".
- [ ] Subir los archivos cambiados de lugar da un mensaje claro, no un error técnico.

## Cuando termines
- **Aprobada:** se abre un Pull Request de la rama a `main` y, al aceptarlo, la app oficial se actualiza sola.
  *(Antes de eso, configura el mismo secreto en la app oficial.)*
- **Descartar la prueba:** en <https://share.streamlit.io> → los tres puntos de la app de prueba → **Delete app**.

## Problemas frecuentes
| Síntoma | Causa probable |
|---|---|
| "Sin enlace al Plan Indicativo de Drive" | Falta el secreto, o la app no se reinició tras guardarlo |
| "No se pudo leer Drive (HTTPError 4xx)" | El libro no es público o el ID está mal copiado |
| "Un archivo no tiene la estructura esperada" | Se subió un archivo en el cuadro equivocado, o EVAPLAN cambió columnas |
| `ModuleNotFoundError: No module named 'src'` | La página se ejecutó como archivo principal. Ya está corregido en el código; además, **Main file path debe ser `app.py`** |
| Aviso de `use_container_width` en los registros | Inofensivo: función obsoleta que aún funciona; está en la hoja de ruta |

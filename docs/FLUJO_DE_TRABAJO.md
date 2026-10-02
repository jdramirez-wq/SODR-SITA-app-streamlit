# Cómo trabajamos

## Ramas
- `main`: lo que usan los compañeros (Streamlit Cloud despliega desde aquí).
- Una rama por cambio (`claude/...` o `mejora/<tema>`). Nada va directo a `main`.

## Ciclo de un cambio
1. Se describe la necesidad (idealmente como *Issue*, plantilla "Mejora o tarea").
2. Se trabaja en una rama y se hacen commits pequeños en español.
3. Se abre un **Pull Request**; el CI (GitHub Actions) revisa que el código compile y pase el lint.
4. Se prueba la app con un archivo de ejemplo y se aprueba el PR → pasa a `main` → se publica.

## Trabajar con Claude
- Claude lee `CLAUDE.md` al iniciar: mantenerlo al día es la forma de "alimentar su contexto".
- Archivos para analizar: adjuntarlos en el chat o dejarlos en Drive (no subir datos reales al repo).
- Para que Claude entienda un formato: un **ejemplo anonimizado** en `data/ejemplos/` + su
  descripción en `docs/FUENTES_DE_DATOS.md`.

## Qué nunca se sube a GitHub
Datos reales, credenciales, enlaces privados, archivos con información personal.

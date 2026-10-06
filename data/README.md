# Carpeta `data/`

El repositorio es **público**. Aquí NO se suben datos reales (planes, proyectos, presupuestos, personas).

- `data/` está ignorada por Git salvo este archivo y `data/ejemplos/`.
- `data/ejemplos/` es para archivos **ficticios o anonimizados** con la misma estructura (columnas y hojas) que los reales. Sirven para pruebas y para que Claude entienda el formato sin ver información sensible.
- Los datos reales viven en Drive y la app los recibe con `st.file_uploader` o los lee de Drive.

Para cada archivo de entrada documenta en `docs/FUENTES_DE_DATOS.md`: de qué plataforma se descarga, hojas, columnas clave y llave de cruce.

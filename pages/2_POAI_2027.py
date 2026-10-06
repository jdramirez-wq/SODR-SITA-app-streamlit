"""Compatibilidad: la app de prueba de Streamlit Cloud se creó con este archivo como principal.

Si Streamlit lo ejecuta como archivo principal, carga la plataforma completa (app.py: portada y navegación).
La página real está en paginas/1_Auditoria_EVAPLAN.py. Cuando se despliegue con app.py como principal, este
archivo se puede borrar.
"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent.parent / "app.py"), run_name="__main__")

"""Rutas absolutas de las páginas. Así la navegación funciona sin importar qué archivo use Streamlit Cloud como
principal (app.py, o el archivo de compatibilidad pages/1_Auditoria_EVAPLAN.py de la app de prueba)."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SEGUIMIENTO = str(RAIZ / "paginas" / "1_Auditoria_EVAPLAN.py")
POAI = str(RAIZ / "paginas" / "2_POAI_2027.py")
LOGO = str(RAIZ / "interfaz" / "logo.svg")
ICONO = str(RAIZ / "interfaz" / "icono.svg")

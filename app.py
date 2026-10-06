"""Punto de entrada: navegación de la plataforma de la SODR (nombres e iconos legibles en la barra lateral)."""
import sys
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from interfaz import estilos, portada  # noqa: E402

st.set_page_config(page_title="Plataforma SODR", page_icon=str(RAIZ / "interfaz" / "icono.svg"), layout="wide",
                   initial_sidebar_state="expanded")
st.logo(str(RAIZ / "interfaz" / "logo.svg"), size="large", icon_image=str(RAIZ / "interfaz" / "icono.svg"))
estilos.aplicar_estilos()

paginas = {
    "": [st.Page(portada.mostrar, title="Inicio", icon=":material/home:", default=True)],
    "Trámites": [
        st.Page("pages/1_Auditoria_EVAPLAN.py", title="Seguimiento EVAPLAN", icon=":material/fact_check:",
                url_path="seguimiento"),
        st.Page("pages/2_POAI_2027.py", title="POAI 2027", icon=":material/edit_note:", url_path="poai"),
    ],
}
st.navigation(paginas).run()

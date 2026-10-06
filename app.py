"""Punto de entrada: navegación de la plataforma de la SODR (nombres e iconos legibles, barra superior)."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from interfaz import estilos, memoria, portada, rutas  # noqa: E402

st.set_page_config(page_title="Plataforma SODR", page_icon=rutas.ICONO, layout="wide", initial_sidebar_state="expanded")
st.logo(rutas.LOGO, size="large", icon_image=rutas.ICONO)
estilos.aplicar_estilos()
memoria.conservar_en_direccion()   # si hay resultados guardados, la dirección conserva su clave en todas las páginas

paginas = {
    "": [st.Page(portada.mostrar, title="Inicio", icon=":material/home:", default=True)],
    "Trámites": [
        st.Page(rutas.SEGUIMIENTO, title="Seguimiento EVAPLAN", icon=":material/fact_check:", url_path="Auditoria_EVAPLAN"),
        st.Page(rutas.POAI, title="POAI 2027", icon=":material/edit_note:", url_path="POAI_2027"),
    ],
}
st.navigation(paginas, position="top").run()   # barra superior: siempre se puede volver al inicio

"""Portada de la plataforma de la SODR: elegir el trámite."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from interfaz import estilos

st.set_page_config(page_title="Plataforma de Gestión - SODR", page_icon="🏢", layout="wide",
                   initial_sidebar_state="expanded")
estilos.aplicar_estilos()

estilos.encabezado(
    "Plataforma de trámites y auditoría",
    "Subdirección de Ordenamiento y Desarrollo Regional (SODR). Herramientas para el seguimiento del Plan de "
    "Desarrollo Departamental.")

st.subheader("¿Qué quieres hacer?")
col1, col2 = st.columns(2)
with col1, st.container(border=True):
    st.markdown("#### 📊 Seguimiento EVAPLAN")
    st.write("Cruza lo reportado en EVAPLAN con el Plan Indicativo y el Plan de Acción: metas sin reporte, avance, "
             "ejecución financiera, reportes en Excel y PDF y el prompt para el asistente de auditoría.")
    st.page_link("pages/1_Auditoria_EVAPLAN.py", label="Abrir Seguimiento EVAPLAN", icon="📊", use_container_width=True)
with col2, st.container(border=True):
    st.markdown("#### 📝 POAI 2027")
    st.write("Formulación, revisión y cargue del Plan Operativo Anual de Inversiones para la vigencia 2027.")
    st.caption("En desarrollo")
    st.page_link("pages/2_POAI_2027.py", label="Explorar el módulo POAI", icon="📝", use_container_width=True)

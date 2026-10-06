"""Portada de la plataforma: elegir el trámite."""
from __future__ import annotations

import streamlit as st

from . import estilos


def mostrar() -> None:
    estilos.aplicar_estilos()
    estilos.encabezado(
        "Plataforma de trámites y auditoría",
        "Herramientas de la Subdirección de Ordenamiento y Desarrollo Regional para el seguimiento del Plan de "
        "Desarrollo Departamental.")
    st.markdown("### ¿Qué quieres hacer?")
    col1, col2 = st.columns(2, gap="medium")
    with col1, st.container(border=True):
        st.markdown("#### Seguimiento EVAPLAN")
        st.write("Cruza lo reportado en EVAPLAN con el Plan Indicativo y el Plan de Acción: metas sin reporte, "
                 "avance, ejecución financiera, reportes en Excel y PDF y el prompt para el asistente de auditoría.")
        estilos.chips(["Metas de producto", "Alertas objetivas", "PDF para IA"])
        st.page_link("pages/1_Auditoria_EVAPLAN.py", label="Abrir Seguimiento EVAPLAN",
                     icon=":material/arrow_forward:", width="stretch")
    with col2, st.container(border=True):
        st.markdown("#### POAI 2027")
        st.write("Formulación, revisión y cargue del Plan Operativo Anual de Inversiones para la vigencia 2027.")
        estilos.chips(["En desarrollo"])
        st.page_link("pages/2_POAI_2027.py", label="Explorar el módulo POAI", icon=":material/arrow_forward:",
                     width="stretch")

"""Prueba de humo: la página de seguimiento carga sin archivos y no lanza excepciones."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parent.parent


def test_pagina_de_seguimiento_carga_sin_archivos():
    at = AppTest.from_file(str(RAIZ / "pages" / "1_Auditoria_EVAPLAN.py"), default_timeout=30).run()
    assert not at.exception
    assert any("Sube" in i.value for i in at.info)            # invita a subir los archivos
    assert at.sidebar.selectbox[0].options[0].startswith("Revisión acumulada")


def test_portada_carga():
    at = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()
    assert not at.exception

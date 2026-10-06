"""Prueba de humo: la página de seguimiento carga sin archivos y no lanza excepciones."""
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parent.parent


def test_pagina_de_seguimiento_carga_sin_archivos():
    at = AppTest.from_file(str(RAIZ / "paginas" / "1_Auditoria_EVAPLAN.py"), default_timeout=30).run()
    assert not at.exception
    boton = next(b for b in at.button if b.label == "Procesar")
    assert boton.disabled                                      # sin los dos archivos no se puede procesar
    assert at.sidebar.selectbox[0].options[0].startswith("Revisión acumulada")


def test_portada_carga():
    at = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()
    assert not at.exception


def test_la_pagina_funciona_aunque_la_raiz_del_repo_no_este_en_sys_path(monkeypatch):
    """Caso real: con la página como archivo principal, Streamlit Cloud falló con "No module named 'src'"."""
    monkeypatch.setattr(sys, "path", [p for p in sys.path if Path(p or ".").resolve() != RAIZ])
    for nombre in [m for m in sys.modules if m in ("src", "interfaz") or m.startswith(("src.", "interfaz."))]:
        monkeypatch.delitem(sys.modules, nombre)
    at = AppTest.from_file(str(RAIZ / "paginas" / "1_Auditoria_EVAPLAN.py"), default_timeout=30).run()
    assert not at.exception


def test_la_app_de_prueba_arranca_desde_el_archivo_de_compatibilidad():
    """La app de prueba de Streamlit Cloud tiene como principal pages/1_Auditoria_EVAPLAN.py (no app.py)."""
    for nombre in ("1_Auditoria_EVAPLAN.py", "2_POAI_2027.py"):
        at = AppTest.from_file(str(RAIZ / "pages" / nombre), default_timeout=30).run()
        assert not at.exception

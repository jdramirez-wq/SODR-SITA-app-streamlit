"""Recargar la página (F5) no debe borrar los resultados ni la configuración de la revisión.

En AppTest, "recargar" es abrir una sesión nueva con la misma dirección (el parámetro ?sesion=...).
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parent.parent
PAGINA = str(RAIZ / "paginas" / "1_Auditoria_EVAPLAN.py")
EJ = RAIZ / "data" / "ejemplos"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _abrir(clave: str | None = None) -> AppTest:
    at = AppTest.from_file(PAGINA, default_timeout=60)
    if clave:
        at.query_params["sesion"] = clave
    return at.run()


def _procesar(at: AppTest) -> AppTest:
    at.get("file_uploader")[0].upload("ejemplo_PI_MP_evaplan.xlsx", (EJ / "ejemplo_PI_MP_evaplan.xlsx").read_bytes(), XLSX)
    at.get("file_uploader")[1].upload("ejemplo_Centralizadas.xlsx", (EJ / "ejemplo_Centralizadas.xlsx").read_bytes(), XLSX)
    at.run()
    next(b for b in at.button if b.label == "Procesar").click()
    return at.run()


def _boton(at: AppTest, etiqueta: str):
    return next((b for b in at.button if b.label == etiqueta), None)


def test_f5_conserva_resultados_y_configuracion():
    at = _abrir()
    assert "sesion" not in at.query_params                      # sin resultados no se guarda nada
    at.sidebar.radio[0].set_value("proyectado")
    at.sidebar.select_slider[0].set_value(10)
    at = _procesar(at)
    assert not at.exception
    assert "resultado" in at.session_state
    clave = at.query_params["sesion"]
    clave = clave[0] if isinstance(clave, list) else clave

    recargada = _abrir(clave)                                   # F5: sesión nueva, misma dirección
    assert not recargada.exception
    assert "resultado" in recargada.session_state
    assert recargada.session_state["archivos"] == ["ejemplo_PI_MP_evaplan.xlsx", "ejemplo_Centralizadas.xlsx"]
    assert recargada.sidebar.radio[0].value == "proyectado"
    assert recargada.sidebar.select_slider[0].value == 10
    assert any("recuperaron" in t.value for t in recargada.toast)
    assert _boton(recargada, "Borrar resultados") is not None


def test_borrar_resultados_los_quita_tambien_de_la_memoria():
    at = _procesar(_abrir())
    clave = at.query_params["sesion"]
    clave = clave[0] if isinstance(clave, list) else clave
    _boton(at, "Borrar resultados").click()
    at.run()
    assert "resultado" not in at.session_state
    assert "sesion" not in at.query_params

    recargada = _abrir(clave)
    assert "resultado" not in recargada.session_state
    assert any("ya no están disponibles" in m.value for m in recargada.markdown)


def test_clave_desconocida_no_falla():
    at = _abrir("clave-que-no-existe")
    assert not at.exception
    assert "resultado" not in at.session_state
    assert "sesion" not in at.query_params


def test_f5_en_inicio_conserva_la_clave_para_volver_a_seguimiento():
    at = _procesar(_abrir())
    clave = at.query_params["sesion"]
    clave = clave[0] if isinstance(clave, list) else clave
    inicio = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=60)
    inicio.query_params["sesion"] = clave
    inicio.run()
    assert not inicio.exception
    assert inicio.session_state["_memoria_clave"] == clave       # al ir a Seguimiento se recupera con esta clave

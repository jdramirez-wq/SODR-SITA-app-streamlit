"""Condiciones numéricas de las Alertas Tipo 1, 2 y 3 del prompt (las que una IA sencilla confundía)."""
import pandas as pd

from src.evaplan.condiciones import condiciones_prompt, texto_condicion


def _fila(**kw):
    base = dict(resultado=0.0, ppto_obligaciones=5_600_000_000.0, pct_ejecucion_financiera=0.611,
                pct_avance_vigencia=0.0, avance_actividades=0.5, tiene_plan_de_accion=True, menciona_gestion=False,
                dificultades_gestiones=pd.NA, n_registros_con_obligaciones_sin_avance=0,
                avance_por_proyecto="PI-1: 50,0 %")
    base.update(kw)
    return pd.Series(base)


def _estado(f):
    return {c["tipo"]: c["se_cumple"] for c in condiciones_prompt(f)}


def test_obligaciones_altas_y_resultado_cero_es_tipo_2_no_tipo_1():
    assert _estado(_fila()) == {1: False, 2: True, 3: False}


def test_tipo_2_exige_mas_de_30_por_ciento():
    assert _estado(_fila(pct_ejecucion_financiera=0.117))[2] is False


def test_tipo_1_avance_sin_obligaciones():
    e = _estado(_fila(resultado=5.0, ppto_obligaciones=0.0, pct_ejecucion_financiera=0.0, pct_avance_vigencia=0.5))
    assert e[1] is True and e[2] is False


def test_tipo_3_meta_alta_y_algun_proyecto_bajo():
    f = _fila(resultado=10.0, pct_avance_vigencia=1.0, avance_actividades=0.6, avance_por_proyecto="P1: 95,0 % | P2: 10,0 %")
    assert _estado(f)[3] is True
    assert _estado(f.copy().replace({"P1: 95,0 % | P2: 10,0 %": "P1: 60,0 %"}))[3] is False


def test_sin_plan_de_accion_no_se_puede_comprobar():
    e = _estado(_fila(tiene_plan_de_accion=False, pct_ejecucion_financiera=pd.NA))
    assert e[1] is None and e[2] is None
    assert "NO SE PUEDE COMPROBAR" in texto_condicion(condiciones_prompt(_fila(tiene_plan_de_accion=False))[0])

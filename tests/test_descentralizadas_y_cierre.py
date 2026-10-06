"""Entidades descentralizadas (otro código en el Z023, actividades con código PPM) y recordatorios de cierre."""
from pathlib import Path

import pandas as pd
import pytest

from src.evaplan import aportes as A
from src.evaplan import lectura as L
from src.evaplan import pipeline, prompts
from src.evaplan import recordatorios as R
from src.evaplan import validaciones as V

EJ = Path(__file__).resolve().parent.parent / "data" / "ejemplos"
PI, CE, DR, Z = (EJ / "ejemplo_PI_MP_evaplan.xlsx", EJ / "ejemplo_Centralizadas.xlsx",
                 EJ / "ejemplo_PI_Drive.xlsx", EJ / "ejemplo_Z023.xlsx")
CIERRE, MEDIO = "Revisión a Cierre de Vigencia", "Revisión acumulada del Primer semestre"


@pytest.fixture(scope="module")
def z_nombres():
    return pd.DataFrame({"dependencia": ["0006", "1105", "1131"],
                         "nombre_dependencia": ["EJEMPLOVALLE – Instituto de E", "SRIA EDUCACION", "SRIA DE VIVIEN Y HABIT"]})


def test_equivalencia_enlaza_la_descentralizada_por_su_nombre(z_nombres):
    entidades = pd.DataFrame({"codigo_entidad": ["1216", "1105", "7777"],
                              "nombre_entidad": ["INSTITUTO DE EJEMPLO DEL VALLE - EJEMPLOVALLE", "SRIA EDUCACION",
                                                 "ENTIDAD QUE NO ESTA EN EL Z023"]})
    eq = A.equivalencias_z023(entidades, z_nombres)
    assert eq == {"1216": "0006", "1105": "1105"}            # la central conserva su código; la desconocida queda fuera


def test_aportes_de_una_descentralizada_marcan_como_propios_los_de_su_codigo_z023(z_nombres):
    z = pd.DataFrame({
        "dependencia": ["0006", "1131"], "nombre_dependencia": [z_nombres.nombre_dependencia[0], "SRIA DE VIVIEN Y HABIT"],
        "vigencia": [2026, 2026], "codigo_mp": ["MP9900101019901001"] * 2, "proyecto_ppm": ["PI-1", "PI-2"],
        "codigo_proyecto_ps": [pd.NA, "PI31-2"], "nombre_proyecto": ["A", "B"], "bpin": ["2024", "2025"],
        "ppm_actividad": ["1", "2"], "ps_actividad": [pd.NA, "PI31-2/1/1/01/01"], "valor_actividad": [10.0, 20.0]})
    matriz = pd.DataFrame({"codigo_mp": ["MP9900101019901001"], "codigo_entidad": ["1216"]})
    sin_eq = A.construir_aportes(z, matriz, 2026)
    assert not sin_eq["es_propia"].any()                       # sin la equivalencia, todo se vería como ajeno
    con_eq = A.construir_aportes(z, matriz, 2026, {"1216": "0006"}).set_index("codigo_dependencia")
    assert con_eq.loc["0006", "es_propia"] and not con_eq.loc["1131", "es_propia"]
    assert con_eq.loc["0006", "tipo_entidad"] == "Descentralizada"


def test_actividades_con_codigo_ppm_no_se_marcan_fuera_de_proyecto():
    ce = pd.DataFrame({"codigo_proyecto": ["PI-1", "PI99-000001"], "bpin": ["2024", "2025"],
                       "codigo_actividad": ["00000000000000049904", "PI98-000009/1/1/01/01"], "fila_excel": [3, 4]})
    q = V.integridad_centralizadas(ce)
    assert list(q["llave"]) == ["PI98-000009/1/1/01/01"]       # solo el código PS que no empieza por su proyecto


def test_actividad_se_cruza_con_el_z023_por_codigo_ps_o_ppm():
    z = pd.DataFrame({"ps_actividad": ["PI99-000001/1/1/01/01", pd.NA], "ppm_actividad": ["10", "00000000000000049904"],
                      "codigo_mp": ["MP1", "MP2"]})
    ce = pd.DataFrame({"codigo_actividad": ["PI99-000001/1/1/01/01", "00000000000000049904", "123"],
                       "codigo_mp": ["MP1", "MP2", "MP3"], "fila_excel": [3, 4, 5]})
    q = V.centralizadas_vs_z023(ce, z)
    assert list(q["llave"]) == ["123"] and list(q["regla"]) == ["actividad_no_esta_en_z023"]


def test_validar_todo_con_vigencia_2027_usa_los_recursos_de_ese_anio():
    pi, ce, dr, z = (L.leer_pi_mp_evaplan(PI), L.leer_centralizadas(CE), L.leer_pi_drive_mp(DR), L.leer_z023(Z))
    V.validar_todo(pi_mp_evaplan=pi, centralizadas=ce, drive_mp=dr, vigencia=2027, z023=z)   # no debe fallar


def test_deteccion_de_descentralizada():
    ppm = pd.DataFrame({"codigo_actividad": ["00000000000000049904", "00000000000000049905"]})
    ps = pd.DataFrame({"codigo_actividad": ["PI99-000001/1/1/01/01", "PI99-000001/1/1/01/02"]})
    assert R.detectar_descentralizada(ppm, {"1216"}, {}) and not R.detectar_descentralizada(ps, {"9999"}, {})
    assert R.detectar_descentralizada(ps, {"1216"}, {"1216": "0006"})            # manda el código del Z023
    assert not R.detectar_descentralizada(ppm, {"1105"}, {"1105": "1105"})


def test_los_recordatorios_solo_aplican_en_periodos_de_cierre():
    res = pipeline.ejecutar(PI, CE, DR, z023=Z)
    assert R.recordatorios_cierre(MEDIO, res.matriz, True, res.aportes) == []
    assert R.es_cierre("Revisión Acumulada y Proyectada a Cierre de Vigencia") and not R.es_cierre(MEDIO)


def test_recordatorio_de_certificado_para_descentralizada_y_para_aportantes():
    res = pipeline.ejecutar(PI, CE, DR, z023=Z)           # el ejemplo tiene una descentralizada que aporta a una meta
    apor = next(r for r in R.recordatorios_cierre(CIERRE, res.matriz, False, res.aportes)
                if r["id"] == "certificado_financiero_aportantes")
    assert "ENTIDAD DESCENTRALIZADA DE EJEMPLO" in apor["texto"] and apor["metas"] == ["MP9900101019901001"]
    propia = [r["id"] for r in R.recordatorios_cierre(CIERRE, res.matriz, True, None)]
    assert "certificado_financiero_entidad" in propia


def test_recordatorio_de_gestion_aplica_a_todas_las_entidades():
    m = pd.DataFrame({"codigo_mp": ["MP1", "MP2", "MP3"], "estado_reporte": ["Reportada", "Reportada", "Sin reporte en EVAPLAN"],
                      "menciona_gestion": [True, False, True], "resultado": [5.0, 3.0, None]})
    r = R.recordatorios_cierre(CIERRE, m)
    assert [x["id"] for x in r] == ["declaracion_avance_por_gestion"] and r[0]["metas"] == ["MP1"]
    assert R.recordatorios_cierre(CIERRE, m.assign(menciona_gestion=False)) == []     # sin gestión, nada que pedir


def test_el_prompt_no_cambia_sin_recordatorios_y_los_incluye_con_ellos():
    base = prompts.generar_prompt_sistema(CIERRE, 2026, False)
    assert prompts.generar_prompt_sistema(CIERRE, 2026, False, recordatorios=[]) == base
    recs = [{"id": "x", "titulo": "Certificados del avance declarado por gestión", "texto": "Solicítelos.", "metas": ["MP1"]}]
    con = prompts.generar_prompt_sistema(CIERRE, 2026, False, recs)
    assert "ADVERTENCIA: certificados de cierre de vigencia" in con and "MP1" in con
    assert con.index("RECORDATORIOS DE CIERRE") < con.index("BASE DE CONOCIMIENTO")      # antes de las reglas

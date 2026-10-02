from pathlib import Path

import pandas as pd
import pytest

from src.evaplan import lectura as L
from src.evaplan import validaciones as V

EJ = Path(__file__).resolve().parent.parent / "data" / "ejemplos"


@pytest.fixture(scope="module")
def fuentes():
    return dict(
        pi_mp_evaplan=L.leer_pi_mp_evaplan(EJ / "ejemplo_PI_MP_evaplan.xlsx"),
        pi_mr_evaplan=L.leer_pi_mr_evaplan(EJ / "ejemplo_PI_MR_evaplan.xlsx"),
        centralizadas=L.leer_centralizadas(EJ / "ejemplo_Centralizadas.xlsx"),
        drive_mp=L.leer_pi_drive_mp(EJ / "ejemplo_PI_Drive.xlsx"),
        drive_mr=L.leer_pi_drive_mr(EJ / "ejemplo_PI_Drive.xlsx"),
    )


def test_ejemplos_producen_exactamente_las_anomalias_sembradas(fuentes):
    h = V.validar_todo(**fuentes)
    esperado = {
        ("advertencia", "financiero_sin_fisico", "PI99-000002/1/1/01/01"),
        ("advertencia", "mp_falta_en_evaplan", "MP9900202039902003"),
        ("advertencia", "pg_vs_anios[pi]", "MP9900202039902003"),
        ("info", "meta_sin_actividades", "MP9900202019902001"),
    }
    assert set(zip(h["severidad"], h["regla"], h["llave"])) == esperado
    assert (h["severidad"] != "error").all()


def test_evaplan_y_drive_vigente_coinciden(fuentes):
    h = V.valores_evaplan_vs_drive(fuentes["pi_mp_evaplan"], fuentes["drive_mp"])
    assert h.empty


def test_detecta_valores_desactualizados(fuentes):
    ev = fuentes["pi_mp_evaplan"].copy()
    ev.loc[ev["codigo_mp"] == "MP9900101019901001", "valor_2026"] = 99.0
    h = V.valores_evaplan_vs_drive(ev, fuentes["drive_mp"])
    assert len(h) == 1 and "2026: EVAPLAN 99 vs Drive 30" in h.iloc[0]["detalle"]


def test_np_y_cero_no_son_lo_mismo(fuentes):
    ev = fuentes["pi_mp_evaplan"].copy()
    i = ev.index[ev["codigo_mp"] == "MP9900202029902002"][0]
    ev.loc[i, ["valor_2024", "valor_2024_np"]] = [0.0, False]    # Drive dice 'NP'
    h = V.valores_evaplan_vs_drive(ev, fuentes["drive_mp"])
    assert "2024: EVAPLAN 0 vs Drive NP" in h.iloc[0]["detalle"]


def test_invariantes_presupuestales(fuentes):
    ce = fuentes["centralizadas"].copy()
    ce.loc[0, "ppto_obligaciones"] = ce.loc[0, "ppto_definitivo"] + 1_000_000
    ce.loc[1, "ppto_disponible"] = ce.loc[1, "ppto_definitivo"] + 1
    reglas = set(V.presupuesto_invariantes(ce)["regla"])
    assert reglas == {"obligaciones_mayores_definitivo", "disponible_excede_saldo"}


def test_avance_no_coincide(fuentes):
    ce = fuentes["centralizadas"].copy()
    ce.loc[0, "avance_actividad_pct"] = 80.0
    h = V.avance_consistente(ce)
    assert h["regla"].tolist() == ["avance_no_coincide"]


def test_llave_duplicada_y_codigo_mp_invalido(fuentes):
    pi = pd.concat([fuentes["pi_mp_evaplan"], fuentes["pi_mp_evaplan"].iloc[[0]]], ignore_index=True)
    assert (V.llave_unica(pi, "codigo_mp", "x")["regla"] == "llave_unica").all()
    malo = fuentes["pi_mp_evaplan"].copy()
    malo.loc[0, "codigo_mp"] = "MP123"
    malo = L.enriquecer_codigo_mp(malo)
    assert "codigo_mp_formato" in set(V.codigo_mp_coherente(malo, "x")["regla"])


@pytest.mark.parametrize("comportamiento, pg, anios, hay_hallazgo", [
    ("Incremento Acumulado", 10, [0, 4, 3, 3], False),
    ("Incremento Acumulado", 10, [4, 4, 3, 3], True),
    ("Incremento Flujo", 90, [70, 80, 85, 90], False),
    ("Incremento Flujo", 90, [70, 80, 85, 60], True),
    ("Mantenimiento Stock", 100, [100, 100, 100, 100], False),
    ("Mantenimiento Stock", 100, [100, 90, 100, 100], True),
    ("Reducción Anual", 5, [9, 8, 7, 6], False),            # no se valida
])
def test_regla_pg_segun_comportamiento(comportamiento, pg, anios, hay_hallazgo):
    fila = {"codigo_mp": "MP0", "fila_excel": 3, "comportamiento": comportamiento, "valor_pg": pg}
    fila.update({f"valor_{a}": v for a, v in zip(V.ANIOS, anios)})
    assert (len(V.pg_vs_anios(pd.DataFrame([fila]), "t")) == 1) is hay_hallazgo

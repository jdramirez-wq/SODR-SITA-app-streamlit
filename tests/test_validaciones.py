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
        # la hoja MR de ejemplo deja '2025' sin marcar aunque ya cerró (inconsistencia real observada)
        ("advertencia", "vigencia_cerrada_sin_marca_logro", "2025"),
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
    ("Incremento Capacidad", 25, [4, 11, 18, 25], False),   # nivel alcanzado cada año; PG = 2027
    ("Incremento Capacidad", 200, [50, 50, 50, 50], True),   # escrito como incrementos que se suman
    ("Mantenimiento Stock", 100, [100, 100, 100, 100], False),
    ("Mantenimiento Stock", 100, [100, 90, 100, 100], True),
    ("Reducción Anual", 5, [9, 8, 7, 6], False),            # no se valida
])
def test_regla_pg_segun_comportamiento(comportamiento, pg, anios, hay_hallazgo):
    fila = {"codigo_mp": "MP0", "fila_excel": 3, "comportamiento": comportamiento, "valor_pg": pg}
    fila.update({f"valor_{a}": v for a, v in zip(V.ANIOS, anios)})
    assert (len(V.pg_vs_anios(pd.DataFrame([fila]), "t")) == 1) is hay_hallazgo


def test_vigencia_se_infiere_de_los_encabezados_de_drive(fuentes):
    assert V.inferir_vigencia(fuentes["drive_mp"]) == 2026       # 2024 y 2025 marcados 'VAL ALC'
    assert fuentes["drive_mp"]["valor_2024_logro"].all() and not fuentes["drive_mp"]["valor_2026_logro"].any()


def test_marca_logro_detecta_inconsistencias(fuentes):
    mp = fuentes["drive_mp"]
    assert V.marca_logro_vs_vigencia(mp, "x", 2026).empty
    h = V.marca_logro_vs_vigencia(mp, "x", 2027)                  # si la vigencia fuera 2027, 2026 debería estar marcado
    assert h["regla"].tolist() == ["vigencia_cerrada_sin_marca_logro"] and h["llave"].tolist() == ["2026"]
    h = V.marca_logro_vs_vigencia(mp, "x", 2025)                  # 2025 marcado pero aún no cerrada
    assert h["regla"].tolist() == ["vigencia_abierta_con_marca_logro"]


def test_la_llave_de_centralizadas_es_el_id_del_registro_no_el_codigo_de_actividad(fuentes):
    ce = fuentes["centralizadas"]
    assert ce["codigo_actividad"].duplicated().any()                    # una actividad con 2 registros
    h = V.validar_todo(**fuentes)
    assert "llave_unica" not in set(h["regla"])
    repetido = pd.concat([ce, ce.iloc[[0]]], ignore_index=True)         # mismo ID dos veces: eso sí es un error
    assert V.llave_unica(repetido, "id_registro", "centralizadas")["regla"].tolist() == ["llave_unica"] * 2


def test_producto_mga_distinto_al_del_codigo_es_advertencia_no_error(fuentes):
    ce = fuentes["centralizadas"].copy()
    ce.loc[0, "codigo_producto_mga"] = "9901000"
    h = V.codigo_mp_coherente(ce, "centralizadas")
    assert h["severidad"].tolist() == ["advertencia"] and h["regla"].tolist() == ["codigo_mp_vs_producto_mga"]


def test_actividad_de_meta_ajena_es_advertencia_no_error(fuentes):
    ce = fuentes["centralizadas"].copy()
    ce.loc[0, "codigo_mp"] = "MP9800101019801001"                       # meta coordinada por otra dependencia
    h = V.cobertura_centralizadas_vs_pi(ce, fuentes["pi_mp_evaplan"])
    assert ("actividad_sin_meta_en_pi", "advertencia") in set(zip(h["regla"], h["severidad"]))
    assert "OTRA" in h.iloc[0]["detalle"].upper()


def test_las_validaciones_de_drive_solo_miran_las_entidades_cargadas(fuentes):
    dm = fuentes["drive_mp"].copy()
    ajena = dm["entidad_codigo"] == "9998"
    dm.loc[ajena, ["pi_pg", "pi_2027"]] = [999.0, 0.0]                  # rompe la regla del PG en OTRA entidad
    h = V.validar_todo(**{**fuentes, "drive_mp": dm})
    assert not any(h["llave"].isin(dm.loc[ajena, "codigo_mp"]))         # no se reporta: no es de la dependencia
    solo_ajena = V.validar_todo(drive_mp=dm)                            # sin archivos de EVAPLAN se revisa todo el libro
    assert any(solo_ajena["llave"].isin(dm.loc[ajena, "codigo_mp"]))

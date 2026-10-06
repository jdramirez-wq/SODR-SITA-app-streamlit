"""Lo que se muestra en pantalla: filtros, orden (lo urgente primero) y textos. Usa el ejemplo ficticio."""
from pathlib import Path

import pandas as pd
import pytest

from src.evaplan import pipeline, vista

EJ = Path(__file__).resolve().parent.parent / "data" / "ejemplos"


@pytest.fixture(scope="module")
def res():
    return pipeline.ejecutar(EJ / "ejemplo_PI_MP_evaplan.xlsx", EJ / "ejemplo_Centralizadas.xlsx",
                             EJ / "ejemplo_PI_Drive.xlsx", z023=EJ / "ejemplo_Z023.xlsx")


def test_conteo_de_filtros(res):
    n = vista.contar_filtros(res.matriz)
    assert n["Todas"] == 5 and n["Sin reporte"] == 1 and n["Compartidas"] == 1
    assert n["Con alertas"] == int((res.matriz["n_alertas"] > 0).sum())
    assert "Compartidas" not in vista.contar_filtros(res.matriz.drop(columns="n_proyectos_ajenos"))


def test_las_metas_con_mas_alertas_van_primero(res):
    v = vista.filtrar_metas(res.matriz, res.hallazgos)
    assert list(v["n_alertas"]) == sorted(v["n_alertas"], reverse=True)
    assert set(vista.filtrar_metas(res.matriz, res.hallazgos, "Sin reporte")["codigo_mp"]) == {"MP9900202039902003"}
    assert set(vista.filtrar_metas(res.matriz, res.hallazgos, "Compartidas")["codigo_mp"]) == {"MP9900101019901001"}


def test_filtrar_por_tipo_de_hallazgo_y_texto(res):
    v = vista.filtrar_metas(res.matriz, res.hallazgos, regla="sin_reporte")
    assert list(v["codigo_mp"]) == ["MP9900202039902003"]
    assert list(vista.filtrar_metas(res.matriz, res.hallazgos, texto="mp99002020199")["codigo_mp"]) == ["MP9900202019902001"]
    assert vista.filtrar_metas(res.matriz, res.hallazgos, texto="no existe").empty


def test_alertas_se_separan_en_revision_e_informativas(res):
    revision, info = vista.alertas_de(res.hallazgos, "MP9900101019901001")
    assert (revision["severidad"] != "info").all() and (info["severidad"] == "info").all()
    assert "meta_con_aportes_de_otras_entidades" in set(info["regla"])


def test_tabla_de_metas_usa_porcentajes_de_0_a_100(res):
    t = vista.tabla_metas(vista.filtrar_metas(res.matriz, res.hallazgos))
    assert list(t.columns[:3]) == ["Código", "Meta", "Reportó"] and "Otras entidades" in t.columns
    fila = t[t["Código"] == "MP9900101019901001"].iloc[0]
    assert fila["% de la meta"] == pytest.approx(40.0) and set(t["Reportó"]) <= {"✅ Sí", "⛔ No"}


def test_textos_cortos():
    assert vista.recortar("a  b\nc", 10) == "a b c" and vista.recortar("x" * 100, 10) == "x" * 9 + "…"
    assert vista.recortar(pd.NA) == "" and vista.recortar(None) == ""
    assert vista.lineas_por_proyecto("P1: 50.0 % | P2: 0.0 %") == ["P1: 50.0 %", "P2: 0.0 %"]
    assert vista.lineas_por_proyecto(pd.NA) == []

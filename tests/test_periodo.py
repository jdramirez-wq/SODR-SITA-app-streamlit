"""Periodo de revisión flexible: cualquier mes de corte, proyección de cierre o cierre definitivo."""
from datetime import date

import pytest

from src.evaplan.periodo import Periodo, como_periodo, mes_por_defecto
from src.evaplan.prompts import generar_prompt_sistema
from src.evaplan.recordatorios import es_cierre


def test_etiquetas_y_cierre():
    assert Periodo("parcial", 10).etiqueta == "Acumulado a octubre" and not Periodo("parcial", 10).es_cierre
    assert Periodo("proyectado", 11).etiqueta == "Acumulado a noviembre y proyección de cierre"
    assert Periodo("proyectado", 11).es_cierre and Periodo("cierre").es_cierre and es_cierre(Periodo("cierre"))
    with pytest.raises(ValueError):
        Periodo("parcial", 13)


def test_mes_por_defecto_es_el_ultimo_mes_cerrado():
    assert mes_por_defecto(date(2026, 11, 4)) == 10 and mes_por_defecto(date(2026, 1, 15)) == 1


def test_el_prompt_usa_el_mes_de_corte():
    p = generar_prompt_sistema(Periodo("parcial", 10), 2026, False)
    assert "acumulado de enero a octubre de 2026 (mes 10 de 12)" in p and "Primer Trimestre" not in p
    assert "40%-50%" in generar_prompt_sistema(Periodo("parcial", 6), 2026, False)        # texto original de junio
    assert "40%-50%" not in p
    proy = generar_prompt_sistema(Periodo("proyectado", 11), 2026, False)
    assert "proyección de cierre" in proy and "noviembre" in proy
    assert "Cierre Final de la Vigencia" in generar_prompt_sistema(Periodo("cierre"), 2026, False)


def test_compatibilidad_con_los_nombres_anteriores():
    assert como_periodo("Revisión acumulada de primer trimestre") == Periodo("parcial", 3)
    assert como_periodo("Revisión a Cierre de Vigencia").es_cierre

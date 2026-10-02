import pandas as pd
import pytest

from src.evaplan import limpieza as lz


@pytest.mark.parametrize("entrada, esperado", [
    (0, 0.0), ("0", 0.0), ("1.500,00", 1500.0), ("41.667", 41.667), (41.667, 41.667), ("1,5", 1.5), (7, 7.0),
    ("22.7", 22.7), ("100%", 100.0),
])
def test_decimal_formatos_validos(entrada, esperado):
    assert lz.decimal(entrada) == pytest.approx(esperado)


@pytest.mark.parametrize("entrada, esperado", [
    ("2.339.400.000", 2339400000.0), (0, 0.0), ("0", 0.0), ("$ 5.432.239.329", 5432239329.0), ("41.667", 41667.0),
    ("1.500,50", 1500.5), ("-1.250", -1250.0), (2339400000, 2339400000.0),
])
def test_moneda_el_punto_es_separador_de_miles(entrada, esperado):
    assert lz.moneda(entrada) == pytest.approx(esperado)


@pytest.mark.parametrize("entrada", [None, float("nan"), "", ".", "NP", "NO DISPONIBLE", "ERROR", "#DIV/0!", "abc", True])
def test_decimal_sin_dato(entrada):
    assert lz.decimal(entrada) is pd.NA


def test_valor_np_distingue_no_programado_de_cero():
    assert lz.valor_np("NP") == (pd.NA, True)
    assert lz.valor_np(" np ") == (pd.NA, True)
    assert lz.valor_np(0) == (0.0, False)
    assert lz.valor_np(None) == (pd.NA, False)


def test_texto_trata_marcadores_como_vacio():
    assert lz.texto(".") is pd.NA and lz.texto("nan") is pd.NA and lz.texto("  ") is pd.NA
    assert lz.texto("  hola   mundo ") == "hola mundo"


def test_codigo_no_pierde_digitos_ni_agrega_decimales():
    assert lz.codigo(2024009990001) == "2024009990001"
    assert lz.codigo(9902062.0) == "9902062"
    assert lz.codigo("PI99-000001") == "PI99-000001"
    assert lz.codigo(float("nan")) is pd.NA


def test_entero_descarta_rangos_de_anios():
    assert lz.entero(2023.0) == 2023
    assert lz.entero("2020-2023") is pd.NA


@pytest.mark.parametrize("entrada, esperado", [
    ("9999 - SECRETARÍA DE EJEMPLO", ("9999", "SECRETARÍA DE EJEMPLO")),
    ("99001 - 99001-ALCANZAR 8.000 PERSONAS", ("99001", "ALCANZAR 8.000 PERSONAS")),
    ("04 - Valle con + Competencias Digitales", ("04", "Valle con + Competencias Digitales")),
    ("9999", ("9999", pd.NA)),
    (None, (pd.NA, pd.NA)),
])
def test_dividir_codigo_nombre(entrada, esperado):
    assert lz.dividir_codigo_nombre(entrada) == esperado


def test_codigo_mr_quita_prefijo():
    assert lz.codigo_mr("MR99001") == "99001" and lz.codigo_mr(99001) == "99001"


def test_descomponer_codigo_mp():
    assert lz.descomponer_codigo_mp("MP9900204099902101") == {
        "mr": "99002", "programa": "99", "subprograma": "04", "consecutivo": "09", "producto_mga": "9902101"}
    assert lz.descomponer_codigo_mp("MP990020409990210") is None      # 17 caracteres
    assert lz.descomponer_codigo_mp("XX9900204099902101") is None
    assert lz.descomponer_codigo_mp(pd.NA) is None


def test_normalizar_encabezado_y_comportamiento():
    assert lz.normalizar_encabezado(2026.0) == "2026"
    assert lz.normalizar_encabezado("VAL ALC 2024\n") == "VAL ALC 2024"
    assert lz.normalizar_encabezado("EDT\n(corte 02/03/2026)") == "EDT (corte 02/03/2026)"
    assert lz.normalizar_comportamiento("Incremento flujo") == "Incremento Flujo"


def test_si_no():
    assert lz.si_no("Sí") is True and lz.si_no("No") is False and lz.si_no(None) is pd.NA

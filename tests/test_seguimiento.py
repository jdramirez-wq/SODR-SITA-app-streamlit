import io
from pathlib import Path

import pandas as pd
import pytest
from openpyxl import load_workbook

from src.evaplan import lectura as L
from src.evaplan import pipeline, reportes
from src.evaplan import seguimiento as S

EJ = Path(__file__).resolve().parent.parent / "data" / "ejemplos"
PI, CE, DR = (EJ / "ejemplo_PI_MP_evaplan.xlsx", EJ / "ejemplo_Centralizadas.xlsx", EJ / "ejemplo_PI_Drive.xlsx")


@pytest.fixture(scope="module")
def datos():
    return L.leer_pi_mp_evaplan(PI), L.leer_centralizadas(CE), L.leer_pi_drive_mp(DR)


@pytest.fixture(scope="module")
def matriz(datos):
    return S.construir_matriz(*datos).set_index("codigo_mp")


def test_universo_incluye_metas_sin_reporte(matriz):
    assert len(matriz) == 5 and (matriz["estado_reporte"] == "Reportada").sum() == 4
    assert matriz.loc["MP9900202039902003", "estado_reporte"] == "Sin reporte en EVAPLAN"
    assert matriz["vigencia"].eq(2026).all()                       # inferida de los encabezados 'VAL ALC'


def test_sin_drive_solo_hay_metas_reportadas(datos):
    pi, ce, _ = datos
    m = S.construir_matriz(pi, ce, None, vigencia=2026)
    assert len(m) == 4 and (m["estado_reporte"] == "Reportada").all()


def test_avance_acumulado_usa_logros_previos_y_resultado(matriz):
    f = matriz.loc["MP9900101019901001"]                           # Acumulado: PG 100; logros 20+30; meta 2026 = 30
    assert f["logro_previo"] == 50 and f["resultado"] == 12
    assert f["pct_avance_vigencia"] == pytest.approx(12 / 30)
    assert f["avance_cuatrienio"] == 62 and f["pct_avance_pg"] == pytest.approx(0.62)


def test_flujo_no_acumula_logros_previos(matriz):
    f = matriz.loc["MP9900101029901002"]
    assert pd.isna(f["logro_previo"]) and pd.isna(f["pct_avance_pg"])
    assert f["pct_avance_vigencia"] == pytest.approx(41.667 / 85)


def test_presupuesto_y_avance_de_actividades_por_proyecto(matriz):
    f = matriz.loc["MP9900101019901001"]
    assert f["ppto_definitivo"] == 2_500_000_000 and f["ppto_obligaciones"] == 1_500_000_000
    assert f["pct_ejecucion_financiera"] == pytest.approx(0.6)
    assert f["avance_actividades"] == pytest.approx(0.125)         # (25 % + 0 %) / 2
    assert f["avance_por_proyecto"] == "PI99-000001: 12.5 %"
    assert f["n_proyectos"] == 1 and f["n_actividades"] == 2
    assert not matriz.loc["MP9900202019902001", "tiene_plan_de_accion"]


def test_el_promedio_se_calcula_por_proyecto_cuando_hay_varios(datos):
    pi, ce, dr = datos
    ce = ce.copy()
    ce.loc[ce["codigo_actividad"] == "PI99-000001/1/2/01/03", ["codigo_mp", "codigo_proyecto", "avance_actividad_pct"]] = \
        ["MP9900101019901001", "PI99-000009", 80.0]
    f = S.construir_matriz(pi, ce, dr).set_index("codigo_mp").loc["MP9900101019901001"]
    assert f["n_proyectos"] == 2 and "PI99-000001: 12.5 %" in f["avance_por_proyecto"] \
        and "PI99-000009: 80.0 %" in f["avance_por_proyecto"]


def test_focalizacion_replica_la_logica_original(datos):
    pi, ce, dr = datos
    f = S.construir_matriz(pi, ce, dr).set_index("codigo_mp").loc["MP9900101019901001"]
    assert f["focalizacion"] == "¿Cuál Otro?: Servidores públicos"       # Otros=0 pero hay texto, como en la página original


def test_hallazgos_sembrados(matriz, datos):
    h = S.detectar_hallazgos(matriz.reset_index())
    pares = set(zip(h["regla"], h["llave"]))
    assert ("sin_reporte", "MP9900202039902003") in pares
    assert ("sin_plan_de_accion", "MP9900202019902001") in pares
    assert ("actividades_con_obligaciones_sin_avance", "MP9900202029902002") in pares
    assert ("narrativa_con_resultado_cero", "MP9900202019902001") in pares


def test_avance_sin_obligaciones_exige_justificar_gestion(datos):
    pi, ce, dr = datos
    ce0 = ce.copy()
    ce0.loc[ce0["codigo_mp"] == "MP9900101029901002", "ppto_obligaciones"] = 0.0
    h = S.detectar_hallazgos(S.construir_matriz(pi, ce0, dr))
    assert ("avance_sin_ejecucion_financiera", "advertencia") in set(zip(h["regla"], h["severidad"]))
    pi2 = pi.copy()
    pi2.loc[pi2["codigo_mp"] == "MP9900101029901002", "principal_logro"] = "Se logró por gestión con otra entidad"
    h2 = S.detectar_hallazgos(S.construir_matriz(pi2, ce0, dr))
    assert ("avance_sin_ejecucion_con_gestion", "info") in set(zip(h2["regla"], h2["severidad"]))
    assert "avance_sin_ejecucion_financiera" not in set(h2["regla"])


def test_no_se_inventan_umbrales(matriz):
    """Una meta con 100 % de ejecución financiera y 0 % de avance físico NO genera juicio de 'crítico' por umbral:
    solo hechos. La única alerta de ese estilo es la objetiva (obligaciones > 0 sin avance de actividades)."""
    reglas = set(S.detectar_hallazgos(matriz.reset_index())["regla"])
    assert not any("umbral" in r or "critic" in r or "semaforo" in r for r in reglas)


def test_pipeline_completo_y_reportes():
    r = pipeline.ejecutar(PI, CE, DR)
    assert r.vigencia == 2026 and r.usa_drive and r.resumen["metas_sin_reporte"] == 1
    assert not r.calidad.empty and (r.calidad["severidad"] != "error").all()
    wb = load_workbook(io.BytesIO(reportes.a_excel(r.matriz, r.hallazgos, r.calidad)))
    assert wb.sheetnames == ["MP_PI_PA", "Hallazgos", "Sin_reporte", "Calidad_de_datos"]
    assert wb["MP_PI_PA"].max_row == 6
    pdf = reportes.a_pdf(r.matriz)
    assert pdf.startswith(b"%PDF") and len(pdf) > 3000


def test_pipeline_sin_drive_y_con_drive_caido():
    r = pipeline.ejecutar(PI, CE, None, vigencia=2026)
    assert not r.usa_drive and r.resumen["metas_sin_reporte"] == 0
    r2 = pipeline.ejecutar(PI, CE, "https://no-existe.invalid/x.xlsx", vigencia=2026)
    assert r2.avisos and "Drive" in r2.avisos[0] and len(r2.matriz) == 4


def test_pipeline_con_archivo_subido_se_puede_leer_dos_veces():
    pi, ce = io.BytesIO(PI.read_bytes()), io.BytesIO(CE.read_bytes())
    pipeline.ejecutar(pi, ce, None, vigencia=2026)
    r = pipeline.ejecutar(pi, ce, None, vigencia=2026)            # segundo clic en "Procesar"
    assert len(r.matriz) == 4


def test_estructura_incorrecta_da_error_claro():
    with pytest.raises(L.EsquemaError, match="Código de Meta"):
        pipeline.ejecutar(CE, CE, None)                           # el usuario subió Centralizadas en el lugar del PI

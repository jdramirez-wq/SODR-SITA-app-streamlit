"""Estilo común de la plataforma: tipografía, paleta, tarjetas, alertas y encabezados. Solo presentación.

Decisiones de diseño:
  - Una sola paleta (verde institucional sobrio + ámbar solo para "requiere atención"). Sin colores de semáforo
    sobre los porcentajes: la herramienta no emite juicios.
  - Tipografía Inter (definida en .streamlit/config.toml) con números tabulares para que las cifras alineen.
  - Jerarquía clara: encabezado → acciones → cifras → lista → ficha; lo técnico queda plegado.
"""
from __future__ import annotations

from html import escape

import streamlit as st

CSS = """
<style>
:root {
    --verde: #0F766E; --verde-oscuro: #0B4F4A; --verde-claro: #E6F2F0; --verde-tenue: #F3F8F7;
    --borde: #DCE5E3; --texto: #14302C; --suave: #5B7470; --ambar: #B45309; --ambar-claro: #FFF7EB;
    --ambar-borde: #F5D9AE; --rojo: #B42318; --rojo-claro: #FEF3F2; --radio: 14px;
}
.stApp {font-feature-settings: "tnum" 1;}   /* números tabulares: las cifras alinean */
footer, #MainMenu {visibility: hidden;}
div[data-testid="stHeader"] {background: transparent;}
.block-container {padding-top: 1.6rem; padding-bottom: 4rem; max-width: 1180px;}
h1, h2, h3, h4, h5 {letter-spacing: -0.015em; color: var(--texto);}
h3 {font-size: 1.12rem !important; font-weight: 650 !important; margin-top: .6rem;}
h5 {font-size: .95rem !important; font-weight: 650 !important; color: var(--verde-oscuro) !important;}

/* Barra lateral */
section[data-testid="stSidebar"] {background: var(--verde-tenue); border-right: 1px solid var(--borde);}
section[data-testid="stSidebar"] h3 {font-size: .8rem !important; text-transform: uppercase; letter-spacing: .08em;
                                     color: var(--suave);}

/* Encabezado grande (portada / antes de cargar) */
.hero {background: linear-gradient(120deg, var(--verde-oscuro) 0%, var(--verde) 70%, #14907F 100%); color: #fff;
       border-radius: 20px; padding: 1.6rem 1.9rem; margin-bottom: 1.1rem; position: relative; overflow: hidden;}
.hero:after {content: ""; position: absolute; right: -60px; top: -60px; width: 220px; height: 220px;
             border-radius: 50%; background: rgba(255,255,255,.07);}
.hero .eyebrow {font-size: .75rem; text-transform: uppercase; letter-spacing: .12em; opacity: .8; margin-bottom: .35rem;}
.hero h1 {color: #fff; font-size: 1.75rem; font-weight: 700; margin: 0 0 .35rem 0; padding: 0;}
.hero p {color: rgba(255,255,255,.88); margin: 0; font-size: .97rem; max-width: 760px; line-height: 1.5;}

/* Encabezado compacto (con resultados) */
.barra-titulo {display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
               padding: .2rem 0 .9rem 0; border-bottom: 1px solid var(--borde); margin-bottom: 1rem;}
.barra-titulo .t {font-size: 1.35rem; font-weight: 700; color: var(--texto); letter-spacing: -0.02em;}
.barra-titulo .t span {color: var(--verde);}
.pildora {display: inline-flex; align-items: center; gap: .4rem; background: var(--verde-claro); color: var(--verde-oscuro);
          border-radius: 999px; padding: .25rem .8rem; font-size: .8rem; font-weight: 500;}
.pildora.ambar {background: var(--ambar-claro); color: var(--ambar);}
.pildora.gris {background: #EEF1F0; color: var(--suave);}

/* Pasos de inicio */
.pasos {display: grid; grid-template-columns: repeat(3, 1fr); gap: .8rem; margin: .2rem 0 1rem 0;}
.paso {background: #fff; border: 1px solid var(--borde); border-radius: var(--radio); padding: .95rem 1.1rem;}
.paso b {color: var(--texto); font-weight: 600;} .paso span.d {color: var(--suave); font-size: .88rem; line-height: 1.45;}
.paso .n {display: inline-flex; width: 1.55rem; height: 1.55rem; border-radius: 8px; background: var(--verde-claro);
          color: var(--verde-oscuro); align-items: center; justify-content: center; font-size: .8rem; font-weight: 700;
          margin-right: .5rem;}

/* Tarjetas de cifras */
.kpis {display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem; margin: .5rem 0 1.4rem 0;}
.kpi {border: 1px solid var(--borde); border-radius: var(--radio); padding: .9rem 1.1rem; background: #fff;
      box-shadow: 0 1px 2px rgba(20,48,44,.04);}
.kpi .et {font-size: .72rem; text-transform: uppercase; letter-spacing: .07em; color: var(--suave); font-weight: 600;}
.kpi .v {font-size: 1.95rem; font-weight: 700; color: var(--texto); line-height: 1.2; margin-top: .15rem;}
.kpi .d {font-size: .8rem; color: var(--suave); line-height: 1.35;}
.kpi.atencion {background: var(--ambar-claro); border-color: var(--ambar-borde);} .kpi.atencion .v {color: var(--ambar);}

/* Chips */
.chips {display: flex; flex-wrap: wrap; gap: .4rem; margin: .3rem 0 .9rem 0;}
.chip {background: var(--verde-claro); color: var(--verde-oscuro); border-radius: 999px; padding: .12rem .7rem;
       font-size: .78rem; font-weight: 500;}

/* Ficha de la meta */
.ficha-codigo {font-family: ui-monospace, 'SFMono-Regular', monospace; color: var(--verde); font-size: .82rem;
               letter-spacing: .02em;}
.ficha-titulo {font-size: 1.08rem; font-weight: 650; color: var(--texto); margin: .1rem 0 .1rem 0; line-height: 1.4;}
.datos {display: grid; grid-template-columns: auto 1fr; gap: .35rem 1rem; margin: .2rem 0 .6rem 0;}
.datos dt, .datos dd {font-size: .9rem; line-height: 1.4;}
.datos dt {color: var(--suave); margin: 0;} .datos dd {margin: 0; color: var(--texto); font-weight: 500; text-align: right;}
.datos dd.destacado {color: var(--verde-oscuro); font-weight: 700;}
.nota {color: var(--suave); font-size: .8rem; line-height: 1.45; margin-bottom: .6rem;}
.vacio {color: var(--suave); font-style: italic;}

/* Alertas como tarjetas (más livianas que los bloques de color de Streamlit) */
.alerta {border: 1px solid var(--ambar-borde); border-left: 4px solid var(--ambar); background: var(--ambar-claro);
         border-radius: 10px; padding: .55rem .8rem; margin-bottom: .5rem; font-size: .88rem; line-height: 1.45;}
.alerta b {display: block; color: var(--ambar); font-size: .82rem; margin-bottom: .1rem;}
.alerta.error {border-color: #F6C9C4; border-left-color: var(--rojo); background: var(--rojo-claro);}
.alerta.error b {color: var(--rojo);}
.alerta.info {border-color: var(--borde); border-left-color: #9DB3AF; background: var(--verde-tenue);}
.alerta.info b {color: var(--suave);}
.alerta.ok {border-color: #BFE3D9; border-left-color: var(--verde); background: var(--verde-claro);}
.alerta.ok b {color: var(--verde-oscuro);}

/* Ajustes de componentes de Streamlit */
div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: var(--radio) !important;}
div[data-testid="stExpander"] details {border-radius: 12px; border-color: var(--borde);}
div[data-testid="stExpander"] summary p {font-weight: 500;}
.stButton button, .stDownloadButton button, .stLinkButton a {border-radius: 10px; font-weight: 500;}
div[data-testid="stMetricLabel"] p {font-size: .74rem; text-transform: uppercase; letter-spacing: .06em;
                                    color: var(--suave); font-weight: 600;}
div[data-testid="stMetricValue"] {font-size: 1.55rem; font-weight: 700; color: var(--texto);}
div[data-testid="stDataFrame"] {border-radius: 12px; overflow: hidden;}

/* Cargador de archivos en español */
div[data-testid="stFileUploaderDropzoneInstructions"] span, div[data-testid="stFileUploaderDropzoneInstructions"] small
    {font-size: 0 !important;}
div[data-testid="stFileUploaderDropzoneInstructions"] > div:after
    {content: "Arrastra aquí el archivo o elígelo"; font-size: .85rem; color: var(--suave);}
div[data-testid="stFileUploaderDropzone"] button p {font-size: 0 !important;}
div[data-testid="stFileUploaderDropzone"] button p:after {content: "Elegir archivo"; font-size: .875rem;}

@media (max-width: 900px) {.kpis, .pasos {grid-template-columns: repeat(2, 1fr);} .hero h1 {font-size: 1.4rem;}}
</style>
"""


def aplicar_estilos() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def encabezado(titulo: str, subtitulo: str, eyebrow: str = "SODR · Plan de Desarrollo Departamental") -> None:
    st.markdown(f'<div class="hero"><div class="eyebrow">{escape(eyebrow)}</div><h1>{escape(titulo)}</h1>'
                f'<p>{escape(subtitulo)}</p></div>', unsafe_allow_html=True)


def barra_titulo(titulo: str, resaltado: str, pildoras: list[tuple[str, str]]) -> None:
    """Encabezado compacto: 'Seguimiento <EVAPLAN>' a la izquierda y píldoras (texto, tono) a la derecha."""
    p = "".join(f'<span class="pildora {tono}">{escape(t)}</span>' for t, tono in pildoras if t)
    st.markdown(f'<div class="barra-titulo"><div class="t">{escape(titulo)} <span>{escape(resaltado)}</span></div>'
                f'<div style="display:flex;gap:.4rem;flex-wrap:wrap">{p}</div></div>', unsafe_allow_html=True)


def pasos(textos: list[tuple[str, str]]) -> None:
    items = "".join(f'<div class="paso"><span class="n">{i}</span><b>{escape(t)}</b><br>'
                    f'<span class="d">{escape(d)}</span></div>' for i, (t, d) in enumerate(textos, start=1))
    st.markdown(f'<div class="pasos">{items}</div>', unsafe_allow_html=True)


def tarjetas(cifras: list[tuple[str, str, str, bool]]) -> None:
    """Fila de tarjetas: (etiqueta, valor, detalle, destacar). Destacar = requiere atención (tono ámbar)."""
    items = "".join(
        f'<div class="kpi{" atencion" if destacar else ""}"><div class="et">{escape(et)}</div>'
        f'<div class="v">{escape(v)}</div><div class="d">{escape(d)}</div></div>'
        for et, v, d, destacar in cifras)
    st.markdown(f'<div class="kpis">{items}</div>', unsafe_allow_html=True)


def chips(textos: list[str]) -> None:
    st.markdown('<div class="chips">' + "".join(f'<span class="chip">{escape(t)}</span>' for t in textos if t)
                + "</div>", unsafe_allow_html=True)


def datos(pares: list[tuple[str, str, bool]]) -> None:
    """Lista de 'dato: valor' alineada (valor a la derecha). El tercer elemento resalta el valor."""
    filas = "".join(f'<dt>{escape(k)}</dt><dd class="{"destacado" if d else ""}">{escape(v)}</dd>' for k, v, d in pares)
    st.markdown(f'<dl class="datos">{filas}</dl>', unsafe_allow_html=True)


def alerta(titulo: str, detalle: str, tono: str = "advertencia") -> None:
    """Tarjeta de alerta. tono: 'error', 'advertencia', 'info' u 'ok'."""
    clase = {"error": "error", "info": "info", "ok": "ok"}.get(tono, "")
    st.markdown(f'<div class="alerta {clase}"><b>{escape(titulo)}</b>{escape(detalle)}</div>', unsafe_allow_html=True)


def nota(texto: str) -> None:
    st.markdown(f'<div class="nota">{escape(texto)}</div>', unsafe_allow_html=True)

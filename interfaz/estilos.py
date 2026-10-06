"""Estilo común de la plataforma: una sola paleta, tarjetas y encabezados. Solo presentación."""
from __future__ import annotations

from html import escape

import streamlit as st

CSS = """
<style>
:root {
    --verde: #0F766E; --verde-oscuro: #0B4F4A; --verde-claro: #E6F2F0; --borde: #DCE5E3;
    --texto: #14302C; --suave: #5B7470; --ambar: #B45309; --ambar-claro: #FEF3E2;
}
footer, #MainMenu {visibility: hidden;}
div[data-testid="stHeader"] {background: transparent;}
.block-container {padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1180px;}
h1, h2, h3 {letter-spacing: -0.01em; color: var(--texto);}
h3 {font-size: 1.15rem !important; margin-top: 0.4rem;}

/* Encabezado de página */
.hero {background: linear-gradient(120deg, var(--verde-oscuro), var(--verde)); color: #fff;
       border-radius: 18px; padding: 1.5rem 1.8rem; margin-bottom: 1.2rem;}
.hero h1 {color: #fff; font-size: 1.7rem; margin: 0 0 .3rem 0; padding: 0;}
.hero p {color: rgba(255,255,255,.88); margin: 0; font-size: .98rem; max-width: 760px;}
.hero .entidad {display: inline-block; background: rgba(255,255,255,.16); border-radius: 999px;
                padding: .15rem .8rem; font-size: .82rem; margin-top: .7rem;}

/* Pasos de inicio */
.pasos {display: grid; grid-template-columns: repeat(3, 1fr); gap: .8rem; margin: .2rem 0 1rem 0;}
.paso {background: var(--verde-claro); border-radius: 14px; padding: .9rem 1.1rem;}
.paso b {color: var(--verde-oscuro);} .paso span {color: var(--suave); font-size: .9rem;}
.paso .n {display: inline-flex; width: 1.5rem; height: 1.5rem; border-radius: 50%; background: var(--verde);
          color: #fff; align-items: center; justify-content: center; font-size: .8rem; margin-right: .4rem;}

/* Tarjetas de cifras */
.kpis {display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem; margin: .4rem 0 1.2rem 0;}
.kpi {border: 1px solid var(--borde); border-radius: 14px; padding: .85rem 1.1rem; background: #fff;}
.kpi .et {font-size: .74rem; text-transform: uppercase; letter-spacing: .06em; color: var(--suave);}
.kpi .v {font-size: 2rem; font-weight: 650; color: var(--texto); line-height: 1.15;}
.kpi .d {font-size: .82rem; color: var(--suave);}
.kpi.atencion {background: var(--ambar-claro); border-color: #F5D9AE;} .kpi.atencion .v {color: var(--ambar);}

/* Chips */
.chips {display: flex; flex-wrap: wrap; gap: .4rem; margin: .2rem 0 .8rem 0;}
.chip {background: var(--verde-claro); color: var(--verde-oscuro); border-radius: 999px; padding: .1rem .7rem;
       font-size: .8rem;}
.chip.gris {background: #EEF1F0; color: var(--suave);}

/* Ficha de la meta */
.ficha-titulo {font-size: 1.05rem; font-weight: 600; color: var(--texto); margin: 0 0 .2rem 0;}
.ficha-codigo {font-family: ui-monospace, monospace; color: var(--verde); font-size: .85rem;}
.vacio {color: var(--suave); font-style: italic;}

@media (max-width: 900px) {.kpis, .pasos {grid-template-columns: repeat(2, 1fr);} .hero h1 {font-size: 1.35rem;}}
</style>
"""


def aplicar_estilos() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def encabezado(titulo: str, subtitulo: str, entidad: str = "") -> None:
    chip = f'<div class="entidad">{escape(entidad)}</div>' if entidad else ""
    st.markdown(f'<div class="hero"><h1>{escape(titulo)}</h1><p>{escape(subtitulo)}</p>{chip}</div>',
                unsafe_allow_html=True)


def pasos(textos: list[tuple[str, str]]) -> None:
    items = "".join(f'<div class="paso"><span class="n">{i}</span><b>{escape(t)}</b><br><span>{escape(d)}</span></div>'
                    for i, (t, d) in enumerate(textos, start=1))
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

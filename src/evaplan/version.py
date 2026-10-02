"""Identifica la versión (commit de Git) del código que está corriendo, para confirmar qué se desplegó."""
from __future__ import annotations

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def version_codigo() -> str:
    """Commit corto (7 caracteres) del código en ejecución, o 'desconocida' si no se puede determinar."""
    try:
        r = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=3)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    try:                                       # sin el programa git: leer .git/HEAD directamente
        head = (RAIZ / ".git" / "HEAD").read_text().strip()
        if head.startswith("ref:"):
            ref = RAIZ / ".git" / head.split(" ", 1)[1]
            if ref.exists():
                return ref.read_text().strip()[:7]
        elif head:
            return head[:7]
    except Exception:
        pass
    return "desconocida"

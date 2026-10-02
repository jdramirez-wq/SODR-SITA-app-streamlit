import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def test_diccionario_de_datos_esta_al_dia():
    r = subprocess.run([sys.executable, str(RAIZ / "scripts" / "generar_diccionario.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr or r.stdout

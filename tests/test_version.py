import re

from src.evaplan.version import version_codigo


def test_version_es_un_commit_corto_o_desconocida():
    assert re.fullmatch(r"[0-9a-f]{7,40}|desconocida", version_codigo())

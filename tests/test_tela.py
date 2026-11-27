"""A tela continua segura depois da migração para o gateway."""
from pathlib import Path


def test_tela_escapa_html_e_nao_tem_scripts_inline():
    js = (Path(__file__).parent.parent / "gateway" / "gateway" / "web" / "app.js").read_text(encoding="utf-8")
    assert "const esc =" in js and "onclick" not in js
    # A tela continua chamando apenas o gateway (API vazia = mesma origem).
    assert 'const API = ""' in js

"""Ambiente de testes comum a todos os serviços.

Define as variáveis antes de qualquer pacote de serviço ser importado, para que
todos validem tokens com o mesmo segredo e não carreguem dados de exemplo.
"""
import os

os.environ.setdefault("JWT_SEGREDO", "segredo-compartilhado-de-teste-com-mais-de-32-caracteres")
os.environ.setdefault("DADOS_EXEMPLO", "0")
os.environ.setdefault("DOCS", "1")

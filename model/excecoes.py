"""
Erros de regra de negócio.

A camada de modelo levanta estes erros e o app.py os transforma
na resposta HTTP certa (404, 409...).
"""


class RegistroNaoEncontrado(Exception):
    """Vira HTTP 404."""


class ConflitoDeDados(Exception):
    """Vira HTTP 409: datas sobrepostas, nome repetido, exclusão bloqueada etc."""

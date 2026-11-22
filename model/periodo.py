"""Funções de apoio para trabalhar com períodos (mês ou ano)."""
from datetime import date
from typing import Optional, Tuple


def intervalo(ano: int, mes: Optional[int] = None) -> Tuple[date, date]:
    """
    Devolve (início, fim) do período. O fim é EXCLUSIVO, ou seja,
    o primeiro dia depois do período. Ex.: jan/2027 -> (2027-01-01, 2027-02-01).
    """
    if mes is None:
        return date(ano, 1, 1), date(ano + 1, 1, 1)
    inicio = date(ano, mes, 1)
    fim = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    return inicio, fim


def noites_no_periodo(check_in: date, check_out: date, inicio: date, fim: date) -> int:
    """Quantas noites da estadia caem dentro do período [inicio, fim)."""
    sobreposicao = (min(check_out, fim) - max(check_in, inicio)).days
    return max(sobreposicao, 0)

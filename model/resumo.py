"""
Resumo financeiro do período: a casa deu lucro ou prejuízo?

Regra de rateio: a receita de uma reserva é dividida pelas noites.
Uma estadia de 30/jan a 03/fev (4 noites) conta 2 noites (metade da receita)
em janeiro e 2 noites em fevereiro. Assim, a soma dos meses bate com o ano.
"""
from collections import defaultdict
from datetime import date
from typing import Optional

from model.database import conectar
from model.periodo import intervalo, noites_no_periodo


def calcular(ano: int, mes: Optional[int] = None) -> dict:
    inicio, fim = intervalo(ano, mes)
    dias_no_periodo = (fim - inicio).days

    with conectar() as conexao:
        plataformas = conexao.execute("SELECT * FROM plataforma ORDER BY nome").fetchall()
        reservas = conexao.execute(
            """SELECT * FROM reserva
                WHERE status = 'confirmada' AND check_in < ? AND check_out > ?""",
            (fim.isoformat(), inicio.isoformat()),
        ).fetchall()
        despesas = conexao.execute(
            """SELECT categoria, SUM(valor) AS total FROM despesa
                WHERE data >= ? AND data < ?
                GROUP BY categoria ORDER BY total DESC""",
            (inicio.isoformat(), fim.isoformat()),
        ).fetchall()

    # Acumuladores por plataforma
    por_plataforma = {
        p["id"]: {"plataforma": p["nome"], "cor": p["cor"], "reservas": 0, "noites": 0,
                  "receita_bruta": 0.0, "comissoes": 0.0}
        for p in plataformas
    }
    noites_ocupadas = 0

    for r in reservas:
        check_in = date.fromisoformat(r["check_in"])
        check_out = date.fromisoformat(r["check_out"])
        total_noites = (check_out - check_in).days
        noites = noites_no_periodo(check_in, check_out, inicio, fim)
        fracao = noites / total_noites
        bruto = r["valor_bruto"] * fracao
        comissao = bruto * r["taxa_aplicada"] / 100

        item = por_plataforma[r["plataforma_id"]]
        item["reservas"] += 1
        item["noites"] += noites
        item["receita_bruta"] += bruto
        item["comissoes"] += comissao
        noites_ocupadas += noites

    lista_plataformas = []
    for item in por_plataforma.values():
        item["receita_bruta"] = round(item["receita_bruta"], 2)
        item["comissoes"] = round(item["comissoes"], 2)
        item["receita_liquida"] = round(item["receita_bruta"] - item["comissoes"], 2)
        lista_plataformas.append(item)

    receita_bruta = round(sum(p["receita_bruta"] for p in lista_plataformas), 2)
    comissoes = round(sum(p["comissoes"] for p in lista_plataformas), 2)
    receita_liquida = round(receita_bruta - comissoes, 2)
    total_despesas = round(sum(d["total"] for d in despesas), 2)
    resultado = round(receita_liquida - total_despesas, 2)

    if resultado > 0:
        situacao = "lucro"
    elif resultado < 0:
        situacao = "prejuizo"
    else:
        situacao = "equilibrio"

    return {
        "ano": ano,
        "mes": mes,
        "periodo_inicio": inicio.isoformat(),
        "periodo_fim": date.fromordinal(fim.toordinal() - 1).isoformat(),
        "receita_bruta": receita_bruta,
        "comissoes": comissoes,
        "receita_liquida": receita_liquida,
        "despesas": total_despesas,
        "resultado": resultado,
        "situacao": situacao,
        "reservas_confirmadas": len(reservas),
        "noites_ocupadas": noites_ocupadas,
        "dias_no_periodo": dias_no_periodo,
        "taxa_ocupacao": round(noites_ocupadas / dias_no_periodo * 100, 1),
        "por_plataforma": lista_plataformas,
        "despesas_por_categoria": [
            {"categoria": d["categoria"], "total": round(d["total"], 2)} for d in despesas
        ],
    }

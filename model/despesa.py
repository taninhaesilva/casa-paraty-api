"""Regras e consultas da tabela `despesa` (manutenção, limpeza, contas...)."""
from typing import Optional

from model.database import conectar
from model.excecoes import RegistroNaoEncontrado
from model import reserva as reserva_model
from model.periodo import intervalo

CONSULTA_BASE = """
    SELECT d.*, r.hospede AS reserva_hospede
      FROM despesa d
      LEFT JOIN reserva r ON r.id = d.reserva_id
"""


def _para_dict(linha) -> dict:
    return {
        "id": linha["id"],
        "data": linha["data"],
        "categoria": linha["categoria"],
        "descricao": linha["descricao"],
        "valor": round(linha["valor"], 2),
        "reserva_id": linha["reserva_id"],
        "reserva_hospede": linha["reserva_hospede"],
    }


def listar(ano: Optional[int] = None, mes: Optional[int] = None,
           categoria: Optional[str] = None) -> list:
    condicoes, parametros = [], []
    if ano:
        inicio, fim = intervalo(ano, mes)
        condicoes.append("d.data >= ? AND d.data < ?")
        parametros += [inicio.isoformat(), fim.isoformat()]
    if categoria:
        condicoes.append("d.categoria = ?")
        parametros.append(categoria)

    sql = CONSULTA_BASE
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    sql += " ORDER BY d.data DESC, d.id DESC"

    with conectar() as conexao:
        linhas = conexao.execute(sql, parametros).fetchall()
    return [_para_dict(l) for l in linhas]


def buscar(despesa_id: int) -> dict:
    with conectar() as conexao:
        linha = conexao.execute(CONSULTA_BASE + " WHERE d.id = ?", (despesa_id,)).fetchone()
    if linha is None:
        raise RegistroNaoEncontrado(f"Despesa {despesa_id} não encontrada.")
    return _para_dict(linha)


def criar(dados: dict) -> dict:
    if dados.get("reserva_id"):
        reserva_model.buscar(dados["reserva_id"])  # 404 se a reserva não existir
    with conectar() as conexao:
        cursor = conexao.execute(
            "INSERT INTO despesa (data, categoria, descricao, valor, reserva_id) VALUES (?, ?, ?, ?, ?)",
            (dados["data"].isoformat(), dados["categoria"], dados["descricao"].strip(),
             dados["valor"], dados.get("reserva_id")),
        )
        novo_id = cursor.lastrowid
    return buscar(novo_id)


def atualizar(despesa_id: int, dados: dict) -> dict:
    buscar(despesa_id)
    if dados.get("reserva_id"):
        reserva_model.buscar(dados["reserva_id"])
    with conectar() as conexao:
        conexao.execute(
            """UPDATE despesa SET data = ?, categoria = ?, descricao = ?, valor = ?, reserva_id = ?
                WHERE id = ?""",
            (dados["data"].isoformat(), dados["categoria"], dados["descricao"].strip(),
             dados["valor"], dados.get("reserva_id"), despesa_id),
        )
    return buscar(despesa_id)


def remover(despesa_id: int) -> None:
    buscar(despesa_id)
    with conectar() as conexao:
        conexao.execute("DELETE FROM despesa WHERE id = ?", (despesa_id,))

"""Regras e consultas da tabela `reserva`."""
from datetime import date
from typing import Optional

from model.database import conectar
from model.excecoes import RegistroNaoEncontrado, ConflitoDeDados
from model import plataforma as plataforma_model
from model.periodo import intervalo

CONSULTA_BASE = """
    SELECT r.*, p.nome AS plataforma_nome, p.cor AS plataforma_cor
      FROM reserva r
      JOIN plataforma p ON p.id = r.plataforma_id
"""


def _para_dict(linha) -> dict:
    check_in = date.fromisoformat(linha["check_in"])
    check_out = date.fromisoformat(linha["check_out"])
    comissao = round(linha["valor_bruto"] * linha["taxa_aplicada"] / 100, 2)
    return {
        "id": linha["id"],
        "hospede": linha["hospede"],
        "plataforma_id": linha["plataforma_id"],
        "plataforma_nome": linha["plataforma_nome"],
        "plataforma_cor": linha["plataforma_cor"],
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "noites": (check_out - check_in).days,
        "num_hospedes": linha["num_hospedes"],
        "valor_bruto": round(linha["valor_bruto"], 2),
        "taxa_aplicada": linha["taxa_aplicada"],
        "valor_comissao": comissao,
        "valor_liquido": round(linha["valor_bruto"] - comissao, 2),
        "status": linha["status"],
        "observacao": linha["observacao"],
    }


def _verificar_conflito(conexao, check_in: date, check_out: date, ignorar_id: Optional[int] = None):
    """
    Duas estadias se sobrepõem quando uma começa antes da outra terminar.
    O dia do check-out pode ser o check-in da próxima (troca de hóspedes no mesmo dia).
    Reservas canceladas não bloqueiam datas.
    """
    conflito = conexao.execute(
        """SELECT id, hospede, check_in, check_out FROM reserva
            WHERE status = 'confirmada'
              AND check_in < ? AND check_out > ?
              AND (? IS NULL OR id <> ?)
            ORDER BY check_in LIMIT 1""",
        (check_out.isoformat(), check_in.isoformat(), ignorar_id, ignorar_id),
    ).fetchone()
    if conflito:
        inicio = date.fromisoformat(conflito["check_in"]).strftime("%d/%m/%Y")
        fim = date.fromisoformat(conflito["check_out"]).strftime("%d/%m/%Y")
        raise ConflitoDeDados(
            f"As datas conflitam com a reserva #{conflito['id']} de "
            f"{conflito['hospede']} ({inicio} a {fim})."
        )


def listar(ano: Optional[int] = None, mes: Optional[int] = None,
           plataforma_id: Optional[int] = None, status: Optional[str] = None) -> list:
    """Lista reservas; com ano/mes, traz as estadias que tocam aquele período."""
    condicoes, parametros = [], []
    if ano:
        inicio, fim = intervalo(ano, mes)
        condicoes.append("r.check_in < ? AND r.check_out > ?")
        parametros += [fim.isoformat(), inicio.isoformat()]
    if plataforma_id:
        condicoes.append("r.plataforma_id = ?")
        parametros.append(plataforma_id)
    if status:
        condicoes.append("r.status = ?")
        parametros.append(status)

    sql = CONSULTA_BASE
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    sql += " ORDER BY r.check_in"

    with conectar() as conexao:
        linhas = conexao.execute(sql, parametros).fetchall()
    return [_para_dict(l) for l in linhas]


def buscar(reserva_id: int) -> dict:
    with conectar() as conexao:
        linha = conexao.execute(CONSULTA_BASE + " WHERE r.id = ?", (reserva_id,)).fetchone()
    if linha is None:
        raise RegistroNaoEncontrado(f"Reserva {reserva_id} não encontrada.")
    return _para_dict(linha)


def criar(dados: dict) -> dict:
    plataforma = plataforma_model.buscar(dados["plataforma_id"])  # 404 se não existir
    with conectar() as conexao:
        if dados["status"] == "confirmada":
            _verificar_conflito(conexao, dados["check_in"], dados["check_out"])
        cursor = conexao.execute(
            """INSERT INTO reserva (hospede, plataforma_id, check_in, check_out, num_hospedes,
                                    valor_bruto, taxa_aplicada, status, observacao)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                dados["hospede"].strip(), dados["plataforma_id"],
                dados["check_in"].isoformat(), dados["check_out"].isoformat(),
                dados["num_hospedes"], dados["valor_bruto"],
                plataforma["taxa_comissao"], dados["status"], dados.get("observacao"),
            ),
        )
        novo_id = cursor.lastrowid
    return buscar(novo_id)


def atualizar(reserva_id: int, dados: dict) -> dict:
    atual = buscar(reserva_id)
    plataforma = plataforma_model.buscar(dados["plataforma_id"])
    # Mantém a taxa original se a plataforma não mudou; se mudou, usa a taxa atual da nova.
    taxa = atual["taxa_aplicada"] if atual["plataforma_id"] == plataforma["id"] else plataforma["taxa_comissao"]
    with conectar() as conexao:
        if dados["status"] == "confirmada":
            _verificar_conflito(conexao, dados["check_in"], dados["check_out"], ignorar_id=reserva_id)
        conexao.execute(
            """UPDATE reserva
                  SET hospede = ?, plataforma_id = ?, check_in = ?, check_out = ?,
                      num_hospedes = ?, valor_bruto = ?, taxa_aplicada = ?,
                      status = ?, observacao = ?
                WHERE id = ?""",
            (
                dados["hospede"].strip(), dados["plataforma_id"],
                dados["check_in"].isoformat(), dados["check_out"].isoformat(),
                dados["num_hospedes"], dados["valor_bruto"], taxa,
                dados["status"], dados.get("observacao"), reserva_id,
            ),
        )
    return buscar(reserva_id)


def remover(reserva_id: int) -> None:
    buscar(reserva_id)
    with conectar() as conexao:
        # Despesas ligadas a esta reserva continuam existindo, só perdem o vínculo.
        conexao.execute("DELETE FROM reserva WHERE id = ?", (reserva_id,))

"""Regras e consultas da tabela `plataforma` (Airbnb, Booking, Direto...)."""
import sqlite3

from model.database import conectar
from model.excecoes import RegistroNaoEncontrado, ConflitoDeDados


def _para_dict(linha) -> dict:
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "taxa_comissao": linha["taxa_comissao"],
        "cor": linha["cor"],
    }


def listar() -> list:
    with conectar() as conexao:
        linhas = conexao.execute("SELECT * FROM plataforma ORDER BY nome").fetchall()
    return [_para_dict(l) for l in linhas]


def buscar(plataforma_id: int) -> dict:
    with conectar() as conexao:
        linha = conexao.execute(
            "SELECT * FROM plataforma WHERE id = ?", (plataforma_id,)
        ).fetchone()
    if linha is None:
        raise RegistroNaoEncontrado(f"Plataforma {plataforma_id} não encontrada.")
    return _para_dict(linha)


def criar(nome: str, taxa_comissao: float, cor: str) -> dict:
    try:
        with conectar() as conexao:
            cursor = conexao.execute(
                "INSERT INTO plataforma (nome, taxa_comissao, cor) VALUES (?, ?, ?)",
                (nome.strip(), taxa_comissao, cor),
            )
            novo_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ConflitoDeDados(f"Já existe uma plataforma chamada '{nome}'.")
    return buscar(novo_id)


def atualizar(plataforma_id: int, nome: str, taxa_comissao: float, cor: str) -> dict:
    """A nova taxa vale só para reservas futuras; as antigas guardam a taxa da época."""
    buscar(plataforma_id)  # garante que existe (senão, 404)
    try:
        with conectar() as conexao:
            conexao.execute(
                "UPDATE plataforma SET nome = ?, taxa_comissao = ?, cor = ? WHERE id = ?",
                (nome.strip(), taxa_comissao, cor, plataforma_id),
            )
    except sqlite3.IntegrityError:
        raise ConflitoDeDados(f"Já existe uma plataforma chamada '{nome}'.")
    return buscar(plataforma_id)


def remover(plataforma_id: int) -> None:
    buscar(plataforma_id)
    with conectar() as conexao:
        em_uso = conexao.execute(
            "SELECT COUNT(*) FROM reserva WHERE plataforma_id = ?", (plataforma_id,)
        ).fetchone()[0]
        if em_uso:
            raise ConflitoDeDados(
                f"A plataforma tem {em_uso} reserva(s) vinculada(s) e não pode ser excluída."
            )
        conexao.execute("DELETE FROM plataforma WHERE id = ?", (plataforma_id,))

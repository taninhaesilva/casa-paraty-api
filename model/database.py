"""
Camada de acesso ao banco de dados (SQLite).

Aqui ficam:
  - o caminho do arquivo do banco;
  - a criação das tabelas (se ainda não existirem);
  - as plataformas cadastradas por padrão na primeira execução;
  - a função `conectar()`, usada por todos os outros módulos.

Cada operação abre uma conexão, executa e fecha. Assim a API não guarda
estado entre uma requisição e outra (restrição "stateless" de Roy Fielding).
"""
import os
import sqlite3
from contextlib import contextmanager

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_PADRAO = os.path.join(PASTA_PROJETO, "database", "casa_paraty.sqlite3")


def caminho_banco() -> str:
    """Permite trocar o arquivo do banco pela variável de ambiente CASA_PARATY_DB."""
    return os.environ.get("CASA_PARATY_DB", CAMINHO_PADRAO)


SCRIPT_CRIACAO = """
CREATE TABLE IF NOT EXISTS plataforma (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT    NOT NULL UNIQUE,
    taxa_comissao  REAL    NOT NULL DEFAULT 0
                   CHECK (taxa_comissao >= 0 AND taxa_comissao <= 100),
    cor            TEXT    NOT NULL DEFAULT '#6c757d'
);

CREATE TABLE IF NOT EXISTS reserva (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    hospede        TEXT    NOT NULL,
    plataforma_id  INTEGER NOT NULL REFERENCES plataforma(id),
    check_in       TEXT    NOT NULL,   -- data no formato AAAA-MM-DD
    check_out      TEXT    NOT NULL,   -- data no formato AAAA-MM-DD
    num_hospedes   INTEGER NOT NULL DEFAULT 1,
    valor_bruto    REAL    NOT NULL CHECK (valor_bruto > 0),
    taxa_aplicada  REAL    NOT NULL,   -- comissão (%) vigente quando a reserva foi feita
    status         TEXT    NOT NULL DEFAULT 'confirmada'
                   CHECK (status IN ('confirmada', 'cancelada')),
    observacao     TEXT,
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    CHECK (check_out > check_in)
);

CREATE INDEX IF NOT EXISTS idx_reserva_datas ON reserva (check_in, check_out);

CREATE TABLE IF NOT EXISTS despesa (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    data        TEXT    NOT NULL,      -- data no formato AAAA-MM-DD
    categoria   TEXT    NOT NULL,
    descricao   TEXT    NOT NULL,
    valor       REAL    NOT NULL CHECK (valor > 0),
    reserva_id  INTEGER REFERENCES reserva(id) ON DELETE SET NULL,
    criado_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_despesa_data ON despesa (data);
"""

# Taxas de exemplo: ajuste pela rota PUT /plataforma conforme o seu contrato.
PLATAFORMAS_PADRAO = [
    ("Airbnb", 15.0, "#FF5A5F"),
    ("Booking", 15.0, "#003580"),
    ("Direto", 0.0, "#2E8B57"),
]


@contextmanager
def conectar():
    """Abre uma conexão, confirma (commit) no final ou desfaz (rollback) se der erro."""
    conexao = sqlite3.connect(caminho_banco())
    conexao.row_factory = sqlite3.Row          # permite acessar colunas pelo nome
    conexao.execute("PRAGMA foreign_keys = ON")  # liga a checagem de chaves estrangeiras
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def inicializar_banco():
    """Cria a pasta e as tabelas, e cadastra as plataformas padrão se o banco estiver vazio."""
    os.makedirs(os.path.dirname(caminho_banco()), exist_ok=True)
    with conectar() as conexao:
        conexao.executescript(SCRIPT_CRIACAO)
        total = conexao.execute("SELECT COUNT(*) FROM plataforma").fetchone()[0]
        if total == 0:
            conexao.executemany(
                "INSERT INTO plataforma (nome, taxa_comissao, cor) VALUES (?, ?, ?)",
                PLATAFORMAS_PADRAO,
            )

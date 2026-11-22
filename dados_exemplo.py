"""
Popula o banco com reservas e despesas de exemplo (útil para testar e gravar o vídeo).

Uso:  python dados_exemplo.py
Atenção: apaga as reservas e despesas que já existirem no banco.
"""
from datetime import date

from model import conectar, inicializar_banco
from model import despesa, reserva


def popular():
    inicializar_banco()
    with conectar() as conexao:
        conexao.execute("DELETE FROM despesa")
        conexao.execute("DELETE FROM reserva")
        ids = {l["nome"]: l["id"] for l in conexao.execute("SELECT id, nome FROM plataforma")}

    reservas = [
        ("Mariana Souza", "Airbnb", date(2027, 1, 2), date(2027, 1, 6), 4, 3200.0),
        ("John Miller", "Booking", date(2027, 1, 8), date(2027, 1, 15), 2, 5250.0),
        ("Família Rezende", "Direto", date(2027, 1, 15), date(2027, 1, 20), 6, 4500.0),
        ("Camila Ortiz", "Airbnb", date(2027, 1, 29), date(2027, 2, 3), 3, 4000.0),
        ("Pedro Lima", "Direto", date(2027, 2, 12), date(2027, 2, 17), 5, 5000.0),
    ]
    criadas = []
    for hospede, plataforma, entrada, saida, pessoas, valor in reservas:
        criadas.append(reserva.criar({
            "hospede": hospede, "plataforma_id": ids[plataforma],
            "check_in": entrada, "check_out": saida, "num_hospedes": pessoas,
            "valor_bruto": valor, "status": "confirmada", "observacao": None,
        }))

    despesas = [
        (date(2027, 1, 6), "limpeza", "Faxina pós check-out", 180.0, criadas[0]["id"]),
        (date(2027, 1, 10), "manutencao", "Conserto da bomba da piscina", 650.0, None),
        (date(2027, 1, 15), "limpeza", "Faxina pós check-out", 180.0, criadas[1]["id"]),
        (date(2027, 1, 20), "contas", "Energia elétrica", 420.0, None),
        (date(2027, 1, 20), "contas", "Internet", 120.0, None),
        (date(2027, 1, 25), "impostos", "IPTU (parcela)", 310.0, None),
        (date(2027, 2, 5), "manutencao", "Pintura da varanda", 1800.0, None),
        (date(2027, 2, 20), "enxoval", "Jogo de toalhas novas", 390.0, None),
    ]
    for data, categoria, descricao, valor, reserva_id in despesas:
        despesa.criar({"data": data, "categoria": categoria, "descricao": descricao,
                       "valor": valor, "reserva_id": reserva_id})

    print(f"{len(reservas)} reservas e {len(despesas)} despesas cadastradas.")


if __name__ == "__main__":
    popular()

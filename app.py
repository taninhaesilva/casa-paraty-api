"""
Casa Paraty API: gestão de aluguel de temporada.

Este arquivo é a camada HTTP: recebe a requisição, valida os dados
(com os schemas do Pydantic) e chama a camada de modelo (pasta model/),
que concentra as regras de negócio e o acesso ao SQLite.
"""
from flask import redirect
from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI, Tag

from model import ConflitoDeDados, RegistroNaoEncontrado, inicializar_banco
from model import despesa as despesa_model
from model import plataforma as plataforma_model
from model import reserva as reserva_model
from model import resumo as resumo_model
from schemas import *

info = Info(
    title="Casa Paraty API",
    version="1.0.0",
    description=(
        "API para gestão do aluguel de temporada de uma casa em Paraty: reservas de "
        "várias plataformas (Airbnb, Booking, direto), despesas de manutenção e "
        "resumo financeiro de lucro ou prejuízo."
    ),
)
app = OpenAPI(__name__, info=info)
CORS(app)  # libera o front-end (aberto direto do arquivo index.html) para chamar a API

inicializar_banco()

tag_doc = Tag(name="Documentação", description="Redireciona para a documentação Swagger.")
tag_plataforma = Tag(name="Plataforma", description="Canais de reserva e suas comissões.")
tag_reserva = Tag(name="Reserva", description="Cadastro de reservas, com bloqueio de datas sobrepostas.")
tag_despesa = Tag(name="Despesa", description="Gastos da casa: manutenção, limpeza, contas etc.")
tag_resumo = Tag(name="Resumo", description="Resultado financeiro do mês ou do ano.")


# ---------- Tratamento central de erros de negócio ----------

@app.errorhandler(RegistroNaoEncontrado)
def tratar_nao_encontrado(erro):
    return {"mensagem": str(erro)}, 404


@app.errorhandler(ConflitoDeDados)
def tratar_conflito(erro):
    return {"mensagem": str(erro)}, 409


# ---------- Documentação ----------

@app.get("/", tags=[tag_doc])
def home():
    """Redireciona para /openapi, onde está a documentação (escolha Swagger)."""
    return redirect("/openapi")


# ---------- Plataformas ----------

@app.get("/plataformas", tags=[tag_plataforma],
         responses={"200": ListagemPlataformasSchema})
def listar_plataformas():
    """Lista as plataformas de reserva cadastradas.

    Na primeira execução a API já cadastra Airbnb, Booking e Direto.
    """
    return {"plataformas": plataforma_model.listar()}, 200


@app.post("/plataforma", tags=[tag_plataforma],
          responses={"201": PlataformaViewSchema, "409": ErroSchema})
def cadastrar_plataforma(body: PlataformaSchema):
    """Cadastra uma nova plataforma de reserva.

    Retorna 409 se já existir uma plataforma com o mesmo nome.
    """
    return plataforma_model.criar(**body.model_dump()), 201


@app.put("/plataforma", tags=[tag_plataforma],
         responses={"200": PlataformaViewSchema, "404": ErroSchema, "409": ErroSchema})
def atualizar_plataforma(query: PlataformaBuscaSchema, body: PlataformaSchema):
    """Altera nome, comissão ou cor de uma plataforma.

    A nova comissão vale para reservas cadastradas daqui em diante;
    as reservas antigas mantêm a taxa que estava valendo na época.
    """
    return plataforma_model.atualizar(query.id, **body.model_dump()), 200


@app.delete("/plataforma", tags=[tag_plataforma],
            responses={"200": MensagemSchema, "404": ErroSchema, "409": ErroSchema})
def remover_plataforma(query: PlataformaBuscaSchema):
    """Exclui uma plataforma.

    Retorna 409 se houver reservas vinculadas a ela.
    """
    plataforma_model.remover(query.id)
    return {"mensagem": "Plataforma removida com sucesso.", "id": query.id}, 200


# ---------- Reservas ----------

@app.get("/reservas", tags=[tag_reserva],
         responses={"200": ListagemReservasSchema})
def listar_reservas(query: ReservaFiltroSchema):
    """Lista as reservas, ordenadas pela data de check-in.

    Filtros opcionais: ano e mês (estadias que tocam o período), plataforma e status.
    """
    reservas = reserva_model.listar(query.ano, query.mes, query.plataforma_id, query.status)
    return {"reservas": reservas}, 200


@app.get("/reserva", tags=[tag_reserva],
         responses={"200": ReservaViewSchema, "404": ErroSchema})
def buscar_reserva(query: ReservaBuscaSchema):
    """Busca uma reserva pelo id, com noites, comissão e valor líquido calculados."""
    return reserva_model.buscar(query.id), 200


@app.post("/reserva", tags=[tag_reserva],
          responses={"201": ReservaViewSchema, "404": ErroSchema, "409": ErroSchema})
def cadastrar_reserva(body: ReservaSchema):
    """Cadastra uma reserva.

    Regras: o check-out precisa ser depois do check-in, e uma reserva confirmada
    não pode se sobrepor a outra (retorna 409). O dia do check-out pode ser o
    check-in do próximo hóspede. A comissão da plataforma é gravada na reserva.
    """
    return reserva_model.criar(body.model_dump()), 201


@app.put("/reserva", tags=[tag_reserva],
         responses={"200": ReservaViewSchema, "404": ErroSchema, "409": ErroSchema})
def atualizar_reserva(query: ReservaBuscaSchema, body: ReservaSchema):
    """Altera uma reserva existente, inclusive para cancelá-la (status = cancelada).

    Reservas canceladas liberam as datas e saem do resumo financeiro.
    """
    return reserva_model.atualizar(query.id, body.model_dump()), 200


@app.delete("/reserva", tags=[tag_reserva],
            responses={"200": MensagemSchema, "404": ErroSchema})
def remover_reserva(query: ReservaBuscaSchema):
    """Exclui uma reserva. Despesas ligadas a ela continuam cadastradas, sem o vínculo."""
    reserva_model.remover(query.id)
    return {"mensagem": "Reserva removida com sucesso.", "id": query.id}, 200


# ---------- Despesas ----------

@app.get("/despesas", tags=[tag_despesa],
         responses={"200": ListagemDespesasSchema})
def listar_despesas(query: DespesaFiltroSchema):
    """Lista as despesas, das mais recentes para as mais antigas.

    Filtros opcionais: ano, mês e categoria.
    """
    despesas = despesa_model.listar(query.ano, query.mes, query.categoria)
    return {"despesas": despesas}, 200


@app.post("/despesa", tags=[tag_despesa],
          responses={"201": DespesaViewSchema, "404": ErroSchema})
def cadastrar_despesa(body: DespesaSchema):
    """Cadastra uma despesa da casa.

    Pode ser ligada a uma reserva (por exemplo, a faxina depois de uma estadia).
    Retorna 404 se a reserva informada não existir.
    """
    return despesa_model.criar(body.model_dump()), 201


@app.put("/despesa", tags=[tag_despesa],
         responses={"200": DespesaViewSchema, "404": ErroSchema})
def atualizar_despesa(query: DespesaBuscaSchema, body: DespesaSchema):
    """Altera uma despesa existente."""
    return despesa_model.atualizar(query.id, body.model_dump()), 200


@app.delete("/despesa", tags=[tag_despesa],
            responses={"200": MensagemSchema, "404": ErroSchema})
def remover_despesa(query: DespesaBuscaSchema):
    """Exclui uma despesa."""
    despesa_model.remover(query.id)
    return {"mensagem": "Despesa removida com sucesso.", "id": query.id}, 200


# ---------- Resumo financeiro ----------

@app.get("/resumo", tags=[tag_resumo],
         responses={"200": ResumoViewSchema})
def resumo_financeiro(query: ResumoBuscaSchema):
    """Mostra se a casa deu lucro ou prejuízo no mês (ou no ano, se o mês não for informado).

    Resultado = receita bruta - comissões das plataformas - despesas.
    A receita de estadias que atravessam a virada do mês é dividida pelas noites.
    Também traz taxa de ocupação, receita por plataforma e despesas por categoria.
    """
    return resumo_model.calcular(query.ano, query.mes), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)

# Casa Paraty API

API para a **gestão do aluguel de temporada** de uma casa em Paraty (RJ).

A casa é anunciada em várias plataformas (Airbnb, Booking) e também é alugada diretamente. A API centraliza:

- **Reservas** de todas as origens, com **bloqueio automático de datas sobrepostas**;
- **Despesas** da casa (manutenção, limpeza, contas, impostos, condomínio, enxoval);
- **Resumo financeiro** do mês ou do ano, que mostra se a casa deu **lucro ou prejuízo**, descontando as comissões de cada plataforma.

> MVP da Sprint 1 (Desenvolvimento Full Stack Básico) da pós-graduação em Engenharia de Software da PUC-Rio.

---

## Tecnologias

- Python 3.10 ou superior
- [Flask](https://flask.palletsprojects.com/) e [flask-openapi3](https://luolingchun.github.io/flask-openapi3/) (documentação Swagger)
- [Pydantic](https://docs.pydantic.dev/) (validação dos dados)
- SQLite (módulo `sqlite3`, que já vem com o Python)
- flask-cors (permite que o front-end, aberto direto pelo `index.html`, chame a API)

## Arquitetura em camadas

```
casa-paraty-api/
├── app.py              # Camada HTTP: rotas e documentação
├── schemas/            # Formato dos dados de entrada e saída (Pydantic)
├── model/              # Regras de negócio e acesso ao banco (SQL)
│   ├── database.py     # Conexão e criação das tabelas
│   ├── plataforma.py
│   ├── reserva.py      # Inclui a verificação de conflito de datas
│   ├── despesa.py
│   ├── resumo.py       # Cálculo de lucro/prejuízo e ocupação
│   └── periodo.py      # Funções de datas (mês/ano, noites no período)
├── database/           # O arquivo .sqlite3 é criado aqui automaticamente
├── dados_exemplo.py    # Script que popula o banco com dados de teste
└── requirements.txt
```

## Modelo de dados

| Tabela | Descrição | Relacionamento |
|---|---|---|
| `plataforma` | Canal de reserva e sua comissão (%) | 1 plataforma → N reservas |
| `reserva` | Hóspede, datas, valor, status; guarda a comissão vigente na data | N reservas → 1 plataforma |
| `despesa` | Gastos da casa por categoria | Opcionalmente ligada a 1 reserva |

---

## Instalação

> Recomenda-se usar um ambiente virtual para isolar as dependências.

1. **Clone o repositório** e entre na pasta:
   ```bash
   git clone https://github.com/taninhaesilva/casa-paraty-api.git
   cd casa-paraty-api
   ```

2. **Crie e ative o ambiente virtual:**

   - Windows (PowerShell):
     ```bash
     python -m venv env
     .\env\Scripts\Activate.ps1
     ```
   - macOS / Linux:
     ```bash
     python3 -m venv env
     source env/bin/activate
     ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. *(Opcional)* **Popule o banco com dados de exemplo:**
   ```bash
   python dados_exemplo.py
   ```

## Execução

```bash
flask run --host 0.0.0.0 --port 5000
```

Ou, para recarregar automaticamente ao editar o código:

```bash
flask run --host 0.0.0.0 --port 5000 --reload
```

Depois, abra **http://localhost:5000** no navegador. Você será levado à página `/openapi`; escolha **Swagger** para ver e testar todas as rotas.

O banco `database/casa_paraty.sqlite3` é criado na primeira execução, já com as plataformas **Airbnb**, **Booking** e **Direto**. As comissões padrão são exemplos e podem ser ajustadas pela rota `PUT /plataforma`.

---

## Rotas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/plataformas` | Lista as plataformas |
| POST | `/plataforma` | Cadastra uma plataforma |
| PUT | `/plataforma?id=` | Altera uma plataforma |
| DELETE | `/plataforma?id=` | Exclui (bloqueado se houver reservas) |
| GET | `/reservas` | Lista reservas (filtros: `ano`, `mes`, `plataforma_id`, `status`) |
| GET | `/reserva?id=` | Busca uma reserva |
| POST | `/reserva` | Cadastra uma reserva |
| PUT | `/reserva?id=` | Altera ou cancela uma reserva |
| DELETE | `/reserva?id=` | Exclui uma reserva |
| GET | `/despesas` | Lista despesas (filtros: `ano`, `mes`, `categoria`) |
| POST | `/despesa` | Cadastra uma despesa |
| PUT | `/despesa?id=` | Altera uma despesa |
| DELETE | `/despesa?id=` | Exclui uma despesa |
| GET | `/resumo?ano=&mes=` | Lucro ou prejuízo, ocupação, receita por plataforma e despesas por categoria |

### Códigos de status

| Código | Quando acontece |
|---|---|
| 200 | Consulta, alteração ou exclusão bem-sucedida |
| 201 | Registro criado |
| 404 | Registro não encontrado |
| 409 | Conflito: datas sobrepostas, nome repetido ou exclusão bloqueada |
| 422 | Dados inválidos (ex.: check-out antes do check-in, categoria inexistente) |

## Regras de negócio

- **Conflito de datas:** uma reserva confirmada não pode se sobrepor a outra. O dia do check-out pode ser o check-in do próximo hóspede. Reservas canceladas liberam as datas.
- **Comissão histórica:** cada reserva grava a comissão vigente quando foi criada. Mudar a taxa de uma plataforma não altera o passado.
- **Rateio por noite:** uma estadia que atravessa a virada do mês tem a receita dividida pelas noites. Ex.: de 29/01 a 03/02 são 5 noites, 3 em janeiro e 2 em fevereiro.
- **Resultado:** `receita bruta − comissões − despesas`.

## Próximos passos

- Importar reservas automaticamente pelos calendários iCal do Airbnb e do Booking.
- Calendário visual de ocupação.
- Autenticação de usuários.

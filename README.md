# Market Hub

Marketplace, construido com Python e FastAPI seguindo uma
abordagem API First.

O foco principal da aplicacao e a jornada do Vendedor. A P3 materializa essa
jornada na API: o Seller lista, detalha, avanca e cancela os proprios Order
Items.

## Escopo atual (P3)

A v0 implementou o **Catalogo**. A P2 adicionou **Order**, JWT e estoque
atomico. A P3, especificada em [`docs/P3_Seller_Journey.md`](docs/P3_Seller_Journey.md),
expõe a operacao do Seller sobre Order Items (paginacao, filtros, detalhe,
isolamento 404 e idempotencia). Sem frontend, Communication ou dashboard.

O estado atual do codigo esta em [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md).

## Dominio

```text
   Produto ──1:N──▶ Oferta ◀──N:1── Vendedor
                         │
                         ▼
                      Order Item ◀──N:1── Order ◀── Buyer (User)
```

- **Oferta** concentra preco, estoque e disponibilidade atuais.
- **Order** agrupa itens de um Buyer; um pedido pode ter itens de varios Sellers.
- **Order Item** congela `purchase_price`, guarda `quantity` e o `status`.
- Escritas de Offer e Order Item usam o Seller do JWT. Checkout usa o Buyer do JWT.
- Users de seed tem `name` (Loja A, Loja B, Buyer Demo).

## Requisitos

- Python 3.12 ou superior
- [uv](https://docs.astral.sh/uv/)
- Docker, para o Postgres local

## Como executar

```bash
cp .env.example .env   # preencha Postgres, JWT_SECRET e SEED_PASSWORD
make install
make db-up             # sobe o Postgres, espera ficar saudavel e cria o banco de teste
make migrate           # aplica as migrations
make seed              # cria Loja A, Loja B e um buyer de demonstracao
make run
```

A API sobe em `http://localhost:8000` e as rotas ficam sob o prefixo `/v1`.
`make db-down` derruba o banco.

Login: `POST /v1/auth/login` com o email de seed (`loja-a@example.com`,
`loja-b@example.com`, `buyer@example.com`) e a senha de `SEED_PASSWORD`.

## Persistencia

PostgreSQL com SQLAlchemy e migrations via Alembic. O banco local vem do
`docker-compose.yml` e as credenciais saem de variaveis de ambiente — nao ha
valor de credencial no repositorio.

Para criar uma migration depois de alterar os modelos:

```bash
make revision m="create catalog tables"
make migrate
```

## Como executar os testes

Os testes usam o mesmo Postgres do `docker-compose`, no banco indicado por
`TEST_DATABASE_URL`. Preencha essa variavel no `.env` e suba o banco antes de
testar.

```bash
make db-up         # sobe o Postgres e cria o banco de teste
make test          # suíte completa
make lint          # ruff (lint e formatacao)
```

## Documentacao da API

- Documentacao interativa gerada pelo FastAPI: `http://localhost:8000/docs`
- Contrato OpenAPI escrito a mao: [`api/openapi.yaml`](api/openapi.yaml)

O contrato em `api/openapi.yaml` e a fonte da verdade e e escrito **antes** da
implementacao. O fluxo de qualquer mudanca na API e:

1. editar `api/openapi.yaml` e revisar o contrato;
2. implementar as rotas e os schemas em `app/`;
3. rodar `make test` — `tests/integration/test_openapi_contract.py` falha se a
   implementacao divergir do contrato.

## Organizacao do codigo

| Caminho | Responsabilidade |
| --- | --- |
| `api/openapi.yaml` | contrato da API, fonte da verdade |
| `app/main.py` | montagem da aplicacao FastAPI |
| `app/core/` | configuracao, erros de negocio e eventos in-memory |
| `app/database.py` | engine, sessao e publicacao de eventos apos commit |
| `app/health.py` | health check |
| `app/auth/` | login, JWT e seed de users |
| `app/catalog/` | rotas, schemas, modelos e seed do Catalogo |
| `app/orders/` | checkout, listagem operacional do Seller, status, cancelamento |
| `migrations/` | migrations do Alembic |
| `tests/` | testes de unidade e de integracao |

O codigo e organizado por dominio: cada dominio novo entra como um modulo
proprio em `app/`, com suas rotas, schemas e regras.

## Configuracao

Toda a configuracao vem de variaveis de ambiente, descritas em `.env.example`.
O arquivo `.env` nunca e commitado, nem qualquer valor de credencial.

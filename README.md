# Market Hub

Marketplace, construido com Python e FastAPI seguindo uma
abordagem API First.
#repositorio: https://github.com/giordani-p/market-hub 


O foco principal da aplicacao e a jornada do Vendedor. A P3 materializa essa
jornada na API: o Seller lista, detalha, avanca e cancela os proprios Order
Items. A P4 adiciona Communication entre Buyer e Seller por Order Item.
A P5.1 adiciona o papel Ops e InternalComment operacional.
A P5.2 adiciona prioridade na Conversation e a fila Ops.
A P5.3, especificada em [`docs/P5.3_Closure_Verification.md`](docs/P5.3_Closure_Verification.md),
fecha e verifica a P5. A P6.1, especificada em
[`docs/P6.1_Foundation_Worker.md`](docs/P6.1_Foundation_Worker.md), adiciona Jobs em
background e o recalculo periodico de prioridade. A P6.2, especificada em
[`docs/P6.2_Notification.md`](docs/P6.2_Notification.md), adiciona Notifications
in-app sobre essa fundacao. A P7, especificada em
[`docs/P7_Dashboard.md`](docs/P7_Dashboard.md), adiciona
`GET /v1/dashboard` como visao de leitura por papel.

## Escopo atual (P7)

A v0 implementou o **Catalogo**. A P2 adicionou **Order**, JWT e estoque
atomico. A P3, especificada em [`docs/P3_Seller_Journey.md`](docs/P3_Seller_Journey.md),
expoe a operacao do Seller sobre Order Items. A P4, especificada em
[`docs/P4_Communication.md`](docs/P4_Communication.md), adiciona Conversation e
Messages. A P5.1, especificada em [`docs/P5.1_Support_Ops.md`](docs/P5.1_Support_Ops.md),
adiciona Ops em `/v1/ops` e InternalComment. A P5.2, especificada em
[`docs/P5.2_Priority_Policy.md`](docs/P5.2_Priority_Policy.md), calcula prioridade
e expoe a fila de Conversations OPEN. A P5.3 confirma o fechamento da P5.
A P6.1 adiciona Worker SQS, EventBridge Rule local e reconcilacao periodica
de prioridade. A P6.2 adiciona Notifications in-app (status para Buyer+Seller,
prioridade efetiva para Seller+Ops). A P7 adiciona `GET /v1/dashboard` para
Buyer, Seller e Ops, sem persistencia propria. Sem realtime.

O estado atual do codigo esta em [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md).

## Dominio

```text
   Produto ──1:N──▶ Oferta ◀──N:1── Vendedor
                         │
                         ▼
                      Order Item ◀──N:1── Order ◀── Buyer (User)
                           │
                           ▼
                     Conversation ──1:N──▶ Message
                           │
                           ▼
                     InternalComment (Seller e Ops)
```

- **Oferta** concentra preco, estoque e disponibilidade atuais.
- **Order** agrupa itens de um Buyer; um pedido pode ter itens de varios Sellers.
- **Order Item** congela `purchase_price`, guarda `quantity` e o `status`.
- **Conversation** liga Buyer e Seller a um Order Item (no maximo uma `open`)
  e guarda `calculated_priority` / `ops_override`.
- **InternalComment** liga Seller e Ops ao mesmo Order Item, sem Conversation.
- Escritas de Offer e Order Item usam o Seller do JWT. Checkout usa o Buyer do JWT.
  Ops nao herda essas escritas; opera em `/v1/ops`.
- `make seed` popula um marketplace de demonstracao (20 users, catalogo, pedidos
  e jornadas). Os testes usam so a identidade minima (Loja A, Loja B, Buyer Demo,
  Ops Demo).

## Requisitos

- Python 3.12 ou superior
- [uv](https://docs.astral.sh/uv/)
- Docker, para o Postgres local, o LocalStack e o Worker

## Como executar

```bash
cp .env.example .env   # preencha Postgres, JWT_SECRET e SEED_PASSWORD
make install
make reset             # recria o volume do Postgres, aplica migrations e a seed completa
make run
```

`make reset` executa `docker compose down -v`, sobe o Postgres, `make migrate` e
`make seed`. Apaga **todos** os dados locais do Postgres (app e banco de teste).
`make db-down` so derruba os containers e **nao** apaga o volume.

Ambiente que ja tem o banco: `make migrate` e `make seed` (a seed e idempotente).
Passo a passo equivalente ao reset: `make db-up`, `make migrate`, `make seed`.

A API sobe em `http://localhost:8000` e as rotas ficam sob o prefixo `/v1`.

Para o Worker e a reconcilacao periodica (LocalStack + SQS):

```bash
make jobs-up           # sobe Postgres, LocalStack e o Worker
make enqueue-reconcile # publica RECONCILE_PRIORITIES na hora, sem esperar 15 min
```

`make jobs-up` **nao** entra no `reset`: rode depois se quiser LocalStack e Worker
(as filas sao recriadas; o Worker ja ve o banco populado).

O e-mail de alerta (prioridade `high`/`critical`) e simulado no log do
Worker, nao na API (`docker compose logs -f worker`). Destinatario extra
opcional: `NOTIFICATION_EMAIL_EXTRA_TO` no `.env`; reinicie o Worker depois
de mudar.

A Rule do EventBridge dispara a cada 15 minutos. Para conferir a DLQ, publique
uma mensagem invalida na fila e receba-a ate `JOBS_MAX_RECEIVE_COUNT` (3).
`make test` nao sobe LocalStack.

Login canonico: `POST /v1/auth/login` com `loja-a@example.com`,
`loja-b@example.com`, `buyer@example.com` ou `ops@example.com` e a senha de
`SEED_PASSWORD`. A seed completa cria outros users `*@example.com` (sellers e
buyers extras) com a mesma senha. Loja A, Buyer Demo e Ops Demo ja entram com
pedidos, conversas e notificacoes para percorrer as jornadas.

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
| `app/catalog/` | rotas, schemas, modelos, seed de identidade e catalogo demo |
| `app/orders/` | checkout, listagem operacional do Seller, status, cancelamento e seed de pedidos |
| `app/communication/` | Conversation, Messages, encerramento por inatividade, prioridade e reconcilacao |
| `app/support/` | listagem Ops, InternalComment, fila e override critical |
| `app/jobs/` | fundacao de Jobs, Worker SQS e enqueue |
| `infra/local/` | provisionamento LocalStack |
| `migrations/` | migrations do Alembic |
| `tests/` | testes de unidade e de integracao |

O codigo e organizado por dominio: cada dominio novo entra como um modulo
proprio em `app/`, com suas rotas, schemas e regras.

## Configuracao

Toda a configuracao vem de variaveis de ambiente, descritas em `.env.example`.
O arquivo `.env` nunca e commitado, nem qualquer valor de credencial.

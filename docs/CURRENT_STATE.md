# Estado atual do projeto

- **Versao**: 0.7.0
- **Fase**: P6.1 — COMPLETE (Jobs + reconcilacao automatica de prioridade)
- **Commit de referencia**: 360017c

## Do que se trata

Backend de um Marketplace em Python com FastAPI. A fase P1 cobre o dominio de
Catalogo (`docs/p1_catalog.md`). A fase P2, especificada em `docs/p2_order.md`,
cobre pedidos, estoque na efetivacao e autenticacao minima. A fase P3,
especificada em `docs/P3_Seller_Journey.md`, materializa a operacao do Seller
sobre os proprios Order Items. A fase P4, especificada em
`docs/P4_Communication.md`, adiciona Conversation e Messages contextualizadas
pelo Order Item. A fase P5.1, especificada em `docs/P5.1_Support_Ops.md`,
adiciona o papel Ops e InternalComment. A fase P5.2, especificada em
`docs/P5.2_Priority_Policy.md`, adiciona prioridade na Conversation e a fila
Ops. A fase P5.3, especificada em `docs/P5.3_Closure_Verification.md`, fecha e
verifica a P5 sem novas capacidades de produto. O resultado do fechamento esta
em `docs/P5.3_Resultado.md`. A fase P6.1, especificada em
`docs/P6.1_Notification.md`, adiciona a fundacao de Jobs (SQS + Worker) e o
recalculo periodico de prioridade. O plano da fase nao deve ser
copiado para ca: este documento descreve o que **existe hoje**.

## Arquitetura

Aplicacao FastAPI unica, organizada por dominio e nao por camada tecnica. Nao
ha Clean Architecture nem Hexagonal. Cada dominio entra como um modulo proprio
em `app/`.

`app/core/` guarda o que e transversal: configuracao, erros de negocio, eventos
em memoria e traducao para HTTP. `app/jobs/` e infra transversal de Jobs, nao
um dominio de produto.

Eventos de dominio (`OrderCreated`, `OrderItemStatusChanged`,
`OrderItemCancelled`, `ConversationCreated`, `MessageCreated`,
`ConversationClosed`, `InternalCommentCreated`) sao acumulados na transacao e
publicados no `InMemoryEventPublisher` somente apos o `commit` da sessao. Nao
ha bus, Outbox, Kafka nem Redis.

Jobs de background usam SQS no LocalStack. Uma EventBridge Rule
(`rate(15 minutes)`) publica `RECONCILE_PRIORITIES` na fila `market-hub-jobs`.
Um Worker em processo separado consome um Job por vez. Falhas nao deletam a
mensagem; apos `maxReceiveCount` (3) ela vai para `market-hub-jobs-dlq`. O
EventBridge Scheduler do LocalStack e mock e nao dispara fila; no AWS real o
mapeamento continua Scheduler → SQS. Recalculo por evento de dominio nao existe:
a fila Ops pode ficar ate cerca de 15 minutos defasada.

## Mapa do codigo

| Caminho              | O que contem                                                                                 |
| -------------------- | -------------------------------------------------------------------------------------------- |
| `app/main.py`        | `create_app()`, handlers de erro e routers com prefixo de versao                             |
| `app/core/config.py` | `Settings` e `get_settings()` com cache                                                      |
| `app/core/errors.py` | `DomainError` e subclasses, inclusive `CheckoutRejectedError`                                |
| `app/core/events.py` | dataclasses de evento e `InMemoryEventPublisher`                                             |
| `app/database.py`    | `Base`, engine, `session_transaction()` (commit + publish)                                   |
| `app/health.py`      | router e schema do health check                                                              |
| `app/auth/`          | `User` (com `name` e `role` buyer/seller/ops), login, `/me`, JWT, seed                       |
| `app/catalog/`       | modelos, schemas, CRUD de Produto/Oferta e seed de sellers                                   |
| `app/orders/`        | checkout, listagem/detalhe do Seller, status e cancelamento                                  |
| `app/communication/` | Conversation, Messages, lazy close, batch de inatividade, PriorityPolicy e reconcilacao |
| `app/support/`       | listagem/detalhe Ops, InternalComment, fila e override critical                              |
| `app/jobs/`          | Job, registry, adapter SQS, Worker e enqueue                                                 |
| `api/openapi.yaml`   | contrato da API escrito a mao                                                                |
| `infra/local/`       | provisionamento LocalStack (filas, DLQ, EventBridge Rule)                                    |
| `migrations/`        | Alembic `001`–`007` (stale detection `007`)                                                  |
| `tests/unit/`        | testes sem aplicacao montada                                                                 |
| `tests/integration/` | testes via `TestClient` no Postgres de teste                                                 |

## Contratos de API

Rotas implementadas, todas sob o prefixo `/v1`:

| Rota                                                | Resposta                                                     |
| --------------------------------------------------- | ------------------------------------------------------------ |
| `GET /v1/health`                                    | `HealthResponse` (`status`, `version`)                       |
| `POST /v1/auth/login`                               | `TokenResponse`; `401 unauthorized` se a senha falhar        |
| `GET /v1/auth/me`                                   | `User` autenticado, inclusive `name`                         |
| `GET /v1/products`                                  | array de `Product`                                           |
| `POST /v1/products`                                 | `201` + `Product`                                            |
| `GET /v1/products/{product_id}`                     | `Product`                                                    |
| `PATCH /v1/products/{product_id}`                   | `Product`                                                    |
| `DELETE /v1/products/{product_id}`                  | `204`; `409` se o produto ainda tiver ofertas                |
| `GET /v1/offers`                                    | array de `Offer`; filtro opcional `?seller_id=` (publico)    |
| `POST /v1/offers`                                   | `201` + `Offer`; `seller_id` vem do JWT de seller            |
| `GET /v1/offers/{offer_id}`                         | `Offer`                                                      |
| `PATCH /v1/offers/{offer_id}`                       | `Offer` do seller autenticado                                |
| `DELETE /v1/offers/{offer_id}`                      | `204`; `409` se houver order items                           |
| `POST /v1/orders`                                   | checkout atomico; `201` + `Order` ou `409 checkout_rejected` |
| `GET /v1/orders`                                    | orders do buyer autenticado                                  |
| `GET /v1/orders/{order_id}`                         | `Order` do buyer autenticado                                 |
| `GET /v1/order-items`                               | envelope paginado dos items do seller autenticado            |
| `GET /v1/order-items/{item_id}`                     | detalhe do seller (`product`, `buyer`, `order`, `offer_id`)  |
| `PATCH /v1/order-items/{item_id}`                   | avanca status no fluxo; mesmo status e idempotente           |
| `POST /v1/order-items/{item_id}/cancel`             | cancela conforme o papel; cancel repetido e idempotente      |
| `POST /v1/order-items/{item_id}/internal-comments`  | `201` InternalComment do Seller no proprio item              |
| `GET /v1/order-items/{item_id}/internal-comments`   | array cronologico do Seller no proprio item                  |
| `POST /v1/order-items/{item_id}/conversation`       | `201` nova ou `200` OPEN reutilizada                         |
| `GET /v1/order-items/{item_id}/conversations`       | array por `last_interaction_at DESC`                         |
| `GET /v1/conversations/{conversation_id}`           | Conversation do participante                                 |
| `POST /v1/conversations/{conversation_id}/close`    | Seller fecha; ja `closed` responde `409`                     |
| `POST /v1/conversations/{conversation_id}/messages` | `201` Message em Conversation `open`                         |
| `GET /v1/conversations/{conversation_id}/messages`  | janela de 24h UTC (`from`, `to`, `has_older`)                |
| `GET /v1/ops/order-items`                           | envelope paginado de todos os items (Ops)                    |
| `GET /v1/ops/order-items/{item_id}`                 | detalhe Ops (`product`, `buyer`, `seller`, `order`)          |
| `POST /v1/ops/order-items/{item_id}/internal-comments` | `201` InternalComment do Ops                              |
| `GET /v1/ops/order-items/{item_id}/internal-comments`  | array cronologico (mesmo historico do Seller)             |
| `GET /v1/ops/order-items/{item_id}/conversations`  | historico open+closed do item, com prioridade                |
| `GET /v1/ops/conversations`                         | fila OPEN paginada por `effective_priority`                  |
| `GET /v1/ops/conversations/{conversation_id}`       | Conversation Ops com prioridade persistida                   |
| `POST /v1/ops/conversations/{conversation_id}/priority/refresh` | recalcula `calculated_priority`                     |
| `POST /v1/ops/conversations/{conversation_id}/critical` | override `critical` + InternalComment                    |
| `POST /v1/ops/conversations/{conversation_id}/critical/remove` | remove override                                     |

`GET /v1/order-items` aceita `page`, `page_size` (padrao 20, maximo 100),
`status`, `from`, `to` e `order_item_id`. Ordenacao `created_at DESC`. Lista
vazia responde `200` com `items`, `page`, `page_size` e `total`.
`GET /v1/ops/order-items` usa os mesmos parametros e acrescenta `seller_id`.
Cada item da listagem Ops inclui `seller` (`id`, `name` da tabela `sellers`).
`GET /v1/ops/conversations` lista so `open`, ordena `critical > high > medium > low`
e depois `last_interaction_at DESC`, e aceita `seller_id`, `order_item_id` e
`effective_priority`. Envelope `items`/`page`/`page_size`/`total`.

`GET /v1/conversations/{id}/messages` aceita `before` (date-time com timezone,
nao futuro). Sem `before`, retorna as Messages das ultimas 24h.

Erros de negocio respondem com `ErrorResponse` (`code`, `message`):
`resource_not_found` (404), `resource_in_use` e `invalid_transition` (409),
`unauthorized` (401), `forbidden` (403). Checkout invalido responde
`CheckoutRejected` (`code: checkout_rejected`, `items` com `reason`).

Seller em item de outro Seller recebe `404 resource_not_found`. Buyer nas
rotas de listagem/detalhe do Seller recebe `403`. Sem token, `401`. Participante
sem relacao com Conversation ou Order Item recebe `404`. Buyer em
`POST .../close` recebe `403`. Buyer e Seller em `/v1/ops/*` recebem `403`.
Ops nas rotas exclusivas de Seller/Buyer recebe `403`; em Conversation/Message
de participante, `404`. Ops le metadados de Conversation em `/v1/ops`, sem
Messages.

Nao existe `POST /v1/auth/register`. Usuarios existem so via seed.

O contrato `api/openapi.yaml` e a fonte da verdade e e escrito antes do codigo.
`tests/integration/test_openapi_contract.py` compara paths e metodos.

## Decisoes de contrato e de stack ja tomadas

- Atualizacao apenas por `PATCH`, com todos os campos opcionais. Nao ha `PUT`.
- Ofertas de um vendedor por filtro na listagem publica: `GET /v1/offers?seller_id=`.
- Preco como string decimal com duas casas (`"299.00"`), mapeado para `Decimal`
  e `NUMERIC(12,2)`.
- Listagens retornam array simples, sem envelope nem paginacao, **exceto**
  `GET /v1/order-items`, `GET /v1/ops/order-items`, `GET /v1/ops/conversations` e
  `GET /v1/conversations/{id}/messages`.
- Exclusao bem-sucedida responde `204` sem corpo.
- Validacao de campo fica com o Pydantic e responde `422`.
- `offers.product_id` e `offers.seller_id` usam `ON DELETE RESTRICT`. `order_items.offer_id`
  tambem. Excluir recurso ainda referenciado responde `409 resource_in_use`.
- Persistencia: PostgreSQL via docker-compose, SQLAlchemy e Alembic.
- Auth: JWT HS256, login com email e senha. Sem refresh token e sem cadastro
  publico. `seller_id` e `buyer_id` de escrita saem do JWT, nunca do body.
- Carrinho nao e persistido: o cliente reenvia os itens no checkout.
- `OrderItem.purchase_price` congela o preco; checkout compara `expected_price`.
- Status do item: `placed` → `preparing` → `in_transit` → `delivered`, mais `cancelled`.
- `PATCH` de Order Item nao aceita `cancelled` (422). Cancelamento e
  `POST .../cancel`.
- Estoque consumido com `UPDATE ... WHERE stock >= quantity`; cancelamento antes de
  `in_transit` recompõe estoque.
- Mutacoes de Order Item relêem o registro com `SELECT ... FOR UPDATE`.
- Users de seed: Loja A, Loja B, Buyer Demo e Ops Demo, com `name`. Senha em
  `SEED_PASSWORD`. `User.role` e `buyer`, `seller` ou `ops`.
- Conversation: uma `open` por Order Item (indice unico parcial). Status
  `open`/`closed`. Motivos: `atraso`, `troca`, `devolucao`, `reclamacao`,
  `suporte`, `elogio`, `outros`.
- Messages sao texto imutavel (maximo 2000). Autor `buyer`, `seller` ou `system`.
- Close manual e so do Seller e nao cria Message sistemica. Inatividade (120h)
  fecha com Message sistemica, via lazy no acesso ou `make close-inactive`.
- Ops opera so em `/v1/ops`. InternalComment e texto imutavel (maximo 2000)
  entre Seller e Ops, no Order Item, independente de Conversation. Autor
  `seller` ou `ops`.
- Conversation persiste `calculated_priority` (`low`/`medium`/`high`) na criacao
  e `ops_override` (`null`/`critical`). `effective_priority` e derivado.
  Recalculo HTTP e `POST .../priority/refresh`. A fila Ops lista Conversations
  `open` pelo snapshot persistido. Ops nao le Messages. GET nao recalcula.
- Conversation persiste `priority_calculated_at` (nullable). Order Item persiste
  `status_updated_at`. Nenhum dos dois aparece na API. OPEN e stale quando o
  calculo e nulo, a ultima interacao ou o status sao posteriores, ou o age
  bucket mudou. O Job `RECONCILE_PRIORITIES` pagina essas Conversations, reusa
  a PriorityPolicy V1, nao mexe em `ops_override` e e idempotente.
- `close_inactive` continua fora da fila SQS (`make close-inactive`).

## Configuracao

Lida de variaveis de ambiente, com `.env` local e `.env.example` como
referencia: `ENVIRONMENT`, `API_PREFIX`, `DATABASE_URL`, `TEST_DATABASE_URL`,
`JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `SEED_PASSWORD`,
`CONVERSATION_INACTIVITY_HOURS`, `AWS_ENDPOINT_URL`, `AWS_REGION`,
`JOBS_QUEUE_NAME`, `JOBS_DLQ_NAME`, `JOBS_VISIBILITY_TIMEOUT_SECONDS`,
`JOBS_MAX_RECEIVE_COUNT`, `JOBS_WAIT_TIME_SECONDS`, `RECONCILE_PAGE_SIZE`,
`JOBS_SCHEDULE_EXPRESSION`. `AWS_ENDPOINT_URL` local padrao e
`http://localhost:4566`; o cliente SQS usa keys dummy nesse endpoint para nao
herdar `~/.aws`. O `docker-compose.yml` consome
`POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_DB`. Credenciais dummy do
LocalStack tambem ficam no Compose do Worker. Nenhum valor de credencial real
existe no repositorio.

## Persistencia

PostgreSQL 16 em container local, SQLAlchemy 2.0 e Alembic. Tabelas `sellers`,
`products`, `offers`, `users` (com `name`), `orders`, `order_items`,
`conversations`, `messages` e `internal_comments`. `conversations` tem
`priority_calculated_at`; `order_items` tem `status_updated_at`. Testes usam
`TEST_DATABASE_URL`. `make test` exige o Postgres no ar e nao sobe LocalStack.

## Convencoes

- Gerenciador de pacotes `uv`; comandos no `Makefile`.
- Lint e formatacao com `ruff`, linha de 100 colunas.
- Testes com `pytest`, em `tests/unit/` e `tests/integration/`.
- Idioma conforme `.cursor/rules/language-conventions.mdc`.

## O que ainda nao existe

- Recalculo de prioridade no GET ou por evento de dominio (`MessageCreated`,
  `OrderItemStatusChanged`).
- Ops lendo Messages Buyer-Seller.
- Pipeline de CI e qualquer artefato de deploy.
- Cadastro publico de usuarios, refresh token e IdP.
- Carrinho persistido, pagamentos, entrega, frontend.
- Inbox global, dashboard/KPIs, WebSocket/SSE, notificacoes.
- Event bus, Outbox, Kafka, Redis ou observabilidade alem dos logs do Worker.
- Soft delete ou diferenciacao entre excluir e deixar de disponibilizar.

## Proxima etapa

P6.2 — Notifications sobre a fundacao de Jobs existente, sem redesenhar
PriorityPolicy nem Conversation. Sem frontend.

## Historico de versoes

- **0.7.0** — P6.1: Worker SQS, EventBridge Rule local, Job
  `RECONCILE_PRIORITIES` paginado e idempotente, stamps de stale detection.
- **0.6.0** — P5.3: fechamento e verificacao da P5 (matriz de testes Ops e
  prioridade, jornada integrada, rebuild das migrations 005/006). P5 completa.
- **0.6.0** — PriorityPolicy V1 na Conversation, fila Ops de Conversations OPEN,
  refresh manual, override `critical` com InternalComment.
- **0.5.0** — Support/Ops: papel `ops`, namespace `/v1/ops` com listagem global
  de Order Items, InternalComment imutavel compartilhado com o Seller, seed
  Ops Demo e evento pos-commit.
- **0.4.0** — Communication: Conversation por Order Item, Messages imutaveis,
  uma OPEN por item, close manual do Seller, encerramento por inatividade
  (lazy + batch) e eventos pos-commit.
- **0.3.0** — jornada do Seller: listagem paginada com filtros, detalhe do
  Order Item, `users.name`, isolamento 404, PATCH/cancel idempotentes e
  `SELECT FOR UPDATE` nas mutacoes.
- **0.2.0** — dominio de Order: checkout atomico, status e cancelamento no
  Order Item, consumo condicional de estoque, JWT sem register, seed de users,
  eventos in-memory apos commit.
- **0.1.0** — dominio de Catalogo implementado: CRUD de Produto e Oferta,
  persistencia com FKs `RESTRICT`, seed de vendedores, `409 resource_in_use`
  quando o produto ainda tem ofertas, e testes de comportamento no Postgres
  de teste.
- **0.1.0** — contrato do Catalogo especificado em `api/openapi.yaml` e
  infraestrutura de persistencia montada (PostgreSQL em docker-compose,
  SQLAlchemy e Alembic). Rotas ainda nao implementadas.
- **0.1.0** — base do backend FastAPI simplificada para o escopo da v0: pacote
  movido para `app/`, remocao das camadas `domain/`, `application/` e
  `infrastructure/`, do logging estruturado, da suite e2e e do exportador de
  OpenAPI. Mantidos o health check e o teste de contrato.

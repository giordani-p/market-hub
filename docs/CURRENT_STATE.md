# Estado atual do projeto

- **Versao**: 0.3.0
- **Fase**: P3 (concluida) — jornada operacional do Seller sobre Order Items
- **Commit de referencia**: c4f86b3

## Do que se trata

Backend de um Marketplace em Python com FastAPI. A fase P1 cobre o dominio de
Catalogo (`docs/p1_catalog.md`). A fase P2, especificada em `docs/p2_order.md`,
cobre pedidos, estoque na efetivacao e autenticacao minima. A fase P3,
especificada em `docs/P3_Seller_Journey.md`, materializa a operacao do Seller
sobre os proprios Order Items. O plano da fase nao deve ser copiado para ca:
este documento descreve o que **existe hoje**.

## Arquitetura

Aplicacao FastAPI unica, organizada por dominio e nao por camada tecnica. Nao
ha Clean Architecture nem Hexagonal. Cada dominio entra como um modulo proprio
em `app/`.

`app/core/` guarda o que e transversal: configuracao, erros de negocio, eventos
em memoria e traducao para HTTP.

Eventos de dominio (`OrderCreated`, `OrderItemStatusChanged`,
`OrderItemCancelled`) sao acumulados na transacao e publicados no
`InMemoryEventPublisher` somente apos o `commit` da sessao. Nao ha bus,
Outbox, Kafka nem Redis.

## Mapa do codigo

| Caminho | O que contem |
| --- | --- |
| `app/main.py` | `create_app()`, handlers de erro e routers com prefixo de versao |
| `app/core/config.py` | `Settings` e `get_settings()` com cache |
| `app/core/errors.py` | `DomainError` e subclasses, inclusive `CheckoutRejectedError` |
| `app/core/events.py` | dataclasses de evento e `InMemoryEventPublisher` |
| `app/database.py` | `Base`, engine, `session_transaction()` (commit + publish) |
| `app/health.py` | router e schema do health check |
| `app/auth/` | `User` (com `name`), login, `/me`, JWT, hash de senha e seed de users |
| `app/catalog/` | modelos, schemas, CRUD de Produto/Oferta e seed de sellers |
| `app/orders/` | checkout, listagem/detalhe do Seller, status e cancelamento |
| `api/openapi.yaml` | contrato da API escrito a mao |
| `migrations/` | Alembic: Catalogo (`001`), auth/orders (`002`) e `users.name` (`003`) |
| `tests/unit/` | testes sem aplicacao montada |
| `tests/integration/` | testes via `TestClient` no Postgres de teste |

## Contratos de API

Rotas implementadas, todas sob o prefixo `/v1`:

| Rota | Resposta |
| --- | --- |
| `GET /v1/health` | `HealthResponse` (`status`, `version`) |
| `POST /v1/auth/login` | `TokenResponse`; `401 unauthorized` se a senha falhar |
| `GET /v1/auth/me` | `User` autenticado, inclusive `name` |
| `GET /v1/products` | array de `Product` |
| `POST /v1/products` | `201` + `Product` |
| `GET /v1/products/{product_id}` | `Product` |
| `PATCH /v1/products/{product_id}` | `Product` |
| `DELETE /v1/products/{product_id}` | `204`; `409` se o produto ainda tiver ofertas |
| `GET /v1/offers` | array de `Offer`; filtro opcional `?seller_id=` (publico) |
| `POST /v1/offers` | `201` + `Offer`; `seller_id` vem do JWT de seller |
| `GET /v1/offers/{offer_id}` | `Offer` |
| `PATCH /v1/offers/{offer_id}` | `Offer` do seller autenticado |
| `DELETE /v1/offers/{offer_id}` | `204`; `409` se houver order items |
| `POST /v1/orders` | checkout atomico; `201` + `Order` ou `409 checkout_rejected` |
| `GET /v1/orders` | orders do buyer autenticado |
| `GET /v1/orders/{order_id}` | `Order` do buyer autenticado |
| `GET /v1/order-items` | envelope paginado dos items do seller autenticado |
| `GET /v1/order-items/{item_id}` | detalhe do seller (`product`, `buyer`, `order`, `offer_id`) |
| `PATCH /v1/order-items/{item_id}` | avanca status no fluxo; mesmo status e idempotente |
| `POST /v1/order-items/{item_id}/cancel` | cancela conforme o papel; cancel repetido e idempotente |

`GET /v1/order-items` aceita `page`, `page_size` (padrao 20, maximo 100),
`status`, `from`, `to` e `order_item_id`. Ordenacao `created_at DESC`. Lista
vazia responde `200` com `items`, `page`, `page_size` e `total`.

Erros de negocio respondem com `ErrorResponse` (`code`, `message`):
`resource_not_found` (404), `resource_in_use` e `invalid_transition` (409),
`unauthorized` (401), `forbidden` (403). Checkout invalido responde
`CheckoutRejected` (`code: checkout_rejected`, `items` com `reason`).

Seller em item de outro Seller recebe `404 resource_not_found`. Buyer nas
rotas de listagem/detalhe do Seller recebe `403`. Sem token, `401`.

Nao existe `POST /v1/auth/register`. Usuarios existem so via seed.

O contrato `api/openapi.yaml` e a fonte da verdade e e escrito antes do codigo.
`tests/integration/test_openapi_contract.py` compara paths e metodos.

## Decisoes de contrato e de stack ja tomadas

- Atualizacao apenas por `PATCH`, com todos os campos opcionais. Nao ha `PUT`.
- Ofertas de um vendedor por filtro na listagem publica: `GET /v1/offers?seller_id=`.
- Preco como string decimal com duas casas (`"299.00"`), mapeado para `Decimal`
  e `NUMERIC(12,2)`.
- Listagens retornam array simples, sem envelope nem paginacao, **exceto**
  `GET /v1/order-items`.
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
- Users de seed: Loja A, Loja B e Buyer Demo, com `name`. Senha em `SEED_PASSWORD`.

## Configuracao

Lida de variaveis de ambiente, com `.env` local e `.env.example` como
referencia: `ENVIRONMENT`, `API_PREFIX`, `DATABASE_URL`, `TEST_DATABASE_URL`,
`JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `SEED_PASSWORD`. O `docker-compose.yml`
consome `POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_DB`. Nenhum valor de
credencial existe no repositorio.

## Persistencia

PostgreSQL 16 em container local, SQLAlchemy 2.0 e Alembic. Tabelas `sellers`,
`products`, `offers`, `users` (com `name`), `orders` e `order_items`. Testes
usam `TEST_DATABASE_URL`. `make test` exige o Postgres no ar.

## Convencoes

- Gerenciador de pacotes `uv`; comandos no `Makefile`.
- Lint e formatacao com `ruff`, linha de 100 colunas.
- Testes com `pytest`, em `tests/unit/` e `tests/integration/`.
- Idioma conforme `.cursor/rules/language-conventions.mdc`.

## O que ainda nao existe

- Pipeline de CI e qualquer artefato de deploy.
- Cadastro publico de usuarios, refresh token e IdP.
- Carrinho persistido, pagamentos, entrega, frontend.
- Communication (Conversation/Messages), dashboard/KPIs, WebSocket/SSE.
- Event bus, Outbox, Kafka, Redis ou observabilidade.
- Soft delete ou diferenciacao entre excluir e deixar de disponibilizar.

## Proxima etapa

Frontend, Communication ou dashboard — sem antecipar no backend.

## Historico de versoes

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

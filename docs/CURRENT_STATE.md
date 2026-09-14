# Estado atual do projeto

- **Versao**: 0.9.0
- **Fase**: P7 Dashboard — COMPLETE
- **Commit de referencia**: 70a8fc5
- **Repositório**: https://github.com/giordani-p/market-hub

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
`docs/P6.1_Foundation_Worker.md`, adiciona a fundacao de Jobs (SQS + Worker) e o
recalculo periodico de prioridade. A fase P6.2, especificada em
`docs/P6.2_Notification.md`, adiciona Notifications in-app via o Job
`NOTIFY_STATUS_CHANGE`. A fase P7, especificada em `docs/P7_Dashboard.md`,
adiciona `GET /v1/dashboard` como capability de leitura por papel, sem
persistencia propria. O plano da fase nao deve ser copiado para ca: este
documento descreve o que **existe hoje**.

## Arquitetura

Aplicacao FastAPI unica, organizada por dominio e nao por camada tecnica. Nao
ha Clean Architecture nem Hexagonal. Cada dominio entra como um modulo proprio
em `app/`.

`app/core/` guarda o que e transversal: configuracao, erros de negocio, eventos
em memoria e traducao para HTTP. `app/jobs/` e infra transversal de Jobs, nao
um dominio de produto.

Eventos de dominio (`OrderCreated`, `OrderItemStatusChanged`,
`OrderItemCancelled`, `ConversationCreated`, `MessageCreated`,
`ConversationClosed`, `ConversationPriorityChanged`, `InternalCommentCreated`)
sao acumulados na transacao e publicados no `InMemoryEventPublisher` somente
apos o `commit` da sessao. Eventos notificaveis enfileiram
`NOTIFY_STATUS_CHANGE` na mesma fila SQS; falha nesse publish nao desfaz o
commit (sem Outbox). Nao ha bus, Kafka nem Redis.

Jobs de background usam SQS no LocalStack. Uma EventBridge Rule
(`rate(15 minutes)`) publica `RECONCILE_PRIORITIES` na fila `market-hub-jobs`.
Um Worker em processo separado consome um Job por vez. Falhas nao deletam a
mensagem; apos `maxReceiveCount` (3) ela vai para `market-hub-jobs-dlq`. O
EventBridge Scheduler do LocalStack e mock e nao dispara fila; no AWS real o
mapeamento continua Scheduler → SQS. Recalculo por evento de dominio nao existe:
a fila Ops pode ficar ate cerca de 15 minutos defasada.

## Mapa do codigo

| Caminho              | O que contem                                                                            |
| -------------------- | --------------------------------------------------------------------------------------- |
| `app/main.py`        | `create_app()`, handlers de erro e routers com prefixo de versao                        |
| `app/core/config.py` | `Settings` e `get_settings()` com cache                                                 |
| `app/core/errors.py` | `DomainError` e subclasses, inclusive `CheckoutRejectedError`                           |
| `app/core/events.py` | dataclasses de evento e `InMemoryEventPublisher`                                        |
| `app/database.py`    | `Base`, engine, `session_transaction()` (commit + publish)                              |
| `app/health.py`      | router e schema do health check                                                         |
| `app/auth/`          | `User` (com `name` e `role` buyer/seller/ops), login, `/me`, JWT, seed                  |
| `app/catalog/`       | modelos, schemas, CRUD de Produto/Oferta e seed de sellers                              |
| `app/orders/`        | checkout, listagem/detalhe do Seller, status e cancelamento                             |
| `app/communication/` | Conversation, Messages, lazy close, batch de inatividade, PriorityPolicy e reconcilacao |
| `app/support/`       | listagem/detalhe Ops, InternalComment, fila e override critical                         |
| `app/jobs/`          | Job, registry, adapter SQS, Worker e enqueue                                            |
| `app/notifications/` | Notification in-app, canal, service, Job `NOTIFY_STATUS_CHANGE` e rotas                 |
| `app/dashboard/`     | Capability de leitura `GET /v1/dashboard` (projecao Seller/Buyer/Ops)                   |
| `api/openapi.yaml`   | contrato da API escrito a mao                                                           |
| `infra/local/`       | provisionamento LocalStack (filas, DLQ, EventBridge Rule)                               |
| `migrations/`        | Alembic `001`–`008` (notifications `008`)                                               |
| `tests/unit/`        | testes sem aplicacao montada                                                            |
| `tests/integration/` | testes via `TestClient` no Postgres de teste                                            |

## Contratos de API

Rotas implementadas, todas sob o prefixo `/v1`:

| Rota                                                            | Resposta                                                           |
| --------------------------------------------------------------- | ------------------------------------------------------------------ |
| `GET /v1/health`                                                | `HealthResponse` (`status`, `version`)                             |
| `POST /v1/auth/login`                                           | `TokenResponse`; `401 unauthorized` se a senha falhar              |
| `GET /v1/auth/me`                                               | `User` autenticado, inclusive `name`                               |
| `GET /v1/products`                                              | array de `Product`                                                 |
| `POST /v1/products`                                             | `201` + `Product`                                                  |
| `GET /v1/products/{product_id}`                                 | `Product`                                                          |
| `PATCH /v1/products/{product_id}`                               | `Product`                                                          |
| `DELETE /v1/products/{product_id}`                              | `204`; `409` se o produto ainda tiver ofertas                      |
| `GET /v1/offers`                                                | array de `Offer`; filtro opcional `?seller_id=` (publico)          |
| `POST /v1/offers`                                               | `201` + `Offer`; `seller_id` vem do JWT de seller                  |
| `GET /v1/offers/{offer_id}`                                     | `Offer`                                                            |
| `PATCH /v1/offers/{offer_id}`                                   | `Offer` do seller autenticado                                      |
| `DELETE /v1/offers/{offer_id}`                                  | `204`; `409` se houver order items                                 |
| `POST /v1/orders`                                               | checkout atomico; `201` + `Order` ou `409 checkout_rejected`       |
| `GET /v1/orders`                                                | orders do buyer autenticado, items com produto (`BuyerOrderItem`)  |
| `GET /v1/orders/{order_id}`                                     | `Order` do buyer autenticado, items com produto (`BuyerOrderItem`) |
| `GET /v1/order-items`                                           | envelope paginado dos items do seller autenticado                  |
| `GET /v1/order-items/{item_id}`                                 | detalhe do buyer ou do seller do item (`product`, `buyer`, `order`, `offer_id`) |
| `PATCH /v1/order-items/{item_id}`                               | avanca status no fluxo; mesmo status e idempotente                 |
| `POST /v1/order-items/{item_id}/cancel`                         | cancela conforme o papel; cancel repetido e idempotente            |
| `POST /v1/order-items/{item_id}/internal-comments`              | `201` InternalComment do Seller no proprio item                    |
| `GET /v1/order-items/{item_id}/internal-comments`               | array cronologico do Seller no proprio item                        |
| `POST /v1/order-items/{item_id}/conversation`                   | `201` nova ou `200` OPEN reutilizada                               |
| `GET /v1/order-items/{item_id}/conversations`                   | array por `last_interaction_at DESC`                               |
| `GET /v1/conversations/{conversation_id}`                       | Conversation do participante, com `effective_priority`             |
| `POST /v1/conversations/{conversation_id}/close`                | Seller fecha; ja `closed` responde `409`                           |
| `POST /v1/conversations/{conversation_id}/messages`             | `201` Message em Conversation `open`                               |
| `GET /v1/conversations/{conversation_id}/messages`              | janela de 24h UTC (`from`, `to`, `has_older`)                      |
| `GET /v1/ops/order-items`                                       | envelope paginado de todos os items (Ops)                          |
| `GET /v1/ops/order-items/{item_id}`                             | detalhe Ops (`product`, `buyer`, `seller`, `order`)                |
| `POST /v1/ops/order-items/{item_id}/internal-comments`          | `201` InternalComment do Ops                                       |
| `GET /v1/ops/order-items/{item_id}/internal-comments`           | array cronologico (mesmo historico do Seller)                      |
| `GET /v1/ops/order-items/{item_id}/conversations`               | historico open+closed do item, com prioridade                      |
| `GET /v1/ops/conversations`                                     | fila OPEN paginada por `effective_priority`                        |
| `GET /v1/ops/conversations/{conversation_id}`                   | Conversation Ops com prioridade persistida                         |
| `POST /v1/ops/conversations/{conversation_id}/priority/refresh` | recalcula `calculated_priority`                                    |
| `POST /v1/ops/conversations/{conversation_id}/critical`         | override `critical` + InternalComment                              |
| `POST /v1/ops/conversations/{conversation_id}/critical/remove`  | remove override                                                    |
| `GET /v1/notifications`                                         | envelope paginado das Notifications do usuario                     |
| `GET /v1/notifications/unread-count`                            | `{ unread_count }` do usuario autenticado                          |
| `PATCH /v1/notifications/{notification_id}/read`                | `200` Notification; alheia → `404`                                 |
| `PATCH /v1/notifications/read-all`                              | `204`; idempotente                                                 |
| `GET /v1/dashboard`                                             | projecao por papel (`seller`/`buyer`/`ops`); empty state e `200`   |

`GET /v1/order-items` aceita `page`, `page_size` (padrao 20, maximo 100),
`status`, `from`, `to` e `order_item_id`. Ordenacao `created_at DESC`. Lista
vazia responde `200` com `items`, `page`, `page_size` e `total`.
`GET /v1/ops/order-items` usa os mesmos parametros e acrescenta `seller_id`.
Cada item da listagem Ops inclui `seller` (`id`, `name` da tabela `sellers`).
`GET /v1/ops/conversations` lista so `open`, ordena `critical > high > medium > low`
e depois `last_interaction_at DESC`, e aceita `seller_id`, `order_item_id` e
`effective_priority`. Envelope `items`/`page`/`page_size`/`total`.

`GET /v1/notifications` usa `page`/`page_size` (padrao 20, maximo 100),
ordena `created_at DESC` e isola por `recipient_id` do JWT.

`GET /v1/dashboard` nao aceita query params: o escopo sai do JWT. Seller
agrega Order Items via `Offer.seller_id`; Buyer agrega Orders via
`buyer_id`; Ops ve Conversations `open` pela mesma ordem da fila
(`effective_priority`, depois `last_interaction_at DESC`). Empty state
responde `200` com zeros e listas vazias. Role fora de buyer/seller/ops
responde `403`. Sem token, `401`.

`GET /v1/conversations/{id}/messages` aceita `before` (date-time com timezone,
nao futuro). Sem `before`, retorna as Messages das ultimas 24h.

Erros de negocio respondem com `ErrorResponse` (`code`, `message`):
`resource_not_found` (404), `resource_in_use` e `invalid_transition` (409),
`unauthorized` (401), `forbidden` (403). Checkout invalido responde
`CheckoutRejected` (`code: checkout_rejected`, `items` com `reason`).

Seller em item de outro Seller recebe `404 resource_not_found`. Buyer na
listagem do Seller (`GET /v1/order-items`) recebe `403`; no detalhe
(`GET /v1/order-items/{item_id}`) do proprio item recebe `200` (desde o F5
do frontend, pro deep link de Notification resolver o `order_id`), de item
de outro buyer recebe `404`, e Ops nessa mesma rota recebe `403`. Sem
token, `401`. Participante
sem relacao com Conversation ou Order Item recebe `404`. Buyer em
`POST .../close` recebe `403`. Buyer e Seller em `/v1/ops/*` recebem `403`.
Ops nas rotas exclusivas de Seller/Buyer recebe `403`; em Conversation/Message
de participante, `404`. Ops le metadados de Conversation em `/v1/ops`, sem
Messages. Buyer/Seller (`ConversationResponse`) veem so `effective_priority`
(derivado); `calculated_priority` e `ops_override` continuam exclusivos de
`OpsConversation`, so lidos via `/v1/ops/*`.

Nao existe `POST /v1/auth/register`. Usuarios existem so via seed.

O contrato `api/openapi.yaml` e a fonte da verdade e e escrito antes do codigo.
`tests/integration/test_openapi_contract.py` compara paths e metodos.

## Frontend

Aplicacao nova em `frontend/` (Vite + React + TypeScript), consumindo o
backend acima via REST. Roadmap em `docs/FRONTEND_IMPLEMENTATION_PLAN.md`,
uma spec por fase em `docs/FRONTEND_F{n}_SPEC.md`. Ciclo de cada fase:
revisar contrato -> UX -> spec -> implementar -> testar -> validar no
browser -> commit -> proxima fase.

Fases concluidas e validadas manualmente pelo usuario:

- **F0 (Foundation)**: projeto, routing, cliente HTTP, auth (JWT em
  storage), layout e navegacao por role, componentes de UI compartilhados,
  estados de loading/error/empty.
- **F1 (Buyer Catalog + Purchase)**: `features/catalog` (listagem e detalhe
  de produto/oferta), checkout e `features/orders` (Buyer): lista e detalhe
  de Order, acompanhamento de status.
- **F2 (Seller Orders)**: `features/seller-orders`: listagem paginada com
  filtros (status, periodo, busca por id) e detalhe do Order Item.
- **F3 (Order Item + Communication)**: `StatusActions` (avancar/cancelar
  status no detalhe do Seller), `features/conversations`
  (`ConversationPanel`, thread Buyer<->Seller, prop `viewerRole`) e
  `features/support` (`InternalCommentsPanel`, log Seller<->Ops), ambos
  visualmente distintos por design. Bug pego em teste manual do usuario logo
  apos o F3 e corrigido na mesma fase: Conversation so tinha UI do lado do
  Seller; Buyer nao tinha rota de detalhe de Order Item. Corrigido com
  `BuyerOrderItemDetailPage` em
  `/buyer/orders/:orderId/items/:itemId` (o item vem de dentro de
  `GET /orders/{orderId}`, ja que nao existe `GET /order-items/{id}` para
  Buyer) e `ConversationPanel` generico o bastante para os dois papeis.
- **F4 (Ops Experience)**: `OpsQueuePage` (`/ops`, fila de Conversations
  `open` por prioridade efetiva, filtros de
  `seller_id`/`order_item_id`/`effective_priority`) e
  `OpsConversationDetailPage` (`/ops/conversations/:id`, contexto do Order
  Item + `PriorityActions` — recalcular, marcar/remover `critical` — +
  `InternalCommentsPanel` reaproveitado). Decisao registrada em
  `docs/FRONTEND_F4_SPEC.md`: sem historico de Messages para Ops (backend
  nao permite, por privacidade). Testando o F4, o usuario pediu mais uma
  coisa: o Seller tambem precisa ver a prioridade da propria Conversation —
  gap real de contrato (nao so de UI), resolvido com `effective_priority`
  em `ConversationResponse` (ver `## Contratos de API` e `Historico de
  versoes`); `ConversationPanel` (Buyer e Seller) mostra isso via
  `PriorityBadge`, agora em `components/ui/` por ser reaproveitado entre
  `features/conversations` e `features/ops`.
- **F5 (Notifications)**: `NotificationBell` no `AppLayout` (contagem de
  nao lidas, dropdown paginado, marcar uma/todas como lidas) e
  `features/notifications/resolveRoute.ts` (funcao pura que resolve a
  rota certa por papel + `entity_type`, com os fetches injetados por
  parametro pra ficar testavel). Gap real de contrato encontrado e
  resolvido na mesma fase: o deep link do Buyer precisa de `order_id`, que
  nao existia em nenhum lugar acessivel a ele —
  `GET /v1/order-items/{item_id}` passou a aceitar Buyer tambem (so
  leitura do proprio item; a listagem continua exclusiva do Seller).
- **F6 (Design Review + UX Polish + Notifications PT-BR)**: revisao de
  todas as telas F0-F5 contra a skill de projeto
  `frontend-design-patterns`; `lucide-react` adicionado (unica lib de
  icones do projeto, no lugar de emoji cru); variante `destructive` nova
  no `Button` pra acoes irreversiveis (cancelar pedido, encerrar
  conversa); dark mode automatico (`prefers-color-scheme`) **removido** —
  tema unico claro, decisao do usuario (a skill e o Mercado Livre real nao
  tem dark mode); `--color-danger` alinhado ao `--color-error` da skill,
  com `--color-danger-solid` novo pra preenchimento solido + texto branco
  (o hex puro da skill fica abaixo do contraste WCAG AA nesse uso).
  Notification (F5) passou a montar `title`/`message` no frontend a partir
  de `type` + `metadata`, em portugues (`features/notifications/copy.ts`)
  — antes exibia o texto pronto do backend, em ingles; decisao do
  usuario, pra alinhar com o padrao que status/prioridade/motivo ja
  usavam (traducao no frontend, nao no backend). Sem mudanca de contrato
  de backend nesta fase.
- **F7 (Dashboard + gaps de jornada)**: home por papel em
  `GET /v1/dashboard` (`/seller` e `/ops` no login; Buyer continua no
  catalogo, com Inicio em `/buyer`). Catalogo compartilhado em `/catalog`
  (compra so Buyer). Fila Ops em `/ops/queue`. Cancelamento do Buyer em
  `placed`/`preparing`. Lista/detalhe Ops de Order Items
  (`/ops/order-items`, historico de conversas sem Messages). Minhas
  ofertas do Seller (`/seller/offers`, CRUD de Offer e Product). Nav em
  PT-BR. Sem mudanca de contrato de backend.

Gaps reais de contrato encontrados e resolvidos ate aqui: CORS ausente
(F0), `BuyerOrderItem` sem produto em `GET /v1/orders` (F1),
`effective_priority` ausente em `ConversationResponse` (F4) e
`GET /v1/order-items/{item_id}` restrito ao Seller, sem acesso do Buyer ao
proprio item (F5).

Ainda nao existe: UI de Notifications push/real-time (fora de escopo,
so poll); qualquer coisa alem do que este documento ja descreve. Ver
`docs/FRONTEND_F7_SPEC.md` para o detalhe da ultima fase fechada.

## Decisoes de contrato e de stack ja tomadas

- `BuyerOrderItem` (usado so em `Order.items`) inclui `product` (`ProductSummary`).
  O `OrderItem` generico (resposta de `PATCH`/`cancel` de Order Item) continua sem
  produto: e um schema a parte, nao o mesmo reaproveitado.
- Atualizacao apenas por `PATCH`, com todos os campos opcionais. Nao ha `PUT`.
- `GET /v1/order-items/{item_id}` aceita Buyer e Seller (desde o F5 do
  frontend). Buyer so acessa o proprio item (`Order.buyer_id`), so leitura
  (sem `PATCH`/`cancel` por essa rota generica -- cancelamento do Buyer
  continua so em `POST .../cancel`); Seller mantem o escopo por `seller_id`
  de sempre. A listagem (`GET /v1/order-items`) continua exclusiva do Seller.
- Ofertas de um vendedor por filtro na listagem publica: `GET /v1/offers?seller_id=`.
- Preco como string decimal com duas casas (`"299.00"`), mapeado para `Decimal`
  e `NUMERIC(12,2)`.
- Listagens retornam array simples, sem envelope nem paginacao, **exceto**
  `GET /v1/order-items`, `GET /v1/ops/order-items`, `GET /v1/ops/conversations`,
  `GET /v1/conversations/{id}/messages` e `GET /v1/notifications`.
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
- `ConversationResponse` (Buyer/Seller) inclui `effective_priority` desde o
  F4 do frontend (decisao do usuario em 2026-09-13, para o Seller enxergar a
  prioridade da propria Conversation) — mesmo campo, calculado do mesmo jeito
  que em `OpsConversation`, mas sem `calculated_priority`/`ops_override`
  (o breakdown continua exclusivo da Ops).
- Conversation persiste `priority_calculated_at` (nullable). Order Item persiste
  `status_updated_at`. Nenhum dos dois aparece na API. OPEN e stale quando o
  calculo e nulo, a ultima interacao ou o status sao posteriores, ou o age
  bucket mudou. O Job `RECONCILE_PRIORITIES` pagina essas Conversations, reusa
  a PriorityPolicy V1, nao mexe em `ops_override` e e idempotente.
- `close_inactive` continua fora da fila SQS (`make close-inactive`).
- Notifications in-app: Job `NOTIFY_STATUS_CHANGE` apos commit. Status de
  OrderItem (`OrderItemStatusChanged`, inclusive cancelamento) e close de
  Conversation (`ConversationClosed`) avisam Buyer + Seller. Mudanca real de
  `effective_priority` (`ConversationPriorityChanged`, inclusive reconcile e
  critical) avisa Seller + Ops. `ConversationCreated` e `MessageCreated` nao
  notificam. `title`/`message` em ingles. Idempotencia por unique
  `(recipient, type, entity, previous, new, changed_at)`. Canal so `IN_APP`.
  A API nao espera a Notification; `make test` usa fila in-memory.

## Configuracao

Lida de variaveis de ambiente, com `.env` local e `.env.example` como
referencia: `ENVIRONMENT`, `API_PREFIX`, `CORS_ORIGINS`, `DATABASE_URL`, `TEST_DATABASE_URL`,
`JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `SEED_PASSWORD`,
`CONVERSATION_INACTIVITY_HOURS`, `AWS_ENDPOINT_URL`, `AWS_REGION`,
`JOBS_QUEUE_NAME`, `JOBS_DLQ_NAME`, `JOBS_VISIBILITY_TIMEOUT_SECONDS`,
`JOBS_MAX_RECEIVE_COUNT`, `JOBS_WAIT_TIME_SECONDS`, `RECONCILE_PAGE_SIZE`,
`JOBS_SCHEDULE_EXPRESSION`. `AWS_ENDPOINT_URL` local padrao e
`http://localhost:4566`; o cliente SQS usa keys dummy nesse endpoint para nao
herdar `~/.aws`. `CORS_ORIGINS` e uma lista separada por virgula (padrao
`http://localhost:5173,http://localhost:3000`) e habilita `CORSMiddleware`
para o frontend local. O `docker-compose.yml` consome
`POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_DB`. Credenciais dummy do
LocalStack tambem ficam no Compose do Worker. Nenhum valor de credencial real
existe no repositorio.

## Persistencia

PostgreSQL 16 em container local, SQLAlchemy 2.0 e Alembic. Tabelas `sellers`,
`products`, `offers`, `users` (com `name`), `orders`, `order_items`,
`conversations`, `messages`, `internal_comments` e `notifications`.
`conversations` tem `priority_calculated_at`; `order_items` tem
`status_updated_at`. Testes usam `TEST_DATABASE_URL`. `make test` exige o
Postgres no ar e nao sobe LocalStack.

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
- Carrinho persistido, pagamentos, entrega.
- Inbox global de frontend, KPIs/analytics, WebSocket/SSE.
- Event bus, Outbox, Kafka, Redis ou observabilidade alem dos logs do Worker.
- Soft delete ou diferenciacao entre excluir e deixar de disponibilizar.
- Canais Email/Slack/WhatsApp e notificacoes de `MessageCreated`.

## Proxima etapa

SLA e transcript Ops no backend continuam sem especificacao. O roadmap
frontend F0-F7 esta completo.

## Historico de versoes

- **0.9.0** — P7 Dashboard: `GET /v1/dashboard` projeta Summary/Attention/Recent
  por papel (Seller em Order Items, Buyer em Orders, Ops na fila de prioridade),
  sem tabela nem agregado proprio. Contrato discriminado por `role` em
  `api/openapi.yaml`; queries agregadas no banco; helper `preview_open_queue`.
- **0.8.0** — F6 (Design Review + UX Polish + Notifications PT-BR)
  mergeado na main (PR #15, commit `6df71e2`): dark mode removido,
  `lucide-react` adicionado, variante `destructive` no `Button`, copy de
  Notification em portugues, ajustes de contraste/paleta contra a skill
  `frontend-design-patterns`. Sem mudanca de contrato de backend.
- **0.8.0** — F5 (Notifications) mergeado na main (PR #14, commit
  `a0d2338`): `NotificationBell`, deep link por papel + `entity_type`.
- **0.8.0** — `GET /v1/order-items/{item_id}` passou a aceitar Buyer (so
  leitura do proprio item), nao so Seller (`api/openapi.yaml`,
  `app/orders/access.py`/`routes.py`), gap real achado revisando o contrato
  do F5 do frontend: o deep link de Notification (`entity_type=ORDER_ITEM`)
  so tem o `item_id`, e a rota do Buyer (`/buyer/orders/:orderId/items/:itemId`)
  precisa do `order_id`, que agora vem em `OrderItemDetail.order.id`.
- **0.8.0** — F4 (Ops Experience) validado manualmente pelo usuario (Ops e
  Seller, incluindo o `effective_priority` novo) e mergeado na main (PR #13,
  commit `5b47254`).
- **0.8.0** — `ConversationResponse` (Buyer/Seller) ganhou `effective_priority`
  (`api/openapi.yaml`, `app/communication/schemas.py`/`routes.py`), pedido
  pelo usuario testando o F4 do frontend: Seller precisava ver a prioridade
  da propria Conversation, nao so a Ops. `calculated_priority`/`ops_override`
  continuam exclusivos de `OpsConversation`. Teste de contrato
  (`test_priority.py`) atualizado para essa exposicao deliberada.
- **0.8.0** — CURRENT_STATE.md atualizado para refletir F0-F3 do frontend
  concluidos e validados; cabecalho estava com "Fase: F.0" incorreta apos o
  merge do F3 (PR #12).
- **0.8.0** — CORS habilitado (`CORS_ORIGINS`) e `BuyerOrderItem` com produto
  em `GET /v1/orders` e `/v1/orders/{id}`, para viabilizar o frontend F0/F1.
- **0.8.0** — P6.2: Notifications in-app (`NOTIFY_STATUS_CHANGE`), canal
  PostgreSQL, APIs de inbox do usuario, prioridade efetiva para Seller+Ops.

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

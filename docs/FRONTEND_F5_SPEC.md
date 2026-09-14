# Market Hub — F5 — Notifications (Spec)

Deriva de `docs/FRONTEND_IMPLEMENTATION_PLAN.md`. Assume F0-F4 prontos,
validados no browser e mergeados na main.

---

## 1. Objetivo

Notificacoes in-app como mecanismo transversal: indicador de nao lidas no
header, lista com as notificacoes, marcar lida/todas e navegar pro contexto
certo (Order Item ou Conversation) conforme o papel de quem esta logado.

## 2. Contexto (verificado no backend nesta sessao)

- `GET /v1/notifications` (`page`/`page_size`, padrao 20/max 100, ordena
  `created_at DESC`, isola por `recipient_id` do JWT), `GET
  /v1/notifications/unread-count`, `PATCH
  /v1/notifications/{id}/read` (alheia -> `404`), `PATCH
  /v1/notifications/read-all` (`204`, idempotente).
- `NotificationResponse`: `id`, `type`
  (`ORDER_ITEM_STATUS_CHANGED`/`CONVERSATION_STATUS_CHANGED`/`CONVERSATION_PRIORITY_CHANGED`),
  `title`, `message` (backend gera os dois, **prontos pra exibir, em
  ingles** — o frontend nao reconstroi nem traduz, conforme
  `FRONTEND_IMPLEMENTATION_PLAN.md` §10: "nao deve reconstruir titulos ou
  mensagens de negocio quando esses dados forem fornecidos pelo backend"),
  `entity_type` (`ORDER_ITEM`/`CONVERSATION`), `entity_id`, `metadata`
  (`previous_status`/`new_status`, so contexto extra, nao usado pra montar
  copy), `created_at`, `read_at` (`null` = nao lida).
- Quem recebe o que (regra do backend, a UI nao decide): status de Order
  Item (inclusive cancelamento) e Conversation fechada avisam **Buyer +
  Seller**; mudanca real de `effective_priority` avisa **Seller + Ops**.
  `ConversationCreated`/`MessageCreated` nao notificam.
- **Gap real encontrado e resolvido nesta sessao**: o deep link do Buyer
  precisa de `order_id`, que nao vinha em lugar nenhum (nem na Notification,
  nem em rota acessivel ao Buyer). `GET /v1/order-items/{item_id}` passou a
  aceitar Buyer tambem (so leitura do proprio item; a listagem continua
  exclusiva do Seller) — ver `docs/CURRENT_STATE.md`. Decisao do usuario:
  estender o backend, no mesmo padrao usado em gaps anteriores (F0 CORS, F1
  produto no Order, F4 `effective_priority`).

### Resolucao de rota por papel + entity_type

Nenhuma logica de negocio nova — so navegacao. Tabela de quantas chamadas
cada combinacao exige antes de montar a URL:

| Papel  | entity_type    | Resolucao                                                                 | Rota final |
| ------ | -------------- | -------------------------------------------------------------------------- | ---------- |
| Seller | `ORDER_ITEM`   | nenhuma — `entity_id` ja e o `item_id`                                     | `/seller/orders/{entity_id}` |
| Seller | `CONVERSATION` | `GET /v1/conversations/{entity_id}` -> `order_item_id`                     | `/seller/orders/{order_item_id}` |
| Buyer  | `ORDER_ITEM`   | `GET /v1/order-items/{entity_id}` -> `order.id`                            | `/buyer/orders/{order.id}/items/{entity_id}` |
| Buyer  | `CONVERSATION` | `GET /v1/conversations/{entity_id}` -> `order_item_id`, depois `GET /v1/order-items/{order_item_id}` -> `order.id` | `/buyer/orders/{order.id}/items/{order_item_id}` |
| Ops    | `CONVERSATION` | nenhuma — `entity_id` ja e o `conversation_id` (so `CONVERSATION_PRIORITY_CHANGED` chega pra Ops) | `/ops/conversations/{entity_id}` |

Ops nunca recebe `entity_type=ORDER_ITEM` (o backend so notifica
Buyer/Seller de status de Order Item), entao essa combinacao nao existe.

## 3. Escopo

### Notification Bell (no `AppLayout`, header)

- Troca o `🔔` estatico/desabilitado (`app-notifications`,
  `aria-hidden`, `cursor: not-allowed`) por um indicador real: busca
  `unread-count` ao montar o layout autenticado e depois de qualquer
  mutacao (marcar lida/todas); mostra a contagem (`0` esconde o badge).
- Clicar abre um dropdown com a lista (`GET /v1/notifications`,
  paginacao simples "carregar mais" reaproveitando `has_older`-like padrao
  ja usado em Messages, ou pagina numerica como as demais listas —
  qualquer uma serve, o critico e nao recarregar a lista inteira a cada
  clique).
- Cada notificacao mostra `title`, `message` (como vem, sem traducao),
  tempo relativo/formatado (`formatDateTime`) e se esta lida (peso de fonte
  + indicador, nunca so cor).
- Clicar numa notificacao: `PATCH .../read` (se ainda nao lida) e navega
  pra rota resolvida (tabela acima) — nessa ordem, mas sem bloquear a
  navegacao esperando o `PATCH` responder (mutation feedback so precisa
  cobrir falha, nao atrasar o clique).
- Botao "Marcar todas como lidas" (`PATCH read-all`), com estado
  processando.
- Mesmo componente pros tres papeis — a diferenca de quem recebe o que ja
  vem do backend; o frontend so resolve rota diferente por
  papel/entity_type.

## 4. Fora de escopo (explicito)

- Mudar quem e notificado ou o texto de `title`/`message` — regra e copy
  sao do backend.
- Push/real-time (WebSocket/SSE) — poll simples ao montar/apos mutacao,
  sem infra nova.
- Recalcular status/prioridade a partir da notificacao — a tela de destino
  busca o estado atual sozinha.
- Traduzir `title`/`message` pro portugues — deliberado (ver secao 2).

## 5. Direcao visual (aplicando a skill `frontend-design-patterns`)

Sino discreto e acionavel (padrao ja descrito na skill, secao "Notifications"):
contagem como pill pequeno de acento, nao amarelo (evitar amarelo como CTA).
Nao lida se diferencia por peso de fonte/indicador, nunca so opacidade ou
so cor. Dropdown simples, sem novo componente de modal/drawer.

## 6. Rotas

Nenhuma nova. O bell/dropdown vive dentro do `AppLayout`, sem rota propria.

## 7. Estados

- Dropdown tem loading/error/empty proprios (`Nenhuma notificacao ainda.`);
  falha nao trava o resto do header.
- Mutation feedback: marcar uma ou todas mostra "processando" e desabilita
  repeticao.

## 8. Criterios de aceite

1. Usuario ve a contagem de nao lidas atualizada ao montar e apos ler.
2. Abre o dropdown, ve titulo/mensagem/tempo de cada notificacao.
3. Clica numa notificacao: ela marca como lida e navega pro contexto certo
   — testar pelo menos um caso de cada linha da tabela da secao 2.
4. Marca todas como lidas de uma vez.
5. Falha de rede no dropdown nao quebra o resto da tela.

## 9. Testes

- Unit: helper de resolucao de rota (papel + entity_type -> rota final),
  cobrindo as 5 combinacoes da tabela.
- Component: `NotificationBell` (contagem, dropdown, marcar lida, marcar
  todas, navegacao ao clicar).
- Backend: `test_seller_order_items.py` ja cobre Buyer no
  `GET /v1/order-items/{item_id}` (200 no proprio item, 403 na listagem).

## 10. Definition of Done (F5)

- `npm run lint`, `npm run test`, `tsc -b` e `npm run build` limpos no
  frontend; `pytest` e `ruff check` limpos no backend (mudanca de contrato
  desta fase).
- Validado manualmente no browser pelo usuario, nos tres papeis.

## 11. Instrucoes para implementacao (Cursor)

1. `types/notification.ts`: `Notification`, `NotificationType`,
   `NotificationEntityType`, `NotificationListResponse`.
2. `features/notifications/api.ts`: `fetchNotifications(filters)`,
   `fetchUnreadCount()`, `markAsRead(id)`, `markAllAsRead()`.
3. `features/notifications/resolveRoute.ts`: funcao pura
   `resolveNotificationRoute(role, notification, { fetchOrderItem,
   fetchConversation })` (ou equivalente) implementando a tabela da secao
   2 — testavel isoladamente, sem side effect de navegacao dentro dela.
4. `features/notifications/NotificationBell.tsx`: composto no
   `AppLayout.tsx`, no lugar do `🔔` estatico.
5. Nao tocar em `features/catalog`, `features/orders`,
   `features/seller-orders`, `features/conversations`, `features/support`
   nem `features/ops` alem de consumir suas rotas via `useNavigate` — nenhum
   componente dessas features muda.

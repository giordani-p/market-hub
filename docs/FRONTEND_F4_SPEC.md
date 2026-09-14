# Market Hub — F4 — Ops Experience (Spec)

Deriva de `docs/FRONTEND_IMPLEMENTATION_PLAN.md`. Assume F0-F3 prontos,
validados no browser e mergeados na main.

---

## 1. Objetivo

Dar a Ops uma fila operacional: ver as Conversations `open` ordenadas por
prioridade efetiva, abrir o contexto de uma delas (Order Item, Seller,
Buyer, Product, prioridade) e agir — marcar/remover `critical` com
justificativa — sem duplicar regra de calculo que e do backend.

## 2. Contexto (verificado no backend nesta sessao)

Sem gaps de contrato para o que este spec cobre — `GET /v1/ops/conversations`,
`GET /v1/ops/conversations/{id}`, `POST .../priority/refresh`,
`POST .../critical`, `POST .../critical/remove`,
`GET/POST /v1/ops/order-items/{id}/internal-comments` e
`GET /v1/ops/order-items/{id}` ja cobrem tudo abaixo. Nenhuma mudanca de
backend nesta fase.

- **Gap real encontrado e resolvido por decisao do usuario em 2026-09-13**:
  `FRONTEND_IMPLEMENTATION_PLAN.md` (secao F4) pede "historico da
  Conversation" na tela de detalhe do Ops. O backend nao permite —
  `load_participant_conversation` (usado em `GET /v1/conversations/{id}` e
  `/messages`) so aceita `role == buyer` ou `role == seller`; Ops recebe
  `404`. Isso e decisao de privacidade ja registrada em
  `docs/CURRENT_STATE.md` ("Ops le metadados de Conversation em `/v1/ops`,
  sem Messages"), nao bug. **Decisao**: este spec respeita o backend como
  esta. A tela de detalhe do Ops mostra status/motivo/prioridade da
  Conversation e o contexto do Order Item, mas nunca o texto das mensagens
  Buyer<->Seller. Sem mudanca de backend nesta fase.
- `GET /v1/ops/conversations` retorna so `status == open`, ordenado por
  `critical > high > medium > low` e depois `last_interaction_at DESC`.
  Aceita `seller_id`, `order_item_id` e `effective_priority` como filtro,
  mais `page`/`page_size` (envelope `items`/`page`/`page_size`/`total`).
- `effective_priority` e derivado (`ops_override` se existir, senao
  `calculated_priority`) — a UI so exibe, nunca recalcula.
- `POST .../priority/refresh` recalcula `calculated_priority` sem mexer em
  `ops_override`. `POST .../critical` marca override e cria um Internal
  Comment com a justificativa (`409` se ja `critical`); `.../critical/remove`
  remove o override (`409` se nao houver override). Ambos retornam a
  `OpsConversation` atualizada.
- `GET /v1/ops/conversations/{id}` **nao** inclui Seller/Buyer/Product — so
  `OpsConversation` (Conversation + prioridade). Para o contexto completo,
  a tela busca tambem `GET /v1/ops/order-items/{order_item_id}` (usando o
  `order_item_id` da Conversation), que traz `product`, `buyer`, `seller` e
  `order`.
- Internal Comment de Ops usa `/v1/ops/order-items/{id}/internal-comments`
  (rota separada da do Seller, `/v1/order-items/{id}/internal-comments`,
  mas mesmo schema `InternalCommentResponse`, `author_type` `ops`/`seller`).
- `InternalCommentsPanel` (de `features/support`, do F3) hoje so serve o
  Seller: rotula o autor como "Ops"/"Voce" (assumindo viewer == seller) e
  chama sempre a rota do Seller. Precisa da mesma generalizacao que o F3 fez
  no `ConversationPanel` (prop `viewerRole`) — ver secao 11. Licao do F3:
  nao esperar bug report do usuario testando como Ops pra descobrir isso.

## 3. Escopo

### Ops Queue (`/ops`)

- Lista as Conversations `open` de `GET /v1/ops/conversations`: Seller,
  Buyer, Product, status do Order Item, Purchase Price e prioridade efetiva
  por linha.
- Filtros disponiveis no contrato: `seller_id`, `order_item_id`,
  `effective_priority`. Paginacao conforme envelope.
- Cada linha navega para o detalhe da Conversation (`/ops/conversations/:id`).
- Loading/error/empty (`Nenhuma conversa em aberto.`) proprios da lista.

### Conversation Detail (`/ops/conversations/:conversationId`)

- Busca `GET /v1/ops/conversations/{id}` e, com o `order_item_id` retornado,
  `GET /v1/ops/order-items/{order_item_id}` para o contexto completo.
- Exibe: Product, Buyer, Seller, dados do Order (`order_id`, data), status
  do Order Item, motivo e status da Conversation, prioridade calculada,
  override e efetiva.
- **Nao exibe mensagens** — nem tenta buscar `/v1/conversations/{id}/messages`
  (ver secao 2). Se quiser deixar isso claro na UI, uma nota curta tipo
  "Conteudo da conversa com o Buyer nao e visivel para Ops" e suficiente;
  sem simular ou placeholder de chat vazio.
- Acoes de prioridade: "Recalcular prioridade" (`priority/refresh`); quando
  `ops_override` for nulo, botao "Marcar como critical" com campo de
  justificativa obrigatorio; quando ja `critical`, botao "Remover critical"
  (sem justificativa, conforme contrato). Erro de transicao (`409`) exibido
  inline, sem navegar.
- `InternalCommentsPanel` (reaproveitado do F3, com prop `viewerRole: 'ops'`)
  abaixo, usando a rota `/v1/ops/order-items/{id}/internal-comments`.

## 4. Fora de escopo (explicito)

- Historico de Messages Buyer<->Seller para Ops (backend nao permite —
  secao 2).
- `GET /v1/ops/order-items` (listagem geral de Order Items da Ops, sem
  filtro por Conversation `open`) — o roadmap nao pede uma tela dedicada a
  isso no F4; a fila e por Conversation, nao por Order Item.
- SLA, transcript ou qualquer coisa alem do que `docs/CURRENT_STATE.md` ja
  documenta como implementado.
- Notificacoes in-app — F5.

## 5. Direcao visual (aplicando a skill `frontend-design-patterns`)

Fila operacional, nao lista de e-mail: densidade de informacao alta, mas
com a prioridade como primeiro criterio visual (nao so ordenacao) — a cor
de acento (amarelo de marca) marca `critical`, nunca decorativo em outras
linhas. `PriorityBadge` e um componente novo, visualmente distinto do
`StatusBadge` do Order Item (cores e vocabulario diferentes: prioridade
nao e status de pedido).

O painel de contexto do Order Item na tela de detalhe reaproveita o
`Card`/`dl` que `SellerOrderItemDetailPage` e `BuyerOrderItemDetailPage` ja
usam — mesma linguagem visual entre os tres papeis para o mesmo tipo de
dado. O painel de Internal Support continua com o tom "de bastidor" que o
F3 definiu, sem herdar nada do estilo de bolha de chat.

Evitar: rotulos em CAIXA ALTA, cards identicos com sombra generica em tudo.
Manter a paleta do Mercado Livre ja definida (amarelo de marca como acento
pontual, azul para acao primaria; vermelho/laranja reservado para
`critical`, nunca para outro estado).

## 6. Rotas

Novas:

- `/ops` — `OpsQueuePage`, substitui o placeholder atual (`RoleHomePage`
  com `role="ops"`).
- `/ops/conversations/:conversationId` — `OpsConversationDetailPage`.

`app/layout/nav.ts`: item `Queue` do papel `ops` ganha `to: '/ops'`. Item
`Operations` continua so rotulo (sem `to`), como hoje.

## 7. Estados

- Queue e Detail tem loading/error/empty proprios; o painel de prioridade e
  o de Internal Support dentro do Detail tambem — falha em um nao trava os
  outros (mesmo principio do F3).
- Empty da Queue: `Nenhuma conversa em aberto.`
- Mutation feedback: recalcular prioridade, marcar/remover critical e
  registrar Internal Comment mostram estado "processando" e desabilitam a
  acao repetida.

## 8. Criterios de aceite

1. Ops abre a fila, ve as Conversations `open` ordenadas por prioridade
   efetiva e filtra por Seller/Order Item/prioridade.
2. Ops abre o detalhe de uma Conversation e ve o contexto completo
   (Product, Buyer, Seller, Order, status, prioridade) sem ver mensagens.
3. Ops recalcula prioridade, marca `critical` com justificativa e remove o
   override; tentativa invalida (`409`) nao quebra a tela.
4. Ops registra e le Internal Comments no mesmo Order Item, com o mesmo
   componente do Seller, rotulado corretamente ("Ops"/"Voce"/"Seller"
   conforme quem esta vendo).
5. Fechar e reabrir a pagina preserva o estado real vindo da API.

## 9. Testes

- Unit: nenhum helper novo de calculo (prioridade e so exibida, nao
  calculada no frontend).
- Component: `OpsQueuePage` (lista, filtro, paginacao, empty); acoes de
  prioridade no Detail (refresh, marcar/remover critical, erro `409`);
  `InternalCommentsPanel` com `viewerRole: 'ops'` (rotulo do autor e rota
  usada).

## 10. Definition of Done (F4)

- `npm run lint`, `npm run test`, `tsc -b` e `npm run build` limpos.
- Backend sem alteracoes nesta fase.
- Validado manualmente no browser pelo usuario, logado como Ops.

## 11. Instrucoes para implementacao (Cursor)

1. `types/ops.ts`: `OpsConversation`, `OpsConversationQueueItem`,
   `OpsConversationQueueResponse`, `OpsOrderItemDetail` — espelhando
   `app/support/schemas.py` (campos em `snake_case`, iguais ao contrato).
2. `features/ops/api.ts`: `fetchOpsConversationQueue(filters)`,
   `fetchOpsConversation(id)`, `fetchOpsOrderItem(orderItemId)`,
   `refreshOpsPriority(id)`, `applyOpsCritical(id, justification)`,
   `removeOpsCritical(id)`.
3. `features/ops/OpsQueuePage.tsx` e `features/ops/OpsConversationDetailPage.tsx`.
4. `features/ops/PriorityBadge.tsx`, novo componente (nao reaproveitar
   `StatusBadge`).
5. `features/support/InternalCommentsPanel.tsx` ganha prop
   `viewerRole: 'seller' | 'ops'` (default `'seller'` para nao quebrar o
   Seller existente): troca o rotulo do autor (`author_type === viewerRole`
   -> "Voce"; senao o outro papel) e a rota chamada
   (`/order-items/{id}/internal-comments` para `seller`,
   `/ops/order-items/{id}/internal-comments` para `ops`). Ajustar
   `features/support/api.ts` para aceitar a base da rota.
6. Atualizar `AppRouter.tsx` (rotas do item 6 desta spec) e `app/layout/nav.ts`.
7. Nao tocar em `features/catalog`, `features/orders` (Buyer),
   `features/seller-orders` nem `features/conversations`.

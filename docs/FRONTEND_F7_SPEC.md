# Market Hub — F7 — Dashboard + gaps de jornada (Spec)

Deriva de `docs/FRONTEND_IMPLEMENTATION_PLAN.md` e do cruzamento entre
`docs/Project_Context.md` e as rotas de `docs/CURRENT_STATE.md`. Assume
F0-F6 prontos, validados no browser e mergeados na main. Backend P7
(`GET /v1/dashboard`) ja existe. Nenhuma mudanca de contrato nesta fase.

---

## 1. Objetivo

Fechar a home operacional dos tres papeis e os gaps de jornada em que o
backend ja tem rota e o frontend ainda nao usa:

1. Dashboard (`GET /v1/dashboard`) — Seller e Ops caem nele no login;
   Buyer continua no catalogo, com item Inicio extra.
2. Catalogo compartilhado em `/catalog` para os tres papeis (compra so Buyer).
3. Cancelamento do Buyer (`POST /v1/order-items/{id}/cancel` em
   `placed`/`preparing`).
4. Contexto operacional da Ops sem conversa aberta (`GET /v1/ops/order-items`
   + historico `GET /v1/ops/order-items/{id}/conversations`).
5. Minhas ofertas do Seller (CRUD de Offer + Product).

O frontend continua camada de apresentacao: formatar, linkar, loading/empty/error.
Nao recalcula prioridade, totais, active/completed nem ownership de Product.

---

## 2. Contexto (verificado no backend)

- `GET /v1/dashboard` devolve union discriminada por `role` (`seller` /
  `buyer` / `ops`). Empty state e `200` com zeros / listas vazias. Sem
  query params: o escopo sai do JWT. Uma chamada so.
- Buyer cancela so `placed`/`preparing`. Seller tambem `in_transit`. Ops
  recebe `403` em cancel/PATCH de status.
- `GET /v1/ops/order-items` e envelope paginado (`items[].order_item_id`,
  nao `id`). Filtros: `status`, `from`, `to`, `order_item_id`, `seller_id`.
- `GET /v1/ops/order-items/{id}/conversations` lista open+closed do item,
  com prioridade. Ops nunca le Messages.
- Product e vitrine global (POST/PATCH/DELETE **nao exigem JWT**). Offer e
  do Seller (`seller_id` no JWT em POST; PATCH/DELETE 403 se nao for dono).
  UI so expoe escrita a Seller autenticado. Nao inventar ownership de Product.
- `GET /v1/health` fica fora da SPA (ops/infra). Inbox de Conversation do
  Seller nao existe no backend — Attention do dashboard e contagem + link
  para `/seller/orders`.

---

## 3. Escopo

### 3.1 Dashboard

Uma `GET /dashboard`. Despacha pela `role` da resposta (nao pelo JWT).
Tres blocos: Summary → Attention → Recent. Sem graficos.

**Seller** (`/seller`, home do login)

- Summary: total, ativos, cinco status (sempre as chaves, inclusive 0).
  Clique no status → `/seller/orders?status=`.
- Attention: `N conversas em aberto` → `/seller/orders`.
- Recent: ate 5 items → `/seller/orders/:orderItemId`.
- Empty: `Nenhum pedido na sua operacao.` + link Catalogo.

**Buyer** (`/buyer`, nao e a home do login)

- Summary: pedidos ativos / concluidos (valores da API) → `/buyer/orders`.
- Attention: conversas abertas → `/buyer/orders`.
- Recent: pedidos com `total_amount` → `/buyer/orders/:orderId`. O status
  exibido e o do Order Item (produto), nao o status derivado do Order
  (`in_progress` | `completed` | `cancelled` continua so no contrato).
- Empty: `Voce ainda nao fez nenhum pedido.` + link Catalogo.
- Nao renderiza `calculated_priority` nem preview de fila.

**Ops** (`/ops`, deixa de ser a fila)

- Summary: abertas + quatro prioridades. Clique →
  `/ops/queue?effective_priority=`.
- Attention: preview (max. 5) → `/ops/conversations/:conversationId`.
  Link `Ver fila completa` → `/ops/queue`. Empty: `Nenhuma conversa em aberto.`
- `recent` vazio da API nao vira secao fantasma.

### 3.2 Catalogo compartilhado

Rotas canônicas `/catalog` e `/catalog/:productId`. Redirect de
`/buyer/catalog...`. Lista: `GET /products` + `GET /offers`; card com
"A partir de {preco}" da menor oferta `available && stock > 0`. Sem oferta
disponivel, card visivel, sem preco, tom muted. Filtro "Somente disponiveis"
(client-side). Detalhe: ofertas (preco, estoque) para todos.
`PurchasePanel` so se `user.role === 'buyer'`.

### 3.3 Filtros via URL

`SellerOrdersListPage` le/escreve `status`. `OpsQueuePage` le/escreve
`effective_priority`. O Dashboard so navega; nao reconstrói a lista.

### 3.4 Cancelamento do Buyer

Em `BuyerOrderItemDetailPage`: botao "Cancelar item" com confirmacao,
so em `placed`/`preparing`. `POST /order-items/{id}/cancel` e reload.
Nao reusar `StatusActions` (stepper + cancel em `in_transit`).
`canBuyerCancel` separado de `canCancel` do Seller.

### 3.5 Ops: Order Items

- Lista `/ops/order-items`: filtros do contrato + paginacao. Empty:
  `Nenhum item encontrado.`
- Detalhe `/ops/order-items/:itemId`: item + historico de conversas
  (link para `/ops/conversations/:id`) + `InternalCommentsPanel`
  `viewerRole: 'ops'`. Sem Messages, sem avancar/cancelar status.
- `OpsConversationDetailPage` ganha link "Ver item".

### 3.6 Seller: Minhas ofertas

- Lista `/seller/offers`: `GET /offers?seller_id={jwt.seller_id}` +
  `GET /products` para o nome. CTA cadastrar.
- Nova `/seller/offers/new`: produto existente ou `POST /products` e
  depois `POST /offers` `{ product_id, price, stock, available }`.
  Preco como `Price` (`"10.00"`).
- Detalhe `/seller/offers/:offerId`: `GET /offers/{id}` + produto.
  PATCH offer; DELETE offer (`409` inline). PATCH product (nome/descricao)
  com copy de que o produto e compartilhado. DELETE product (`409` se
  houver ofertas).

---

## 4. Fora de escopo

- Graficos, analytics, cache, nova rota de backend.
- Inbox de Conversation do Seller.
- `GET /v1/health` na UI.
- Auth em Product (seria backend).
- SLA, transcript, registro de usuario.
- Traduzir o resto do app alem da nav e das telas desta fase.

---

## 5. Direcao visual

Home operacional de marketplace, nao dashboard SaaS: sem graficos, sem
cards identicos com sombra. Numeros do summary sao links, nao
mini-analytics. `critical` usa o acento ja do `PriorityBadge`. Catalogo
e ofertas seguem o `product-grid` / `Card` existentes. Formularios de
oferta usam `Input`/`Button` padrao. 409 de delete inline, sem navegar.

---

## 6. Rotas de UI

| Rota | Pagina |
| --- | --- |
| `/buyer` | Dashboard Buyer |
| `/seller` | Dashboard Seller |
| `/ops` | Dashboard Ops |
| `/ops/queue` | `OpsQueuePage` |
| `/ops/order-items` | lista Ops |
| `/ops/order-items/:itemId` | detalhe Ops |
| `/catalog`, `/catalog/:productId` | catalogo |
| `/buyer/catalog`, `/buyer/catalog/:productId` | `Navigate` para `/catalog...` |
| `/seller/offers` | lista de ofertas |
| `/seller/offers/new` | nova oferta |
| `/seller/offers/:offerId` | detalhe/edicao |

`roleHomePath`: buyer `/catalog`, seller `/seller`, ops `/ops`.

Nav PT-BR:

- Buyer: Inicio `/buyer`, Catalogo `/catalog`, Meus pedidos `/buyer/orders`
- Seller: Inicio `/seller`, Catalogo `/catalog`, Pedidos `/seller/orders`,
  Minhas ofertas `/seller/offers`
- Ops: Inicio `/ops`, Catalogo `/catalog`, Fila `/ops/queue`,
  Pedidos `/ops/order-items`

Deep links de Notification nao mudam.

---

## 7. Estados

Loading (`Spinner`), error (`ErrorState` + retry), empty por bloco no
Dashboard (nao esconder a pagina se so Recent estiver vazio). Mutacoes
(cancel, CRUD, 409) mostram erro inline e desabilitam o botao enquanto
pendente.

---

## 8. Criterios de aceite

1. Login Buyer cai no catalogo; Seller e Ops no Dashboard.
2. Cada papel ve so o bloco da propria `role` da API.
3. Deep link de status/prioridade preenche o filtro da lista.
4. Seller/Ops veem o catalogo sem botao Comprar.
5. Buyer cancela item `placed`/`preparing` e nao ve o botao em `in_transit`.
6. Ops lista Order Items sem conversa aberta e ve o historico de conversas
   do item, sem Messages.
7. Seller lista, cria, edita e exclui ofertas (e produtos); 409 nao quebra
   a tela.
8. Fechar e reabrir a pagina preserva o estado real vindo da API.

---

## 9. Testes

- Unit: labels do status de Order do Buyer; `canBuyerCancel`; preco minimo
  do card.
- `DashboardPage`: empty Seller/Buyer/Ops; preview Ops linka
  `conversation_id`; Buyer nao renderiza fila.
- Catalogo: card com preco minimo; Seller autenticado sem Comprar.
- Listas: filtro inicial da query string.
- `AppRouter`: homes; `/ops/queue` ainda e a fila.
- Buyer cancel: botao so em `placed`/`preparing`.
- Ops detalhe: historico de conversas, sem Messages.
- Ofertas: lista chamada com `seller_id`; 409 de delete.

---

## 10. Definition of Done (F7)

- `npm run lint`, `npm run test`, `tsc -b` e `npm run build` limpos.
- Backend sem alteracoes nesta fase.
- Validado no browser nos tres papeis (desktop e ~400px).
- `docs/CURRENT_STATE.md` atualizado (fase F7 no frontend; UI do Dashboard
  sai de "O que ainda nao existe").

---

## 11. Instrucoes para implementacao (Cursor)

1. Escrever este spec e acrescentar F7 em `FRONTEND_IMPLEMENTATION_PLAN.md`.
2. `lib/auth/role.ts`, `app/layout/nav.ts` (labels PT-BR, `end` no Inicio),
   `AppRouter.tsx`.
3. `types/dashboard.ts` + `features/dashboard/` (`api.ts`, `copy.ts`,
   `DashboardPage.tsx`, views). Uma `GET /dashboard`.
4. Catalogo em `/catalog`; `PurchasePanel` gated; filtro disponiveis.
5. `useSearchParams` em Seller orders e Ops queue.
6. `canBuyerCancel` + acao de cancel no detalhe do Buyer;
   `cancelOrderItem` em `features/orders/api.ts` (Seller reexporta).
7. `types/ops.ts` + lista/detalhe Ops de Order Items;
   `fetchOpsItemConversations`.
8. `features/seller-offers/` + mutacoes em `features/catalog/api.ts`
   (`fetchOffers` aceita `sellerId`; `GET /offers/{id}`).
9. Testes, lint/build, `CURRENT_STATE.md`, validar no browser.

# Market Hub — F2 — Seller Orders (Spec)

Deriva de `docs/FRONTEND_IMPLEMENTATION_PLAN.md`. Assume F0 (fundação) e F1
(Buyer Catalog + Purchase) prontos e validados no browser.

---

## 1. Objetivo

Primeira jornada operacional do Seller: consultar, buscar, filtrar e paginar
os próprios Order Items, e acessar o detalhe de um item.

## 2. Contexto (verificado no backend nesta sessão)

Nenhum gap de contrato encontrado para o F2 — `GET /v1/order-items` e
`GET /v1/order-items/{item_id}` já cobrem tudo que o escopo pede. Nenhuma
mudança de backend nesta fase.

- `GET /v1/order-items` (só Seller autenticado; Buyer/Ops recebem `403`):
  parâmetros `page`, `page_size` (padrão 20, máx. 100), `status`, `from`,
  `to`, `order_item_id`. Ordena `created_at DESC` — fixo, sem controle de
  ordenação na UI. Envelope `{items, page, page_size, total}`.
- `order_item_id` é **igualdade exata de UUID**, não busca parcial por
  texto. A "busca por identificador" do plano é, na prática, colar o UUID
  completo do item — não um `LIKE`/fuzzy search (o backend não oferece
  isso). Documentar isso na UI (placeholder do campo).
- `GET /v1/order-items/{item_id}`: detalhe do item no escopo do Seller
  (`product{id,name,description}`, `buyer{id,name}`, `order{id,created_at}`,
  `offer_id`, `quantity`, `purchase_price`, `status`, `created_at`,
  `updated_at`). Item de outro Seller responde `404`.
- Ambas as rotas já existiam antes da F0/F1 e têm cobertura de teste no
  backend (`tests/integration/test_seller_order_items.py`).

## 3. Escopo

### Orders List (`/seller/orders`)

- Lista paginada dos Order Items do Seller autenticado.
- Filtros: status (select com os 5 valores + "todos"), período (`from`/
  `to`), busca por `order_item_id` (UUID exato).
- Paginação com `page`/`page_size` (fixo em 20); mudar filtro volta para a
  página 1.
- Cada linha mostra: id curto, produto, buyer, quantidade, preço, status,
  data; navega para o detalhe.
- Loading/empty (`Nenhum item encontrado.`)/error com retry.

### Order Item detail (`/seller/orders/:itemId`)

- Somente leitura nesta fase: produto (nome + descrição), buyer, pedido,
  quantidade, preço histórico, status, datas.
- **Fora de escopo aqui, entra na F3**: atualização de status, cancelamento,
  Conversation, Internal Comment. A tela mostra uma nota indicando que essas
  ações chegam na próxima fase — não simular nem desenhar esses controles
  desabilitados.

## 4. Fora de escopo (explícito)

- Qualquer ação de mutação sobre o Order Item (status, cancelamento).
- Conversation / Internal Comment (F3).
- Ordenação customizável (a API só ordena por `created_at DESC`).
- Busca textual por nome de produto/buyer (a API não oferece; só
  `order_item_id` exato).

## 5. Rotas

```text
/seller/orders               (Orders List)
/seller/orders/:itemId       (Order Item detail, somente leitura)
```

`roleHomePath('seller')` passa a apontar para `/seller/orders`. O item de
nav "Orders" do seller deixa de estar desabilitado.

## 6. Estrutura

Nova feature `features/seller-orders/` (api + `SellerOrdersListPage` +
`SellerOrderItemDetailPage`), sem duplicar o que já existe: reaproveita
`OrderItemStatus`/`ORDER_ITEM_STATUS_LABELS` de `features/orders/status.ts`
e um novo `components/ui/StatusBadge.tsx` compartilhado (extraído do que já
existia inline em `features/orders/OrderItemsTable.tsx`, sem mudar
comportamento do F1).

## 7. Estados

- Loading: spinner na lista e no detalhe.
- Empty: lista sem itens (após filtro ou não) mostra
  `Nenhum item encontrado.`.
- Error: `ErrorState` com retry em lista e detalhe.
- Filtro/paginação não têm "mutation feedback" (são leitura), só re-fetch
  com loading.

## 8. Critérios de aceite

1. Seller autenticado vê os próprios Order Items paginados, mais recentes
   primeiro.
2. Filtrar por status reduz a lista corretamente; limpar o filtro volta ao
   total.
3. Buscar por um `order_item_id` exato retorna só aquele item (ou vazio se
   não existir/for de outro Seller).
4. Clicar num item navega para o detalhe e mostra os dados corretos
   (produto, buyer, pedido, preço, status).
5. Buyer/Ops autenticados não veem "Orders" no nav do Seller (nav já é por
   papel) — não há necessidade de bloquear a rota além do que a guarda da F0
   já garante.

## 9. Testes

- Unit: helper de querystring dos filtros (monta `page`/`status`/`from`/
  `to`/`order_item_id` só com os parâmetros presentes).
- Component: lista renderiza itens e paginação; filtro de status refaz a
  busca; `StatusBadge` usado tanto no F1 (Buyer) quanto no F2 (Seller) sem
  regressão.

## 10. Definition of Done (F2)

- As 2 telas navegáveis e funcionais contra a API local.
- `npm run lint`, `npm run test`, `tsc -b` e `npm run build` limpos.
- Backend: `uv run pytest` e `ruff` continuam limpos (não deve haver
  mudança de backend nesta fase; se precisar, é um sinal de que o escopo
  saiu do previsto e deve ser perguntado antes).
- Validado manualmente no browser pelo usuário.

## 11. Instruções para implementação (Cursor)

1. `types/order.ts`: adicionar `SellerOrderItemListItem`,
   `SellerOrderItemListResponse`, `SellerOrderItemDetail`, `BuyerSummary`.
2. `components/ui/StatusBadge.tsx`: extrair de
   `features/orders/OrderItemsTable.tsx` (Buyer/F1) sem mudar o HTML/CSS
   resultante — é refactor de reuso, não mudança de comportamento.
3. `features/seller-orders/api.ts`, `SellerOrdersListPage.tsx`,
   `SellerOrderItemDetailPage.tsx`.
4. Atualizar `lib/auth/role.ts` e `app/layout/nav.ts` para o Seller.
5. Não tocar em `features/catalog`, `features/orders` (Buyer) além da
   extração do `StatusBadge`, nem em `app/router`/`app/providers` além de
   registrar as duas rotas novas.

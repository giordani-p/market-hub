# Market Hub — F1 — Buyer Catalog + Purchase (Spec)

Deriva de `docs/FRONTEND_IMPLEMENTATION_PLAN.md`. Assume a fundação da F0
pronta (auth, router, layout, cliente HTTP, componentes compartilhados).

---

## 1. Objetivo

Construir a jornada do Buyer: descobrir um produto, escolher uma oferta e
criar um pedido — e acompanhar os pedidos criados.

## 2. Contexto (verificado no backend nesta sessão)

- `GET /v1/products` e `GET /v1/offers` são públicos (sem auth) e **não têm
  busca/filtro por texto nem paginação** — retornam array completo. A busca
  do Catalog é client-side sobre a lista carregada; aceitável no volume atual
  de seed. `GET /v1/offers` só filtra por `?seller_id=`, não por
  `product_id` — a tela de produto filtra as ofertas client-side pelo
  `product_id` já carregado.
- Checkout (`POST /v1/orders`) aceita uma lista de itens, mas **carrinho não
  é persistido no backend** — decisão do usuário (2026-09-13): F1 implementa
  fluxo "comprar agora" (uma oferta e quantidade por vez → um pedido por
  compra), não um carrinho multi-produto. Pode evoluir depois se fizer
  falta.
- Gap de contrato corrigido nesta sessão: `OrderItemResponse` não trazia
  produto. Agora `GET /v1/orders` e `GET /v1/orders/{id}` retornam
  `Order.items` como `BuyerOrderItem` (inclui `product: {id, name}`) — ver
  `app/orders/schemas.py` e `api/openapi.yaml`. Isso é o que a tela de
  acompanhamento de pedidos consome.
- Erro de negócio (`{code, message}`) é uniforme, exceto `checkout_rejected`,
  que também traz `items: [{offer_id, reason, expected_price, current_price,
  available, stock}]` — precisa ser tratado à parte para mostrar o motivo de
  cada item rejeitado (`not_found`, `unavailable`, `insufficient_stock`,
  `price_changed`).
- `expected_price` enviado no checkout deve ser o preço da oferta como
  exibido na tela no momento da compra (string decimal, ex.: `"299.00"`).
- Sem cadastro de Buyer: login usa os usuários de seed (`Buyer Demo`).

## 3. Escopo

### Catalog (`/buyer/catalog`)

- Lista todos os produtos (`GET /v1/products`).
- Busca client-side por nome (filtra a lista já carregada).
- Loading/empty (`Nenhum produto encontrado.`)/error com retry.
- Cada card navega para o detalhe do produto.

### Product detail (`/buyer/catalog/:productId`)

- `GET /v1/products/{id}` para nome/descrição.
- `GET /v1/offers` (client-side filtrado por `product_id`) para as ofertas
  disponíveis: preço, estoque, `available`.
- Ofertas indisponíveis (`available: false` ou `stock: 0`) aparecem
  desabilitadas, sem opção de compra.
- Loading/empty (`Nenhuma oferta disponível para este produto.`)/error.

### Purchase (dentro do Product detail)

- Selecionar uma oferta disponível.
- Selecionar quantidade (`1..stock`, input numérico simples).
- Confirmar compra → `POST /v1/orders` com um item
  (`offer_id`, `quantity`, `expected_price` = preço atual exibido).
- Sucesso (`201`): feedback de sucesso + navegação para
  `/buyer/orders/:orderId` do pedido criado.
- Falha (`409 checkout_rejected`): mostrar o motivo do item rejeitado
  (mapear `reason` para mensagem legível) sem sair da tela; permitir tentar
  de novo.
- Estado de "processando" no botão de compra enquanto a chamada está em voo.

### My Orders (`/buyer/orders`)

- `GET /v1/orders`: lista os pedidos do Buyer autenticado, mais recentes
  primeiro (a API já ordena por `created_at`; frontend não reordena).
- Cada pedido mostra id curto, data e itens (produto, quantidade, preço,
  status).
- Loading/empty (`Você ainda não fez nenhum pedido.`)/error.
- Cada pedido navega para o detalhe.

### Order detail (`/buyer/orders/:orderId`)

- `GET /v1/orders/{id}`: mesmos dados do item da lista, para um pedido só.
- Reflete o `status` de cada Order Item exatamente como veio da API — sem
  recalcular nem inferir transição.

## 4. Fora de escopo (explícito)

- Comunicação (Conversation/Internal Comment) do Buyer — não está no roteiro
  de nenhuma fase deste plano; não implementar agora.
- Carrinho persistido ou multi-produto por pedido.
- Cancelamento de Order Item pelo Buyer (o contrato permite, mas não está no
  escopo do F1 — entra se/quando o roadmap pedir).
- CRUD de Produto/Oferta (visão do Seller) — isso é F2+.
- Notificações — F5.

## 5. Rotas

```text
/buyer/catalog                 (Catalog)
/buyer/catalog/:productId      (Product detail + Purchase)
/buyer/orders                  (My Orders)
/buyer/orders/:orderId         (Order detail)
```

`roleHomePath('buyer')` passa a apontar para `/buyer/catalog`. Os itens de
nav "Catalog" e "My Orders" do buyer deixam de estar desabilitados.

## 6. Estados

- Loading: spinner ao carregar lista/detalhe.
- Empty: mensagens específicas por tela (catalog vazio, sem ofertas, sem
  pedidos).
- Error: `ErrorState` com retry manual (refetch) em toda tela que busca
  dado.
- Mutation feedback: botão de compra mostra "Comprando..." e desabilita
  durante a chamada; erro de checkout aparece inline, sem navegação.

## 7. Critérios de aceite

1. Buyer navega Catalog → Product → escolhe oferta e quantidade → compra →
   cai no detalhe do pedido criado, com o produto certo e `status: placed`.
2. Comprar mais que o estoque disponível é bloqueado no cliente (quantidade
   máxima = `stock`) e, se ainda assim falhar no backend, mostra o motivo
   sem quebrar a tela.
3. `My Orders` lista todos os pedidos do Buyer autenticado com produto e
   preço corretos (valida o `BuyerOrderItem` novo).
4. Nenhuma tela desta fase é acessível por Seller/Ops (o nav já esconde os
   itens; navegação direta por URL não precisa bloquear além do que a rota
   protegida da F0 já garante — role não é revalidado por tela nesta fase).
5. Todas as chamadas HTTP passam pelo `lib/api/client` existente; nenhum
   `fetch` direto nas telas.

## 8. Testes

- Unit: normalização do erro `checkout_rejected` (com `items`).
- Component: fluxo de compra (seleção de oferta, limite de quantidade,
  sucesso e erro de checkout); lista de pedidos renderiza produto/preço.

## 9. Definition of Done (F1)

- As 4 telas navegáveis e funcionais contra a API local.
- `npm run lint`, `npm run test` e `tsc -b` limpos.
- Validado manualmente no browser (login → catálogo → compra → pedido).

## 10. Instruções para implementação (Cursor)

1. `features/catalog/` (api + `ProductListPage` + `ProductDetailPage`) e
   `features/orders/` (api + `OrdersListPage` + `OrderDetailPage`,
   `PurchasePanel` dentro do detail de produto).
2. Tipos em `types/catalog.ts` (`Product`, `Offer`) e `types/order.ts`
   (`BuyerOrderItem`, `Order`, `CheckoutItem`, `CheckoutRejectedItem`).
3. Estender `ApiError`/`normalizeErrorBody` para carregar o corpo bruto do
   erro (`details`) quando houver campos além de `code`/`message` — usado
   pelo `checkout_rejected`.
4. Atualizar `lib/auth/role.ts` (`roleHomePath`) e `app/layout/nav.ts` para
   apontar Buyer para `/buyer/catalog` e `/buyer/orders`.
5. Não tocar em `features/auth`, `app/router` (guarda de rota) ou
   `app/providers` além do necessário para registrar as novas rotas.

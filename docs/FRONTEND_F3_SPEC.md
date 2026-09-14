# Market Hub — F3 — Order Item + Communication (Spec)

Deriva de `docs/FRONTEND_IMPLEMENTATION_PLAN.md`. Assume F0–F2 prontos e
validados no browser.

---

## 1. Objetivo

Transformar o Order Item do Seller (hoje só leitura, do F2) no centro da
operação: avançar/cancelar status, conversar com o Buyer e usar o suporte
interno com a Ops — tudo no mesmo lugar.

## 2. Contexto (verificado no backend nesta sessão)

Sem gaps de contrato — `PATCH /v1/order-items/{id}`, `POST .../cancel`,
`POST/GET .../conversation(s)`, `GET/POST /v1/conversations/{id}` +
`/messages`, e `GET/POST /v1/order-items/{id}/internal-comments` já cobrem
tudo. Nenhuma mudança de backend nesta fase.

- Transição de status é sempre **um passo à frente**:
  `placed → preparing → in_transit → delivered` (`app/orders/status.py`,
  `FORWARD`). Não existe "pular" status; a UI oferece só o próximo, nunca um
  seletor livre. `PATCH` com o mesmo status é idempotente; com qualquer
  outro que não seja o próximo, `409 invalid_transition`.
- Cancelamento do Seller é permitido em `placed`/`preparing`/`in_transit`
  (não em `delivered`/`cancelled`). Cancelar duas vezes é idempotente.
- Conversation: no máximo uma `open` por Order Item. `POST
  .../conversation` cria ou reaproveita a aberta. Fechar
  (`POST .../close`) é exclusivo do Seller.
- Messages: janela de 24h. Sem `before`, retorna as últimas 24h. Com
  `before`, retorna a janela anterior a essa data. `has_older` indica se há
  mais histórico para carregar — "carregar mais antigas" pagina com
  `before = created_at` da mensagem mais antiga carregada.
- `MessageResponse.author_type` é `buyer`/`seller`/`system` — usar isso para
  diferenciar quem enviou, nunca inferir pelo conteúdo.
- Internal Comment é **outro recurso**, independente de Conversation, entre
  Seller e Ops no mesmo Order Item. `author_type` é `ops`/`seller`.
- Enviar mensagem ou comentário em `Conversation`/Order Item fechado/errado
  responde `404`/`409` conforme o caso — tratar como erro de mutação comum.

## 3. Escopo

### Status (na tela de detalhe do F2)

- Botão "Avançar para `<próximo status>`" quando existir próximo válido
  (`FORWARD[status]`); some quando o item está `delivered`/`cancelled`.
- Botão "Cancelar pedido" quando `can_cancel` permitir pelo status atual;
  pede confirmação inline antes de enviar.
- Erro de transição (`409 invalid_transition`) exibido inline, sem navegar.

### Conversation

- Ao entrar no Order Item, buscar conversas (`GET
  .../conversations`) e identificar a `open`, se houver.
- Sem conversa aberta: formulário mínimo para abrir uma (motivo —
  `ConversationReason`) → `POST .../conversation`.
- Com conversa aberta ou selecionada: histórico de mensagens (24h),
  "Carregar mais antigas" quando `has_older`, campo de envio de mensagem,
  botão "Encerrar conversa" (Seller).
- Mensagens do Buyer, do Seller e do sistema (fechamento por inatividade)
  visualmente distintas entre si (autor claro em cada bolha).

### Internal Support

- Lista de Internal Comments do item (Seller ↔ Ops) e campo para criar um
  novo.
- Visualmente **separado** da Conversation — layout, cor e posição
  diferentes o bastante para nunca ser confundido com mensagem do Buyer.
  Esse é requisito explícito do plano, não só polimento.

## 4. Fora de escopo (explícito)

- Qualquer coisa do lado Ops (`/v1/ops/*`) — isso é F4.
- Prioridade / critical override — F4.
- Notificações in-app — F5.
- Reabrir Conversation fechada (o contrato não permite).

## 5. Direção visual (aplicando a skill `frontend-design`)

Este é um painel operacional, não uma landing page — a "personalidade" vem
da clareza hierárquica, não de decoração. Duas decisões deliberadas:

- **Conversation** como thread de chat (bolhas alinhadas à direita para o
  Seller, à esquerda para o Buyer, mensagens de sistema centralizadas e
  discretas) — o padrão mental de "conversa" que qualquer usuário já
  reconhece.
- **Internal Support** como um painel com tom visualmente "de bastidor"
  (fundo levemente diferenciado, sem parecer chat) — reforça que é um canal
  interno, não a conversa com o cliente. Nada de reaproveitar o componente
  de bolha de chat aqui.

Evitar: rótulos em CAIXA ALTA, cards idênticos com sombra genérica em tudo,
setas decorativas em botões. Manter a paleta do Mercado Livre já definida
(amarelo de marca como acento pontual, azul para ação primária).

## 6. Rotas

Sem rotas novas — tudo dentro de `/seller/orders/:itemId`, que passa a
compor `StatusActions` + `ConversationPanel` + `InternalCommentsPanel`
abaixo do que o F2 já mostra.

## 7. Estados

- Cada painel (status, conversation, internal support) tem seu próprio
  loading/error/empty independente — uma falha em um não deve travar os
  outros.
- Empty da Conversation: `Nenhuma conversa neste pedido ainda.` com o
  formulário de abertura.
- Empty do Internal Support: `Nenhum comentário interno ainda.`
- Mutation feedback: enviar mensagem/comentário, avançar status, cancelar e
  encerrar conversa mostram estado "enviando/processando" e desabilitam a
  ação repetida.

## 8. Critérios de aceite

1. Seller avança o status de um item passo a passo e o cancela quando
   permitido; tentativa inválida não quebra a tela.
2. Seller abre uma conversa, troca mensagens, carrega histórico mais antigo
   e encerra a conversa.
3. Seller registra e lê Internal Comments, visualmente distintos da
   conversa com o Buyer.
4. Fechar e reabrir a página preserva o estado real vindo da API (nada de
   estado otimista permanente sem confirmação do backend).

## 9. Testes

- Unit: helper de transição de status (próximo status esperado por status
  atual); normalização de erro de transição inválida.
- Component: `StatusActions` (mostra/esconde ações certas por status);
  `ConversationPanel` (abrir conversa, enviar mensagem, carregar mais
  antigas, encerrar); `InternalCommentsPanel` (listar e criar).

## 10. Definition of Done (F3)

- `npm run lint`, `npm run test`, `tsc -b` e `npm run build` limpos.
- Backend sem alterações nesta fase.
- Validado manualmente no browser pelo usuário.

## 11. Instruções para implementação (Cursor)

1. `features/conversations/` (api + `ConversationPanel.tsx`, reaproveitável
   depois pela Ops no F4) e `features/support/` (api +
   `InternalCommentsPanel.tsx`, mesmo racional).
2. `features/seller-orders/StatusActions.tsx` para avançar/cancelar,
   consumindo `PATCH`/`cancel` já usados hoje só implicitamente.
3. Compor tudo em `SellerOrderItemDetailPage.tsx` existente — não recriar a
   página.
4. Tipos novos em `types/conversation.ts` e `types/support.ts`.
5. Não tocar em `features/catalog`, `features/orders` (Buyer) nem nas rotas
   do Buyer/Ops.

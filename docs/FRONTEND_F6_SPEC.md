# Market Hub — F6 — Design Review + UX Polish + Notification Copy (Spec)

Deriva de `docs/FRONTEND_IMPLEMENTATION_PLAN.md` (secao 11, "F6 — UX Polish +
Integration"), ampliado por pedido direto do usuario em 2026-09-14: revisar
o design de toda a aplicacao contra a skill `frontend-design-patterns` e
melhorar a copy das Notifications. Assume F0-F5 prontos, validados no
browser e mergeados na main.

---

## 1. Objetivo

Tres frentes, sem mudar contrato de backend nem adicionar tela nova:

1. Revisar e ajustar **todas** as telas ja construidas (F0-F5) contra a
   skill de projeto `frontend-design-patterns` — paleta, tipografia,
   espacamento, estados, acessibilidade, responsivo — usando a skill
   `frontend-design-review` como metodo de auditoria.
2. Trocar a copy das Notifications (hoje `title`/`message` do backend, em
   ingles, sem tradução no frontend) por mensagens amigaveis em portugues,
   montadas no frontend a partir de `type` + `metadata`.
3. Remover o dark mode automatico (`prefers-color-scheme: dark`) — a
   skill `frontend-design-patterns` (e o Mercado Livre real) so define
   paleta clara; o app passa a renderizar sempre no tema claro,
   independente da preferencia do SO/browser.

## 2. Contexto e decisoes tomadas nesta sessao

- **Gap de arquitetura encontrado no F5, resolvido agora**: o
  `FRONTEND_IMPLEMENTATION_PLAN.md` diz "o frontend nao deve reconstruir
  titulos ou mensagens de negocio quando esses dados forem fornecidos pelo
  backend" — regra que o F5 seguiu ao pe da letra pra Notification. Mas
  **todo o resto do app ja faz o oposto**: o backend devolve enum cru
  (`preparing`, `high`, `atraso`...) e o **frontend** traduz pra rotulo em
  PT-BR (`ORDER_ITEM_STATUS_LABELS`, `PRIORITY_LABELS`,
  `CONVERSATION_REASON_LABELS`, todos ja existentes). Notification era o
  unico caso em que o backend mandava a frase pronta, em ingles. **Decisao
  do usuario**: alinhar Notification ao padrao do resto do app — o
  frontend monta `title`/`message` a partir de `type` + `metadata`,
  reaproveitando os labels que ja existem. `title`/`message` do backend
  deixam de ser exibidos (nenhuma mudanca de contrato — o backend continua
  mandando os dois, so que o frontend ignora e monta a propria copy).
- **Decisao do usuario**: adicionar uma biblioteca de icones
  (`lucide-react`, outline, stroke consistente — a mesma familia visual
  que a skill sugere) no lugar dos emoji crus usados hoje (`🔔` no sino).
  Unica dependencia nova desta fase.
- **Decisao do usuario**: remover o dark mode automatico. O app tinha
  `color-scheme: light dark` e um bloco `@media (prefers-color-scheme:
  dark)` inteiro em `global.css`, gerado numa fase anterior sem pedido
  explicito — a skill nunca definiu paleta escura, e o usuario apontou
  que ficar trocando de tema sozinho, sem visual pensado pra isso, fere
  boas praticas de UX. Passa a ser tema unico (claro), igual ao Mercado
  Livre real.
- Escopo do F6 no plano original (`FRONTEND_IMPLEMENTATION_PLAN.md`
  secao 11) ja cobria UX/acessibilidade/responsivo/integracao — este spec
  absorve e detalha isso, sem remover nada do que ja estava previsto.

## 3. Telas e componentes no escopo da revisao

Todo o frontend construido ate aqui, nenhuma tela fica de fora:

| Area              | Arquivos |
| ----------------- | -------- |
| Auth              | `LoginPage` |
| Buyer             | `ProductListPage`, `ProductDetailPage`, `PurchasePanel`, `OrdersListPage`, `OrderDetailPage`, `BuyerOrderItemDetailPage`, `OrderItemsTable` |
| Seller            | `SellerOrdersListPage`, `SellerOrderItemDetailPage`, `StatusActions` |
| Ops               | `OpsQueuePage`, `OpsConversationDetailPage`, `PriorityActions` |
| Comunicacao       | `ConversationPanel`, `InternalCommentsPanel` |
| Notifications     | `NotificationBell` |
| Layout/navegacao  | `AppLayout`, `NotFoundPage` |
| UI compartilhado  | `Button`, `Input`, `Card`, `StatusBadge`, `PriorityBadge`, `EmptyState`, `ErrorState`, `Spinner` |

## 4. Escopo

### 4.1 Design review (skill `frontend-design-review` + `frontend-design-patterns`)

Pra cada area da tabela acima, revisar contra a skill e corrigir o que
divergir. Achados ja identificados nesta sessao, pra usar como ponto de
partida (nao a lista final — a revisao pode achar mais):

- **Tipografia**: `global.css` usa
  `system-ui, -apple-system, 'Segoe UI', sans-serif`; a skill pede
  `"Proxima Nova", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
  Arial, sans-serif`. Alinhar a stack.
- **Paleta**: os tokens atuais (`--color-primary`, `--color-brand`,
  `--color-success`, `--color-danger`, `--color-warning`) ja batem em
  valor com a maior parte da paleta da skill (`--color-action-primary
  #3483FA`, `--color-brand-yellow #FFE600`, `--color-success #00A650`,
  `--color-warning #A6600A`), **exceto** `--color-danger` (`#E53935`) vs
  `--color-error` da skill (`#F23D4F`) — decidir se alinha o hex ou
  mantem (motivo documentado se mantiver). Nao renomear as variáveis
  (churn grande, sem ganho visual) — so os valores.
- **Sombra em vez de borda**: `.notification-dropdown` (do F5) usa
  `box-shadow: 0 8px 24px ...`; a skill diz "preferir bordas e diferencas
  de superficie a sombras". Trocar por borda + leve diferenca de
  superficie.
- **Espacamento e radius**: escala atual (`0.25/0.5/0.75/1/1.5/2rem` e
  radius `6px`/`8px`/`999px`) ja bate com a escala da skill
  (`4/8/12/16/24/32...` e `6px` controles, `8px` cards, `999px` pills) —
  confirmar que nada foge disso ao revisar, sem refatorar o que ja esta
  certo.
- **Largura de tela operacional**: `.page-wide` (`1100px`) usado em
  `SellerOrderItemDetailPage`/`BuyerOrderItemDetailPage`/Ops — a skill
  permite telas operacionais mais largas quando a densidade justificar;
  avaliar se `OpsQueuePage` (tabela densa) se beneficia de mais largura.
- **Icones**: trocar `🔔` (unico emoji hoje) por `lucide-react`; ao
  revisar cada tela, usar a tabela de icones sugerida da skill (Search,
  Bell, MessageCircle, LifeBuoy, SlidersHorizontal, CheckCircle, XCircle,
  AlertTriangle) onde fizer sentido — sem inventar icone pra tudo.
- **Empty/Error/Loading**: os tres ja existem em toda tela (`EmptyState`,
  `ErrorState`, `Spinner`); revisar se a mensagem de cada uma e humana e
  com proxima acao quando fizer sentido (regra da skill secao 16),
  nao so texto generico.
- **Acessibilidade**: navegacao por teclado, foco visivel (`:focus-visible`
  ja existe globalmente — conferir que nenhum componente novo o
  sobrescreve), contraste dos tokens de cor, `aria-label` em botoes so-icone.
- **Responsivo**: `SellerOrdersListPage`/`OpsQueuePage` usam `.order-list`
  (cards) — ja funciona em mobile; `OpsQueuePage`/filtros com varios
  `Input` em linha (`.filters`) — conferir quebra em telas estreitas.

### 4.2 Notification copy em PT-BR

Novo `features/notifications/copy.ts`, puro (`type` + `metadata` ->
`{ title, message }`), reaproveitando os labels que ja existem
(`ORDER_ITEM_STATUS_LABELS`, `PRIORITY_LABELS`). Mapeamento:

| `type`                          | Copy |
| ------------------------------- | ---- |
| `ORDER_ITEM_STATUS_CHANGED`, `new_status = delivered` | "Pedido entregue" / "Seu pedido foi entregue." |
| `ORDER_ITEM_STATUS_CHANGED`, `new_status = cancelled` | "Pedido cancelado" / "Seu pedido foi cancelado." |
| `ORDER_ITEM_STATUS_CHANGED`, outro `new_status`       | "Status do pedido atualizado" / `Seu pedido agora esta "{label}".` |
| `CONVERSATION_STATUS_CHANGED`                          | "Conversa encerrada" / "A conversa sobre este pedido foi encerrada." |
| `CONVERSATION_PRIORITY_CHANGED`, `new_status = critical` | "Prioridade critica" / "Uma conversa foi marcada como prioridade critica." |
| `CONVERSATION_PRIORITY_CHANGED`, outro `new_status`      | "Prioridade atualizada" / `A prioridade da conversa mudou para "{label}".` |

`NotificationBell` passa a chamar `buildNotificationCopy(notification)` em
vez de exibir `notification.title`/`notification.message` diretamente.
Sem fallback pro texto em ingles do backend — se `type` for desconhecido
(nao deveria acontecer, mas por seguranca), usar um texto generico
("Voce tem uma atualizacao.") em vez do texto cru do backend.

### 4.3 Remover o dark mode

- `global.css`: apagar o bloco `@media (prefers-color-scheme: dark) {
  :root { ... } }` inteiro; trocar `color-scheme: light dark` por
  `color-scheme: light` no `:root` (isso tambem para o browser de
  escurecer sozinho os controles nativos de formulario).
- Os tokens derivados (`--color-bubble-mine-bg`, `--color-support-bg`,
  etc., no segundo bloco `:root`) usam `color-mix()` em cima dos tokens
  base — conferem que continuam corretos so com o tema claro (devem
  continuar, ja que so dependem dos valores base, nao de um bloco dark
  em separado).
- Revisar visualmente cada tela da secao 3 renderizada com o SO/browser
  em modo escuro, pra confirmar que nada mais no app reage a
  `prefers-color-scheme` (nenhum outro CSS ou lib deveria, mas e a
  validacao final do item).

## 5. Fora de escopo (explicito)

- Qualquer mudanca de contrato de backend (nenhuma rota, schema ou regra
  muda nesta fase).
- Tela nova, fluxo novo ou campo novo de produto — so revisao visual/UX
  do que ja existe.
- Busca global no header (a skill sugere um campo de busca no header;
  cada tela ja tem sua propria busca/filtro — nao criar uma busca global
  nesta fase, e um escopo novo, nao pedido).
- Toggle manual de tema claro/escuro — decisao foi remover o dark mode,
  nao substituir por um seletor.

## 6. Rotas

Nenhuma nova.

## 7. Criterios de aceite

1. Todas as telas da tabela da secao 3 revisadas contra a skill; cada
   divergencia encontrada (alem das ja listadas na secao 4.1) documentada
   e corrigida ou justificada.
2. `lucide-react` instalado e usado pelo menos no sino de notificacoes;
   nenhum emoji cru sobrando onde um icone da lib fizer mais sentido.
3. Notification exibe titulo/mensagem em portugues, humanos, sem nenhum
   texto cru do backend aparecendo na tela.
4. Navegacao por teclado e foco visivel funcionam em todas as telas
   revisadas; sem estado comunicado so por cor.
5. Nenhuma tela quebra em ~400px de largura.
6. App renderiza sempre no tema claro, mesmo com o SO/browser em modo
   escuro — nenhum `@media (prefers-color-scheme: dark)` restante.
7. Journeys completas validadas pelo usuario: Buyer (login -> catalogo ->
   compra -> acompanhar pedido -> conversa), Seller (login -> orders ->
   item -> status -> conversa -> suporte interno -> notificacao), Ops
   (login -> fila -> conversa -> prioridade -> suporte interno ->
   notificacao).

## 8. Testes

- Unit: `buildNotificationCopy` (uma combinacao por linha da tabela da
  secao 4.2, mais o caso de `type` desconhecido).
- Component: `NotificationBell` atualizado pra afirmar a copy em
  portugues (os testes existentes usavam `title`/`message` do fixture
  diretamente — ajustar pra refletir a copy montada).
- Nenhum teste de backend muda (sem mudanca de contrato).

## 9. Definition of Done (F6)

- `npm run lint`, `npm run test`, `tsc -b` e `npm run build` limpos.
- Backend sem alteracoes nesta fase.
- Validado manualmente no browser pelo usuario, nos tres papeis, em
  desktop e em largura de mobile (~400px).

## 10. Instrucoes para implementacao (Cursor)

1. `npm install lucide-react` (unica dependencia nova).
2. `features/notifications/copy.ts` + `copy.test.ts` (tabela da secao
   4.2); `NotificationBell.tsx` passa a usar a copy montada.
3. Ajustar `global.css`: remover o bloco `@media (prefers-color-scheme:
   dark)` e trocar `color-scheme: light dark` por `color-scheme: light`
   (secao 4.3); font-family stack; `.notification-dropdown` (borda em vez
   de sombra); qualquer token de cor alinhado na secao 4.1.
4. Revisar tela por tela da secao 3, na ordem: UI compartilhada primeiro
   (`Button`/`Input`/`Card`/`StatusBadge`/`PriorityBadge`/`EmptyState`/
   `ErrorState`/`Spinner`, ja que tudo depende deles), depois
   `AppLayout`/`NotFoundPage`, depois Auth, Buyer, Seller, Ops,
   Comunicacao.
5. Nenhum arquivo de `app/` (backend) muda nesta fase.

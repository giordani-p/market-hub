# Market Hub — F8 — Refatoracao de UI e Design System (Spec)

Deriva de `docs/FRONTEND_IMPLEMENTATION_PLAN.md` e da skill de projeto
`.cursor/skills/frontend-design-patterns/SKILL.md`. Assume F0-F7 prontos,
validados no browser e mergeados na main. Nenhuma mudanca de contrato de
backend, de rota de UI ou de fluxo de dados nesta fase.

Decisoes tomadas com o autor antes de escrever esta spec:

- **Base de UI**: CSS proprio com sistema de tokens. Nao migrar para Copan
  (`@loft/react-loft`) — pacotes privados, identidade visual da Loft,
  conflita com a paleta inspirada no Mercado Livre e com a skill do projeto.
- **Escopo**: camada visual e design system. Rotas, contratos e fluxo de
  dados permanecem intactos.

---

## 1. Objetivo

Levar o frontend de "funcional com CSS ad-hoc" para "produto de marketplace
com linguagem visual sistematizada", sem tocar em dominio.

Tres resultados, nessa ordem de prioridade:

1. **Sistema** — tokens de espacamento, tipografia, raio, elevacao e
   breakpoint, hoje inexistentes; so cor esta tokenizada.
2. **Densidade e escaneabilidade** — listas operacionais de Seller e Ops
   viram tabelas com cabecalho e alinhamento de valor, como a secao 12 da
   skill ja pede e o codigo ainda nao cumpre.
3. **Confiabilidade percebida** — skeleton no lugar de spinner de pagina
   inteira, feedback pos-acao, responsividade real e acessibilidade
   verificada em todas as telas.

A paleta atual (`--color-primary`, `--color-brand`, semanticas e derivados
de bolha/suporte) e preservada valor a valor. E a parte madura do CSS de
hoje e o unico elemento visual que nao muda.

---

## 2. Contexto (verificado no codigo)

Levantamento sobre `frontend/src` na `main` (commit `d330575`):

| Area | Estado hoje |
|---|---|
| CSS | Arquivo unico `src/styles/global.css`, 905 linhas, seletores por nome de tela (`.ops-queue`, `.support-log`, `.thread-composer`) |
| Tokens | 14 variaveis, todas de cor. Zero token de espaco, fonte, raio, sombra ou breakpoint |
| Shell | `AppLayout.tsx`: header de 3 elementos + sidebar fixa de 200px. Sem busca, sem breadcrumb, sem menu de usuario |
| Primitivos | `Button`, `Card`, `Input`, `StatusBadge`, `PriorityBadge`. `Card` nao aceita props. Select e checkbox sao HTML cru com `className="input"` |
| Listas | Seller/Ops usam `Card` + `.order-item-row` com `<span>` soltos em flex-wrap. Sem cabecalho de coluna, sem alinhamento de valor, sem ordenacao |
| Filtros | `SellerOrdersListPage` e `OpsQueuePage` exigem UUID completo digitado. `ProductListPage` filtra no cliente; as demais no servidor |
| Estados | `Spinner` substitui a pagina inteira; `ErrorState` idem. Sem skeleton, sem toast, sem dialog de confirmacao (usa `.confirm-inline`) |
| Responsivo | 2 media queries em 905 linhas (`720px` e `480px`). Sidebar, filtros e listas nao tem comportamento mobile |
| A11y | `aria-*`/`role` so em `Spinner`, `ErrorState` e mensagens de erro. Sem skip link, sem `aria-current`, sem foco gerenciado na navegacao |
| Copy | "Meus Order Items", "Fila de Ops", "Seller (UUID)" — jargao de dominio na interface |
| Testes | 26 arquivos. Apenas `OpsQueuePage.test.tsx:59` acopla em classe CSS (`.priority-high`) |

Consequencia: o risco de regressao da refatoracao e baixo, porque a suite
consulta por papel e texto acessivel, nao por estrutura.

---

## 3. Principios

1. **Usabilidade antes de semelhanca visual.** Vale a ordem da skill:
   usabilidade, acessibilidade, clareza, consistencia, semelhanca.
2. **Tabela quando a densidade justificar.** Card so agrupa informacao
   relacionada; nao existe por estetica.
3. **Token ou nada.** Nenhum `px`, hex ou `rem` solto em componente novo.
4. **Borda e superficie antes de sombra.** Sombra fica reservada a camadas
   flutuantes — dropdown, toast, dialog, barra fixa.
5. **O frontend nao calcula dominio.** Prioridade, totais e transicoes
   continuam vindo do backend.
6. **PT-BR na interface, ingles no codigo.** Vale a convencao do repo.

---

## 4. Escopo

### 4.1 Sistema de tokens

Quebrar `global.css` em:

```text
src/styles/tokens.css     variaveis (cor preservada + novas escalas)
src/styles/base.css       reset, body, foco, tipografia base, utilitarios
src/styles/global.css     so importa os dois acima
```

Cores: copiadas sem alteracao do arquivo atual.

Novas escalas, seguindo a secao 4 da skill:

```css
/* Espacamento — 4/8/12/16/24/32/48/64 */
--space-1: 0.25rem;  --space-2: 0.5rem;   --space-3: 0.75rem;
--space-4: 1rem;     --space-6: 1.5rem;   --space-8: 2rem;
--space-12: 3rem;    --space-16: 4rem;

/* Tipografia */
--font-size-display: 2.5rem;  --font-size-h1: 2rem;
--font-size-h2: 1.75rem;      --font-size-h3: 1.5rem;
--font-size-h4: 1.25rem;      --font-size-subtitle: 1.125rem;
--font-size-body: 1rem;       --font-size-body-sm: 0.875rem;
--font-size-caption: 0.75rem;
--line-height-tight: 1.25;    --line-height-base: 1.5;
--font-weight-regular: 400;   --font-weight-semibold: 600;
--font-weight-bold: 700;

/* Raio */
--radius-sm: 4px;   --radius-md: 6px;
--radius-lg: 8px;   --radius-pill: 999px;

/* Elevacao — so camada flutuante */
--shadow-dropdown: 0 2px 8px rgb(0 0 0 / 12%);
--shadow-dialog:   0 8px 24px rgb(0 0 0 / 16%);

/* Layout */
--container-max: 1200px;
--container-max-wide: 1440px;
--header-height: 56px;
--sidebar-width: 220px;
```

Breakpoints ficam documentados em comentario no topo de `tokens.css` e
usados de forma uniforme — CSS nativo nao aceita variavel em `@media`:

```text
sm  480px   telefone grande
md  768px   tablet / quebra da sidebar
lg  1024px  desktop
xl  1200px  container maximo
```

### 4.2 Arquitetura de CSS

Migrar de CSS global com seletor por tela para **CSS Modules** (suporte
nativo do Vite, sem dependencia nova). Cada componente carrega seu
`Componente.module.css`; `tokens.css` e `base.css` permanecem globais.

Ganho: fim das colisoes de nome, morte natural de classes orfas e
possibilidade de renomear tela sem caçar seletor no arquivo de 905 linhas.

> Confirmar com o autor antes de F8.1. A alternativa e manter um CSS global
> reorganizado por camada, que custa menos agora e mais a cada tela nova.

### 4.3 Primitivos de UI

`src/components/ui/` passa a conter:

| Componente | Nota |
|---|---|
| `Button` | Adicionar variante `tertiary` (texto/link), tamanhos `sm`/`md`, `loading` com spinner interno e `fullWidth` |
| `Card` | Aceitar `as`, `padding`, `interactive` — hoje nao aceita nenhuma prop |
| `Field` | Wrapper unico de label + hint + erro + `aria-describedby`, usado por todo controle |
| `TextField` | Refatorado sobre `Field` |
| `SelectField` | Novo — hoje e `<select className="input">` cru, sem erro nem hint |
| `SearchField` | Novo — input com icone `Search`, botao de limpar e debounce |
| `Checkbox` / `Radio` | Novos, com area de toque de 44px |
| `Table` | Novo — `Table`, `TableHead`, `TableRow`, `TableCell`, cabecalho fixo, `numeric` para alinhar valor a direita com `tabular-nums`, `sortable` com `aria-sort` |
| `Pagination` | Extrair a duplicacao entre `SellerOrdersListPage` e `OpsQueuePage` |
| `Tabs` | Novo — usado no detalhe de item (Conversa / Suporte interno) no mobile |
| `Dialog` | Novo — confirmacao de acao destrutiva, com foco preso e `Escape` |
| `Toast` + `ToastProvider` | Novo — feedback pos-acao, `role="status"` |
| `Skeleton` | Novo — variantes `text`, `card`, `table-row` |
| `Tag` | Unifica a base visual de `StatusBadge` e `PriorityBadge`, que continuam distintos em vocabulario e cor |
| `Avatar` | Iniciais do usuario, para o menu do header |
| `Tooltip` | Para icone isolado sem rotulo visivel |
| `Breadcrumbs` | Novo — trilha nas telas de detalhe |
| `PageHeader` | Titulo, subtitulo, breadcrumb e slot de acao — hoje cada pagina monta o seu |

Regra: nenhum componente novo alem desta lista sem necessidade demonstrada
por tela existente.

### 4.4 App shell

`AppLayout.tsx` reescrito.

Header fixo, altura `--header-height`, borda inferior amarela preservada:

```text
┌──────────────────────────────────────────────────────────────────┐
│ Market Hub   [ Buscar pedido, produto ou pessoa    🔍 ]   🔔  PG │
└──────────────────────────────────────────────────────────────────┘
```

- Busca global no centro. Escopo por papel: Buyer busca produto, Seller e
  Ops buscam pedido e produto. Sem endpoint novo — despacha para a tela de
  lista ja existente com o termo na URL.
- Sino de notificacao mantido como esta, so re-tokenizado.
- Menu de usuario: `Avatar` com iniciais, dropdown com nome, papel e
  "Sair". Tira o botao "Sair" solto do header.

Navegacao por papel, como a secao 7 da skill separa as jornadas:

- **Buyer** — nav horizontal sob o header. Jornada de compra, poucos itens,
  parece marketplace.
- **Seller e Ops** — sidebar de `--sidebar-width`, com icone por item
  (`Package`, `Box`, `LifeBuoy`), recolhivel em `lg`.
- **Abaixo de `md`** — sidebar vira drawer acionado por botao no header;
  nav do Buyer vira barra rolavel horizontal.

`aria-current="page"` no item ativo. Item futuro sem rota sai da nav — hoje
existe um `<span aria-disabled>` com `title="Em breve"` que so ocupa espaco.

Container: `--container-max` nas telas de conteudo, `--container-max-wide`
nas telas de tabela de Ops.

### 4.5 Densidade — listas viram tabelas

Migram de `Card` + flex para `Table`:

| Tela | Colunas |
|---|---|
| `SellerOrdersListPage` | Produto, Comprador, Qtd, Valor, Status, Data |
| `OpsQueuePage` | Prioridade, Produto, Vendedor, Comprador, Valor, Status, Ultima interacao |
| `OpsOrderItemsListPage` | Produto, Vendedor, Comprador, Valor, Status, Data |
| `SellerOffersListPage` | Produto, Preco, Estoque, Disponivel |

Regras:

- Valor e quantidade alinhados a direita com `font-variant-numeric: tabular-nums`.
- Linha inteira clicavel, com o link real na primeira celula para o leitor
  de tela — nao um `onClick` na `<tr>`.
- Sem ordenacao por coluna: nenhuma rota do backend aceita parametro de
  sort (ver secao 10). A lista chega ja ordenada — fila da Ops por
  prioridade, listas de pedido por data.
- `OpsQueuePage` mantem a ordem de prioridade do backend.
- Abaixo de `md`, cada linha vira card com rotulo explicito por campo.

`OrdersListPage` e o catalogo continuam em card — ali o card agrupa
informacao relacionada de verdade.

### 4.6 Filtros e busca

Componente `FilterBar`:

- Filtros ativos viram chips removiveis, com "Limpar filtros" quando houver
  mais de um.
- Todo filtro passa a viver na URL, como `status` e `effective_priority` ja
  fazem — a tela inteira vira linkavel e o botao voltar funciona.
- Campo de texto com debounce de 300ms; hoje cada tecla dispara um fetch.
- Campos de UUID (`Seller (UUID)`, `ID do item`) ganham rotulo humano,
  placeholder de exemplo e validacao de formato antes do fetch, com
  mensagem "Informe o ID completo do pedido". Continuam exigindo UUID
  exato — busca parcial exigiria mudanca de contrato e esta fora de escopo,
  registrada na secao 10.
- `ProductListPage` mantem filtro no cliente nesta fase; a inconsistencia
  com as demais telas fica registrada na secao 10.
- Empty state distingue "ainda nao existe" de "nada corresponde ao filtro",
  com acao de limpar filtro no segundo caso.

### 4.7 Estados

| Estado | Hoje | Depois |
|---|---|---|
| Carregando lista | `Spinner` substitui a pagina | `Skeleton` com a forma da tabela; filtros continuam operaveis |
| Carregando detalhe | `Spinner` substitui a pagina | `Skeleton` no bloco de dados; cabecalho ja renderiza |
| Recarregando apos filtro | Conteudo some | Conteudo antigo esmaecido com `aria-busy` |
| Erro | `ErrorState` substitui a pagina | Inline, preservando filtro e contexto |
| Acao concluida | Silencio | `Toast` de sucesso |
| Acao destrutiva | `.confirm-inline` | `Dialog` com foco preso, verbo explicito no botao |
| Botao em submissao | Troca o texto | `loading` no proprio botao, largura estavel |

### 4.8 Responsividade

Checklist por tela, verificada em 375px, 768px, 1024px e 1440px:

- Shell: drawer abaixo de `md`, sidebar recolhida em `lg`.
- Tabelas: viram lista de cards abaixo de `md`.
- `.detail-columns` (conversa + suporte): hoje quebra em uma coluna em
  720px, empilhando dois paineis longos. Passa a usar `Tabs` abaixo de `md`.
- `FilterBar`: colapsa em botao "Filtros" que abre drawer abaixo de `md`.
- Alvo de toque minimo de 44px em todo controle.

### 4.9 Acessibilidade

Base obrigatoria, hoje ausente:

- Skip link "Ir para o conteudo" antes do header.
- Landmarks: `header`, `nav`, `main` com `aria-label` distinto por papel.
- Foco vai para o `<h1>` a cada navegacao de rota.
- `aria-current="page"` na nav; `aria-sort` nas colunas ordenaveis.
- `Dialog` com foco preso, retorno de foco ao gatilho e `Escape`.
- `Toast` em `role="status"` e regiao `aria-live="polite"`.
- Todo controle com rotulo — `SelectField` e os checkboxes de hoje nao tem
  associacao formal entre label e input.
- Contraste verificado: `--color-muted` (#757575) em branco da 4.6:1 e
  passa; `--color-warning` e `--color-success` so podem ser usados em texto
  sobre fundo esmaecido, nunca em preenchimento solido com texto branco,
  como `--color-danger-solid` ja documenta.
- Passe de teclado em cada tela antes de fechar a fase.

### 4.10 Vocabulario da interface

Dominio em ingles fica no codigo; a tela fala portugues:

| Hoje | Depois |
|---|---|
| "Meus Order Items" | "Pedidos" |
| "Fila de Ops" | "Fila de atendimento" |
| "Seller (UUID)" | "Vendedor" |
| "Order Item (UUID)" | "Item do pedido" |
| "Buyer" (label no detalhe) | "Comprador" |
| "Início" (dashboard) | Mantido |

Identificadores, rotas, tipos e nomes de teste continuam em ingles.

---

## 5. Fora de escopo

- Qualquer mudanca de contrato de backend, rota de UI ou fluxo de dados.
- Busca parcial ou autocomplete por vendedor e item — depende de query param
  novo.
- Filtro de catalogo no servidor, ordenacao de catalogo, imagem de produto.
- Inbox unificada de conversas, checkout multi-item, PDP estilo marketplace.
- Dark mode — a skill define tema unico claro.
- Biblioteca de componentes de terceiros, incluindo Copan.
- Grafico, KPI e analytics no dashboard.

---

## 6. Fases de execucao

Cada subfase e uma PR propria, com a suite verde e verificacao no browser
antes da seguinte.

### F8.1 — Fundacao

`tokens.css`, `base.css`, decisao de CSS Modules aplicada, `Button`,
`Card`, `Field`, `TextField`, `SelectField`, `Tag`, `Skeleton` e
`Pagination`. Telas existentes continuam funcionando, agora sobre tokens.
Nenhuma mudanca visual deliberada alem do que os tokens padronizam.

### F8.2 — App shell

`AppLayout` reescrito: header com busca e menu de usuario, nav por papel,
drawer mobile, `Breadcrumbs`, `PageHeader`, skip link, landmarks e foco em
troca de rota.

### F8.3 — Densidade

`Table` e `FilterBar`. Migracao das quatro listas operacionais, chips de
filtro, filtros na URL, debounce e empty state diferenciado.

### F8.4 — Interacao e feedback

`Dialog`, `Toast`, `Tooltip`, `Tabs`. Substituicao de `.confirm-inline`,
skeleton por tela, erro inline e estados de recarga.

### F8.5 — Fechamento

Passe de responsividade e teclado em todas as telas, remocao de CSS morto,
atualizacao de `docs/CURRENT_STATE.md` e nota no
`docs/FRONTEND_IMPLEMENTATION_PLAN.md`.

---

## 7. Criterios de aceite

1. `src/styles/global.css` nao contem mais regra de tela; nenhum componente
   novo usa cor, espaco, raio ou tamanho de fonte fora de token.
2. A paleta e identica a de hoje, variavel por variavel.
3. As quatro listas operacionais sao tabela em `md` para cima e lista de
   card abaixo disso, com rotulo por campo.
4. Toda tela responde corretamente em 375px, 768px, 1024px e 1440px.
5. Toda tela e operavel so pelo teclado, com foco sempre visivel.
6. Toda acao de mutacao produz feedback visivel; toda acao destrutiva
   passa por `Dialog`.
7. Nenhum fetch novo, nenhum parametro novo, nenhuma rota nova.
8. Suite de 26 arquivos verde, incluindo `OpsQueuePage.test.tsx`, que deixa
   de consultar por `.priority-high` e passa a consultar por texto.

---

## 8. Testes

- Cada primitivo novo com teste de comportamento: `Dialog` fecha no
  `Escape` e devolve foco, `Toast` anuncia em regiao viva, `Table` expoe
  caption e cabecalhos de coluna, `Tabs` navega por seta, `useDebouncedValue`
  so estabiliza no ultimo valor da rajada.
- Testes de tela existentes migram de consulta estrutural para consulta por
  papel e texto acessivel, onde ainda nao estao.
- Teste de navegacao do shell: item ativo marca `aria-current`, drawer abre
  e fecha, skip link leva ao `main`.
- Sem teste de snapshot visual — a suite nao tem infraestrutura para isso e
  a fase nao justifica introduzir.

---

## 9. Definition of Done (F8)

- F8.1 a F8.5 mergeadas na main, cada uma verificada no browser.
- `docs/CURRENT_STATE.md` atualizado: versao, fase, commit de referencia,
  secao de frontend, convencoes de CSS e "o que ainda nao existe".
- `.cursor/skills/frontend-design-patterns/SKILL.md` atualizada quando a
  implementacao divergir do que a skill descreve — hoje ela descreve tabela
  e header com busca que o codigo nao tem.
- `frontend/README.md` com a arquitetura de estilo e a lista de primitivos.
- Nenhuma classe CSS orfa em `src/styles/`.

---

## 10. Decisoes pendentes e divida registrada

Confirmadas com o autor antes da implementacao:

1. **Fundo de pagina cinza adotado.** `--color-canvas: #eeeeee` para o fundo
   e `--color-surface: #ffffff` para card e tabela, como a skill do projeto
   ja declarava. `--color-bg` continua branco: e a base dos `color-mix` de
   bolha e de suporte, que acontecem sempre sobre um card.
2. **CSS Modules adotado**, sem dependencia nova.

Divergencias entre o que esta spec planejou e o que foi implementado:

- **Ordenacao por coluna nao existe.** A secao 4.5 previa ordenar por
  `created_at` e `effective_priority`, mas nenhuma rota do backend aceita
  parametro de sort — nem o frontend, nem `app/`. Ordenar so no cliente
  ordenaria a pagina atual, nao o conjunto. `TableHeaderCell` ficou sem a
  API de sort, em vez de expor um controle que engana. Habilitar isso e
  mudanca de contrato, que a secao 5 poe fora de escopo.
- **`SearchField` nao virou componente proprio.** O que a secao 4.3 pedia
  dele — icone, debounce, limpar — ja e coberto por `TextField type="search"`
  (o `type` nativo traz o botao de limpar) mais o hook
  `useDebouncedValue`. Um componente a mais so para juntar os dois seria
  invencao sem caso de uso, contra a regra "criar somente o necessario".
- **Hint abaixo do controle, nao acima.** Descoberto na verificacao no
  browser: com a dica entre label e input, o campo com hint empurrava o
  proprio input para baixo e desalinhava a linha inteira da barra de filtros.
- **Divergencia de nomenclatura registrada, nao corrigida.** A skill nomeia
  `--color-background`, `--color-action-primary` e `--color-error`; o codigo
  usa `--color-canvas`, `--color-primary` e `--color-danger` desde o F0.
  Mesmos valores, nomes diferentes. Renomear esta fora do escopo acordado e
  fica como decisao em aberto.

Divida deliberada, fora desta fase:

- Busca por UUID exato nas telas de Seller e Ops.
- Catalogo filtrando no cliente enquanto as demais listas filtram no
  servidor.
- Catalogo sem imagem de produto, sem ordenacao e sem paginacao.

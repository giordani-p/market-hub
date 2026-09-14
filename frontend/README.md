# Market Hub — Frontend

Aplicacao React + TypeScript (Vite) que consome a API do Market Hub. Camada
de apresentacao: formata, linka e trata loading/empty/error. Regra de
negocio — prioridade, totais, transicao de status, ownership — fica no
backend.

## Como rodar

```bash
npm install
npm run dev
```

A URL da API vem de `VITE_API_BASE_URL`.

| Comando          | O que faz                                |
| ---------------- | ---------------------------------------- |
| `npm run dev`    | Servidor de desenvolvimento              |
| `npm run build`  | Typecheck (`tsc -b`) e build de producao |
| `npm test`       | Suite Vitest + Testing Library           |
| `npm run lint`   | Oxlint                                   |
| `npm run format` | Prettier                                 |

## Estrutura

```text
src/
  app/          shell, rotas e providers
    layout/     AppLayout, nav por papel, busca global, menu de usuario
    router/     rotas e guardas de acesso
    providers/  AuthProvider e contexto de auth
  components/
    ui/         primitivos (Button, Field, Tag, Tabs, Skeleton, Logo, ...)
    data/       Table, FilterBar, DetailList
    layout/     Page, PageHeader, Section, Breadcrumbs
    feedback/   Spinner, EmptyState, ErrorState, FormError
    overlay/    Dialog, ConfirmDialog, ToastProvider
  features/     uma pasta por dominio (catalog, orders, ops, ...)
  lib/          cliente HTTP, auth, hooks e formatadores
  styles/       tokens e base globais
  test/         setup do Vitest e renderWithProviders
  types/        contratos da API
```

Cada `features/*` tem o proprio `api.ts`. Nenhum componente chama `fetch`
direto: tudo passa por `lib/api/client.ts`, que injeta o JWT e normaliza
erro em `ApiRequestError`.

## Estilo

Tres camadas, nessa ordem:

1. `styles/tokens.css` — cor, espacamento, tipografia, raio, elevacao e
   layout. **Toda** medida e cor sai daqui. Nenhum hex, `px` ou `rem` solto
   em componente.
2. `styles/base.css` — reset, elementos base, foco e dois utilitarios
   (`.text-muted`, `.sr-only`).
3. `Componente.module.css` — estilo de componente, ao lado do `.tsx`.

Regras que valem em todo lugar:

- Sombra so em camada flutuante (dropdown, dialog, toast). Superficie
  inline se separa por borda e por diferenca de fundo.
- Breakpoints: 480, 768, 1024 e 1200px, usados literalmente — CSS nativo
  nao aceita variavel em `@media`. A escala esta documentada no topo de
  `tokens.css`.
- Tema unico claro. Nao ha dark mode, por decisao de produto.
- A marca (`Logo`) e o quadrado azul com a sacola, o mesmo simbolo do
  `public/favicon.svg`. A cor do wordmark vem de `currentColor`: quem
  decide e o contexto.

A linguagem visual esta em `.cursor/skills/frontend-design-patterns`.

## Primitivos

| Grupo        | Componentes                                                                                               |
| ------------ | --------------------------------------------------------------------------------------------------------- |
| Acao         | `Button` (`primary`/`secondary`/`tertiary`/`destructive`, `loading`, `fullWidth`)                         |
| Formulario   | `Field`, `TextField` (com slot `trailing`), `SelectField`, `TextAreaField`, `Checkbox`, `Radio`           |
| Dado         | `Table` (+ `TableHead`, `TableRow`, `TableCell`, `TableRowLink`), `DetailList`, `FilterBar`, `Pagination` |
| Layout       | `Page`, `PageHeader`, `Section`, `Breadcrumbs`, `Card`                                                    |
| Estado       | `Skeleton`, `SkeletonList`, `Spinner`, `EmptyState`, `ErrorState`, `FormError`                            |
| Sobreposicao | `Dialog`, `ConfirmDialog`, `ToastProvider` + `useToast`, `Tooltip`                                        |
| Sinalizacao  | `Tag`, `StatusBadge`, `PriorityBadge`, `Avatar`, `Logo`                                                   |
| Navegacao    | `Tabs`                                                                                                    |

Antes de criar um componente novo, procure reuso. `lucide-react` e a unica
biblioteca de icones.

## Hooks compartilhados

Em `lib/utils/`, e usados pelas telas de lista:

| Hook                | Para que                                                                      |
| ------------------- | ----------------------------------------------------------------------------- |
| `useAsync`          | Um fetch com `loading`/`success`/`error` e `retry`                            |
| `useUrlFilters`     | Filtros na query string; trocar um filtro volta para a primeira pagina        |
| `useDebouncedValue` | Atrasa o valor aplicado de um campo de texto (300ms por padrao)               |
| `useMediaQuery`     | So quando o layout muda de **estrutura** (paineis que viram abas). CSS antes. |

`isCompleteUuid`, em `useUrlFilters.ts`, valida os filtros de ID antes do
fetch — o backend so compara por igualdade.

## Logica de tela

Regra de apresentacao que nao e render mora em modulo proprio, ao lado da
tela, como funcao pura e testada antes da UI. O catalogo e o exemplo
completo:

```text
features/catalog/
  catalogRows.ts     cruza produto e oferta; deriva menor preco, lojas, estoque
  catalogFilters.ts  busca sem acento, faixa de preco, disponibilidade
  catalogSort.ts     ordenacoes e a posicao de quem nao tem preco
```

A tela consome essas funcoes com `useMemo`; o cruzamento nao acontece
dentro do `.map`.

## Convencoes

- Interface em portugues; identificadores, rotas e tipos em ingles.
- Sucesso de acao vai para `Toast`; erro fica inline, perto do controle que
  a disparou (`FormError`).
- Acao irreversivel passa por `ConfirmDialog`.
- Filtro de lista vive na URL: a tela filtrada e um link e o botao voltar
  desfaz o filtro.
- Lista operacional densa e `Table`, que vira lista de cards abaixo de
  `md`, com o rotulo da coluna repetido em cada celula.
- Estado vazio distingue "ainda nao existe" de "nada corresponde ao
  filtro"; o segundo oferece limpar os filtros.
- Contagem de resultado fica em regiao viva (`role="status"`), senao
  aplicar um filtro nao avisa quem usa leitor de tela.
- Teste consulta por papel e texto acessivel, nunca por classe de estilo.
  Componente que depende de provider usa `test/renderWithProviders`.
- Todo controle tem rotulo; icone isolado tem `aria-label` ou `Tooltip`.

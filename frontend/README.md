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
    ui/         primitivos (Button, Field, Tag, Tabs, Skeleton, ...)
    data/       Table, FilterBar, DetailList
    layout/     Page, PageHeader, Section, Breadcrumbs
    feedback/   Spinner, EmptyState, ErrorState, FormError
    overlay/    Dialog, ConfirmDialog, Toast
  features/     uma pasta por dominio (catalog, orders, ops, ...)
  lib/          cliente HTTP, auth, hooks e formatadores
  styles/       tokens e base globais
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

A linguagem visual esta em `.cursor/skills/frontend-design-patterns`.

## Primitivos

| Grupo        | Componentes                                                                                               |
| ------------ | --------------------------------------------------------------------------------------------------------- |
| Acao         | `Button` (`primary`/`secondary`/`tertiary`/`destructive`, `loading`, `fullWidth`)                         |
| Formulario   | `Field`, `TextField`, `SelectField`, `TextAreaField`, `Checkbox`, `Radio`                                 |
| Dado         | `Table` (+ `TableHead`, `TableRow`, `TableCell`, `TableRowLink`), `DetailList`, `FilterBar`, `Pagination` |
| Layout       | `Page`, `PageHeader`, `Section`, `Breadcrumbs`, `Card`                                                    |
| Estado       | `Skeleton`, `SkeletonList`, `Spinner`, `EmptyState`, `ErrorState`, `FormError`                            |
| Sobreposicao | `Dialog`, `ConfirmDialog`, `ToastProvider` + `useToast`, `Tooltip`                                        |
| Sinalizacao  | `Tag`, `StatusBadge`, `PriorityBadge`, `Avatar`                                                           |
| Navegacao    | `Tabs`                                                                                                    |

Antes de criar um componente novo, procure reuso. `lucide-react` e a unica
biblioteca de icones.

## Convencoes

- Interface em portugues; identificadores, rotas e tipos em ingles.
- Sucesso de acao vai para `Toast`; erro fica inline, perto do controle que
  a disparou (`FormError`).
- Acao irreversivel passa por `ConfirmDialog`.
- Filtro de lista vive na URL: a tela filtrada e um link e o botao voltar
  desfaz o filtro.
- Teste consulta por papel e texto acessivel, nunca por classe de estilo.
- Todo controle tem rotulo; icone isolado tem `aria-label` ou `Tooltip`.

# Market Hub — F0 — Frontend Foundation (Spec)

Deriva de `docs/FRONTEND_IMPLEMENTATION_PLAN.md`. Este documento cobre **apenas**
a F0. Não implementa Catalog, Orders, Conversations ou Ops.

---

## 1. Objetivo

Criar a fundação técnica e visual do frontend: projeto React + TypeScript,
routing, cliente HTTP, autenticação (login/logout/sessão), layout principal e
os componentes/estado compartilhados (loading, error, empty) que as fases
seguintes vão reutilizar sem reestruturar o projeto.

## 2. Contexto (verificado no backend nesta sessão)

Antes desta spec, o backend não expunha `CORS`, o que bloquearia qualquer SPA
rodando em outra origem (browser barra a chamada antes de chegar na API).
Correção já aplicada nesta sessão:

- `Settings.cors_origins` (env `CORS_ORIGINS`, default
  `http://localhost:5173,http://localhost:3000`) em `app/core/config.py`.
- `CORSMiddleware` registrado em `app/main.py` com esses origins,
  `allow_credentials=True`, métodos e headers livres.
- `.env.example` e `docs/CURRENT_STATE.md` atualizados.

Sem essa mudança, F0 não teria como validar login/sessão contra a API real a
partir do browser. Nenhum outro gap bloqueante foi identificado para F0: login,
`/me`, formato de erro e o próprio `openapi.json` já existem e cobrem o que
esta fase precisa.

Contratos usados nesta fase (não redefinir, só consumir):

| Rota | Request | Resposta | Erros |
|---|---|---|---|
| `POST /v1/auth/login` | `{ email, password }` | `{ access_token, token_type: "bearer" }` | `401 unauthorized` |
| `GET /v1/auth/me` | Bearer token | `{ id, email, name, role, seller_id }` | `401 unauthorized` |
| `GET /v1/health` | — | `{ status, version }` | — |

- `role` é `"buyer" | "seller" | "ops"`. `seller_id` é `null` para buyer/ops.
- Erros de negócio: `{ code, message }` (`ErrorResponse`). Erros de validação
  (422) seguem o formato padrão do FastAPI (`{ detail: [...] }`) — tratar os
  dois formatos no cliente HTTP.
- Não existe refresh token nem `/auth/register`. Sessão expira em
  `JWT_EXPIRE_MINUTES` (60 por padrão); a UI deve deslogar ao receber `401` e
  não deve tentar renovar o token silenciosamente.
- `api/openapi.yaml` é a fonte de verdade do contrato; `GET /openapi.json` é
  servido pela app em runtime e pode ser usado para gerar tipos, mas isso é
  opcional para F0 — tipos podem ser escritos à mão dado o escopo pequeno.

## 3. Escopo

- Projeto Vite + React + TypeScript em `frontend/` (novo diretório na raiz do
  repo, ao lado de `app/`).
- Estrutura de diretórios feature-oriented (reduzida ao necessário para F0):
  ```text
  frontend/
  ├── src/
  │   ├── app/
  │   │   ├── router/         # rotas + guarda de autenticação
  │   │   ├── providers/       # AuthProvider, etc.
  │   │   └── layout/          # shell, navegação por papel
  │   ├── features/
  │   │   └── auth/            # login, sessão — única feature completa na F0
  │   ├── components/
  │   │   ├── ui/              # Button, Input, Card, etc.
  │   │   └── feedback/        # Spinner, EmptyState, ErrorState
  │   ├── lib/
  │   │   ├── api/              # cliente HTTP, tratamento de erro
  │   │   ├── auth/              # storage/leitura de token
  │   │   └── utils/
  │   ├── types/                # tipos dos contratos consumidos (auth por ora)
  │   └── styles/
  ├── index.html
  ├── package.json
  ├── tsconfig.json
  └── vite.config.ts
  ```
- Roteamento com React Router: `/login` (público) e um shell autenticado com
  rota raiz `/` que redireciona para uma home placeholder por papel (ver §5).
- Cliente HTTP centralizado (`lib/api`): base URL via env, injeta
  `Authorization: Bearer <token>`, normaliza os dois formatos de erro do
  backend em um tipo único (`ApiError { code, message }`), e dispara logout em
  qualquer `401`.
- Autenticação: formulário de login → `POST /auth/login` → guarda token →
  `GET /auth/me` → guarda usuário → redireciona pela `role`. Logout limpa
  storage e volta para `/login`.
- Persistência de sessão: token em `localStorage` (única opção viável, já que
  o backend não emite cookie httpOnly); ao carregar a app, se houver token
  guardado, chamar `GET /auth/me` para revalidar antes de liberar rotas
  protegidas.
- Layout principal: header com nome do produto, indicador de notificação
  **desabilitado/oculto** (F5 implementa o dado real — não simular contagem),
  nome do usuário e logout. Navegação lateral/superior placeholder por papel
  (Buyer: Catalog, My Orders — desabilitados/"em breve"; Seller: Orders —
  desabilitado; Ops: Operations/Queue — desabilitado), conforme a navegação
  proposta na §12 do plano.
- Componentes UI compartilhados essenciais: Button, Input, Card, Badge (para
  status), Spinner, EmptyState, ErrorState, layout de página (`PageHeader`,
  container).
- Estados básicos de loading/error/empty como componentes reutilizáveis (sem
  dado real ainda — usados a partir da F1).
- Tratamento inicial de erros da API: boundary de erro genérico na rota +
  mapeamento de `ApiError` para mensagem legível.
- Lint/format: ESLint + Prettier (ou só Prettier, decidir no setup) alinhado ao
  padrão de 100 colunas do backend, se aplicável ao frontend; Vitest +
  Testing Library para os testes desta fase.

## 4. Fora de escopo (explícito)

- Catalog, Offers, Orders, Order Items, Conversation, Internal Comments,
  Priority, Notifications reais — tudo isso é F1+.
- Qualquer chamada às rotas de `/v1/order-items`, `/v1/ops/*`,
  `/v1/conversations/*`, `/v1/notifications/*`.
- Deep linking de notificações.
- Gerenciador de estado global (Redux/Zustand/etc.) — não há necessidade real
  ainda.
- Geração automática de tipos a partir do OpenAPI (pode entrar depois se o
  volume de contratos justificar).

## 5. UX / Rotas

```text
/login                      (público)
/                            (autenticado; redireciona por role)
/buyer                       (placeholder "Catalog em breve")
/seller                      (placeholder "Orders em breve")
/ops                         (placeholder "Queue em breve")
*                            (404 simples)
```

- Usuário não autenticado acessando qualquer rota exceto `/login` → redireciona
  para `/login`.
- Usuário autenticado acessando `/login` → redireciona para a home do seu
  papel.
- Login: formulário com email/senha, estado de loading no submit, mensagem de
  erro inline quando `401 unauthorized` (credenciais inválidas) e para outros
  erros de rede/servidor.

## 6. Estados

- **Loading**: enquanto `GET /auth/me` revalida sessão ao carregar a app, e
  enquanto o login está em voo.
- **Error**: erro de login (credenciais inválidas / falha de rede) exibido no
  próprio formulário; erro inesperado (crash de render) capturado por um
  boundary genérico com opção de recarregar.
- **Empty**: não se aplica a dados nesta fase (não há listas); os componentes
  `EmptyState`/`ErrorState` devem existir e ser exercitados só via Storybook-
  like harness ou teste de componente, não por uma tela real ainda.

## 7. Critérios de aceite

1. `npm run dev` (ou equivalente) sobe o frontend em `http://localhost:5173`
   e consegue chamar a API local (`make run`) sem erro de CORS.
2. Login com um usuário de seed (Loja A/B = seller, Buyer Demo = buyer, Ops
   Demo = ops) autentica e redireciona para a home correspondente ao `role`.
3. Login com credenciais inválidas mostra mensagem de erro sem quebrar a tela.
4. Recarregar a página autenticado mantém a sessão (revalidação via `/me`) até
   o token expirar; após expirar, qualquer chamada 401 desloga e volta para
   `/login`.
5. Logout limpa o token e bloqueia acesso a rotas protegidas.
6. Nenhuma rota fora de `/login` é acessível sem autenticação (testado
   manualmente via navegação direta por URL).
7. Estrutura de pastas criada conforme §3, pronta para receber `features/orders`,
   `features/conversations`, `features/ops`, `features/notifications` na
   sequência sem mover arquivos existentes.

## 8. Testes

- Unit: cliente HTTP (injeção de token, normalização de erro, logout em 401).
- Component: formulário de login (submit, loading, erro), guarda de rota
  (redireciona não autenticado).
- Não é necessário E2E nesta fase.

## 9. Definition of Done (F0)

- Aplicação navegável localmente, integrada à API real (login/me/logout).
- Estrutura de diretórios estável, sem necessidade de reorganização para F1.
- Estados de loading/error básicos implementados nos componentes
  compartilhados (mesmo sem consumidores reais ainda).
- Lint e testes desta fase passando.
- Nenhuma funcionalidade de Catalog/Orders/Conversation/Ops implementada.

## 10. Instruções para implementação (Cursor)

1. Rodar `make run` localmente e confirmar `CORS_ORIGINS` no `.env` (ou usar o
   default) antes de iniciar o frontend.
2. Criar o projeto com Vite (`npm create vite@latest frontend -- --template
   react-ts`), depois ajustar para a estrutura de pastas do §3.
3. Implementar `lib/api` primeiro (cliente HTTP + tipos de erro), depois
   `features/auth`, depois `app/router` + `app/layout`.
4. Usar variável de ambiente (`VITE_API_BASE_URL`, default
   `http://localhost:8000/v1`) para a base URL — nunca hardcode.
5. Não implementar telas de Catalog/Orders/Ops além dos placeholders
   descritos em §5 — isso é F1/F2/F4.
6. Ao final, validar manualmente os 7 critérios de aceite do §7 contra a API
   local antes de considerar a fase concluída.

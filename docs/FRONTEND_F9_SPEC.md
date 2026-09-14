# Market Hub — F9 — Listagem do Catalogo (Spec)

Deriva de `docs/FRONTEND_IMPLEMENTATION_PLAN.md` e da skill de projeto
`.cursor/skills/frontend-design-patterns`. Assume F0-F8 prontos e
mergeados. **Nenhuma mudanca de contrato de backend, de rota de UI ou de
fluxo de dados.**

Decisao tomada com o autor antes de escrever esta spec: a fase e so de
frontend. Categoria e loja ficam de fora porque nao existem no backend
(ver secao 2). Se uma fase de backend vier depois, a modelagem ja
acordada e `category` como enum fixo no `Product` — sem tabela nova.

---

## 1. Objetivo

Transformar `/catalog` de uma grade simples em uma listagem de produto que
se comporta como a de um marketplace, dentro do que os dados de hoje
permitem.

Tres resultados, nessa ordem:

1. **Encontrar** — filtros de busca, faixa de preco e disponibilidade, mais
   ordenacao, tudo refletido na URL.
2. **Comparar** — o card passa a dizer o que importa para escolher: menor
   preco em destaque, em quantas lojas o produto esta e se da para comprar.
3. **Entender onde se esta** — contagem de resultados, filtros ativos
   visiveis e estados vazios que distinguem "nao existe" de "nao achou".

---

## 2. Contexto (verificado no backend, commit `8d8dd17`)

O que a API oferece hoje para esta tela:

| Rota | O que devolve |
|---|---|
| `GET /v1/products` | Lista **completa**, sem filtro, sem ordenacao, sem paginacao |
| `GET /v1/offers` | Lista **completa** das ofertas; so aceita `seller_id` |

Campos disponiveis:

- `Product`: `id`, `name`, `description`. **Nao ha** categoria, imagem,
  marca, data de criacao nem avaliacao.
- `Offer`: `id`, `product_id`, `seller_id`, `price`, `stock`, `available`.
  **Nao ha** nome da loja — e nao existe rota de sellers em lugar nenhum
  (`app/main.py` nao registra nenhuma).

Volume do seed atual: 32 produtos, 46 ofertas, 8 lojas. Os produtos formam
seis segmentos evidentes (tech, moda, casa, esporte, livros, kids), mas
**esse agrupamento so existe em `app/catalog/demo.py`** — nao e campo, nao
e tabela e nao chega na resposta.

Consequencia direta: os filtros mais uteis de um marketplace — categoria e
loja — sao impossiveis nesta fase. O que da para derivar dos dados que
chegam:

| Derivado | De onde sai |
|---|---|
| Menor preco comprável | menor `price` entre ofertas com `available` e `stock > 0` |
| Faixa de preco | menor e maior preco entre as compraveis |
| Em quantas lojas | `seller_id` distintos com oferta comprável |
| Quantas ofertas | ofertas compraveis do produto |
| Tem estoque | existe ao menos uma oferta comprável |

### Estado da tela hoje

- `ProductListPage` busca `fetchProducts()` e `fetchOffers()` em paralelo e
  cruza no cliente.
- Filtra por nome e por "somente disponiveis", ambos na URL (F8).
- Sem ordenacao, sem paginacao, sem contagem de resultados.
- O card mostra nome, descricao e "A partir de <preco>".
- `offers.filter(...)` roda dentro do `.map` e tambem dentro do filtro de
  disponibilidade: o cruzamento produto/oferta e refeito a cada render,
  duas vezes, em O(produtos x ofertas).
- O skeleton usa `SkeletonList variant="card"`, que desenha barras de
  largura inteira — nao tem a forma da grade que vai aparecer.

---

## 3. Principios

1. **So o que os dados sustentam.** Nenhum filtro decorativo, nenhum
   "categoria" inventado no cliente a partir de palavra no nome. Se o dado
   nao existe, o filtro nao existe — e a secao 9 registra por que.
2. **A URL e o estado.** Busca, faixa, disponibilidade, ordenacao e pagina
   vivem na query string, como as demais listas desde a F8.
3. **Derivar uma vez.** O cruzamento produto/oferta vira um indice
   memoizado, nao um `filter` dentro do `map`.
4. **Regra de dominio continua no backend.** Preco, estoque e
   disponibilidade vem prontos; o cliente so agrega para exibir.
5. **Token ou nada**, e o card continua sendo card porque agrupa
   informacao relacionada — nao por estetica.

---

## 4. Escopo

### 4.1 Modelo de apresentacao

Novo modulo `features/catalog/catalogRows.ts`, funcoes puras:

```ts
interface CatalogRow {
  product: Product
  lowestPrice: string | null   // null quando nao ha oferta comprável
  highestPrice: string | null
  sellerCount: number
  offerCount: number
  inStock: boolean
}

deriveCatalogRows(products: Product[], offers: Offer[]): CatalogRow[]
```

`deriveCatalogRows` monta um `Map<product_id, Offer[]>` em uma passada e
deriva cada linha a partir dele.

> Divergencia da implementacao: esta spec previa reaproveitar
> `lowestAvailablePrice` de `pricing.ts` por dentro de `deriveCatalogRows`.
> Nao foi: a funcao derivada precisa de menor preco, maior preco, lojas
> distintas e contagem, tudo em um laco so. Chamar `lowestAvailablePrice`
> exigiria uma segunda varredura para calcular o que o laco ja tem.
> `pricing.ts` ficou sem nenhum consumidor e foi removido junto com o seu
> teste; o comportamento dele esta coberto por `catalogRows.test.ts`.

### 4.2 Filtros

Um modulo `catalogFilters.ts` com a aplicacao, tambem pura:

| Filtro | Parametro na URL | Comportamento |
|---|---|---|
| Busca | `q` | Casa em `name` **e** `description`, sem acento e sem caixa. Debounce de 300ms, como as demais listas |
| Preco minimo | `min` | Compara com `lowestPrice`; produto sem preco sai quando o filtro esta ativo |
| Preco maximo | `max` | Idem |
| Somente disponiveis | `available=true` | Mantem so `inStock` |

Regras que precisam estar escritas, porque sao decisao e nao detalhe:

- Busca ignora acento (`Intl`/`normalize('NFD')`), senao "relogio" nao acha
  "Relogio" digitado com acento e vice-versa.
- `min` maior que `max` nao filtra nada: mostra erro no campo
  ("O minimo nao pode ser maior que o maximo.") e mantem a lista anterior.
- Valor invalido em `min`/`max` e ignorado, nao zera a lista.

### 4.3 Ordenacao

`sort` na URL, com quatro opcoes:

| Valor | Rotulo | Criterio |
|---|---|---|
| (ausente) | Mais relevantes | Ordem em que a API devolveu |
| `price_asc` | Menor preco | `lowestPrice` crescente |
| `price_desc` | Maior preco | `lowestPrice` decrescente |
| `name_asc` | Nome (A-Z) | `localeCompare` em pt-BR |

Produto sem oferta comprável **vai sempre para o fim** nas duas ordenacoes
por preco, independente da direcao. Jogar "sem preco" para o topo de
"maior preco" seria matematicamente coerente e praticamente inutil.

Nao existe "mais recentes": `Product` nao tem data.

### 4.4 Layout da listagem

Duas colunas a partir de `lg` (1024px):

```text
┌────────────┬──────────────────────────────────────────┐
│  Filtros   │  32 produtos        [ Ordenar por  ▾ ]   │
│  (fixo)    ├──────────────────────────────────────────┤
│            │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
│  Busca     │  │ card │ │ card │ │ card │ │ card │     │
│  Preco     │  └──────┘ └──────┘ └──────┘ └──────┘     │
│  Estoque   │  ...                                     │
│            │  [ paginacao ]                           │
└────────────┴──────────────────────────────────────────┘
```

- Coluna de filtros com `position: sticky` abaixo do header, largura fixa
  (~260px), rolagem propria.
- Abaixo de `lg` ela vira o `FilterBar` que ja existe desde a F8 — colapsa
  atras do botao "Filtros". Nenhum componente novo para o mobile.
- A barra de resultados (contagem + ordenacao) fica acima da grade e
  acompanha a coluna de resultados, nao a pagina inteira.
- A grade continua `auto-fill` com minimo de 220px; a pagina passa a usar
  `width="wide"`, porque quatro colunas nao cabem em 1200px com o rail.

### 4.5 Card de produto

O que o card passa a mostrar, de cima para baixo:

1. Area de imagem (placeholder, como hoje — nao ha `image_url`).
2. Nome, com no maximo duas linhas.
3. **Menor preco em destaque**, com "a partir de" como rotulo pequeno.
4. Linha de contexto: `em N lojas` quando `sellerCount > 1`; `1 loja`
   quando e uma so.
5. Sem oferta comprável: no lugar do preco, uma `Tag` `muted` "Sem
   estoque", e o card inteiro fica esmaecido — continua clicavel, porque a
   PDP ainda tem informacao util.

A descricao **sai do card**. Ela ocupa duas a tres linhas, empurra o preco
para baixo e nao ajuda a escolher entre produtos; continua na PDP.

### 4.6 Barra de resultados

- Contagem: "32 produtos" / "1 produto" / "Nenhum produto". Vive em
  `aria-live="polite"` — quem usa leitor de tela precisa saber que a lista
  mudou depois de aplicar um filtro.
- `SelectField` de ordenacao, rotulado "Ordenar por".
- Chips de filtro ativo continuam no `FilterBar`, como nas demais listas.

### 4.7 Paginacao

`Pagination` (o componente da F8), `page` na URL, 24 por pagina. So
aparece quando o resultado passa de uma pagina — com 32 produtos e um
filtro aplicado, o controle some sozinho na maioria das buscas.

Trocar qualquer filtro ou a ordenacao volta para a pagina 1 (o
`useUrlFilters` ja faz isso).

### 4.8 Estados

| Estado | Comportamento |
|---|---|
| Carregando | Skeleton **com a forma da grade** — nova variante `product` no `Skeleton`, no lugar das barras de largura inteira |
| Erro | `ErrorState` inline; filtros continuam operaveis |
| Catalogo vazio | "Nenhum produto no catalogo ainda." |
| Filtro sem resultado | "Nenhum produto corresponde aos filtros." + acao "Limpar filtros" |

### 4.9 Acessibilidade

- A grade vira `<ul>`/`<li>`: e uma lista, e o leitor de tela anuncia
  quantos itens tem.
- Cada card e um unico link, com nome acessivel = nome do produto. Preco e
  contexto ficam dentro do link, sem virar alvo separado.
- Contagem de resultados em regiao viva.
- Campos de preco com `inputMode="decimal"` e rotulo proprio ("Preco
  minimo" / "Preco maximo"), nunca so um placeholder.
- Passe de teclado e de contraste antes de fechar a fase.

---

## 5. Fora de escopo

- Qualquer mudanca de contrato, rota ou fluxo de dados.
- Filtro por categoria e por loja (ver secao 9).
- Imagem de produto.
- Ordenacao por novidade, relevancia real, avaliacao ou frete.
- Filtro no servidor e paginacao no servidor: a tela continua baixando
  `products` e `offers` inteiros e cruzando no cliente.
- PDP (`ProductDetailPage`) e fluxo de compra.
- Alternar entre grade e lista: com 32 produtos sem imagem, a visao em
  lista nao acrescenta nada que a grade ja nao mostre.

---

## 6. Fases de execucao

Duas PRs, cada uma com a suite verde e verificacao no browser.

### F9.1 — Dados e regras

`catalogRows.ts`, `catalogFilters.ts` e a ordenacao, com teste unitario
antes da tela. `ProductListPage` passa a consumir as funcoes puras, com o
indice memoizado. Filtros novos na URL. Sem mudanca visual deliberada
alem dos controles novos.

### F9.2 — Listagem

Rail de filtros, barra de resultados, card novo, skeleton em forma de
grade, paginacao, estados vazios e responsividade.

---

## 7. Criterios de aceite

1. Busca casa nome e descricao, ignora acento e caixa, e so dispara o
   filtro 300ms depois da ultima tecla.
2. Faixa de preco filtra pelo menor preco comprável; `min > max` mostra
   erro no campo e nao esvazia a lista.
3. As quatro ordenacoes funcionam, e produto sem oferta comprável fica no
   fim das duas por preco.
4. Busca, faixa, disponibilidade, ordenacao e pagina sobrevivem a um
   recarregar e ao botao voltar.
5. A contagem de resultados bate com o que esta na grade e e anunciada em
   regiao viva.
6. O card mostra menor preco e numero de lojas; produto sem estoque aparece
   esmaecido, com "Sem estoque" no lugar do preco.
7. Em `lg` ha rail de filtros fixo; abaixo de `md`, o `FilterBar` colapsado
   da F8, sem componente novo.
8. O cruzamento produto/oferta acontece uma vez por mudanca de dado, nao a
   cada render.
9. Nenhum fetch novo, nenhum parametro novo de API, nenhuma rota nova.

---

## 8. Testes

- `catalogRows.test.ts`: produto sem oferta, com oferta indisponivel, com
  `stock: 0`, com varias lojas, e a contagem de lojas distintas.
- `catalogFilters.test.ts`: busca sem acento, faixa invertida, faixa
  parcial (so `min`), produto sem preco com faixa ativa.
- `catalogSort.test.ts`: as quatro ordenacoes e a posicao de quem nao tem
  preco.
- `ProductListPage.test.tsx`: filtro inicializado pela query string,
  contagem de resultados, estado vazio com filtro versus sem filtro, e
  card de produto sem estoque.

---

## 9. Divida registrada — e por que

O que um marketplace teria nesta tela e este projeto nao pode ter agora:

| Falta | Bloqueio real |
|---|---|
| Filtro por categoria | `Product` nao tem o campo. O agrupamento existe so em `app/catalog/demo.py` |
| Filtro e nome de loja | `OfferResponse` traz so `seller_id`, e **nao ha rota de sellers** |
| Imagem do produto | Nao ha `image_url` nem estrategia de asset |
| Ordenar por novidade | `Product` nao tem `created_at` |
| Filtro e paginacao no servidor | `GET /products` e `GET /offers` nao aceitam parametro nenhum |
| Avaliacao, frete, parcelamento | Nao existem no dominio |

Decisao ja acordada para quando uma fase de backend abrir: `category` como
**enum fixo no `Product`** (tech, moda, casa, esporte, livros, kids) — uma
migration, sem tabela nova, sem CRUD de categoria. O resto da lista acima
continua em aberto.

---

## 10. Definition of Done (F9)

- F9.1 e F9.2 mergeadas, cada uma verificada no browser em 375, 768, 1024
  e 1440px.
- `docs/CURRENT_STATE.md` atualizado: versao, fase, secao de frontend e
  "o que ainda nao existe".
- `frontend/README.md` com os modulos novos de catalogo, se a lista de
  primitivos mudar.
- Nenhuma classe CSS orfa e nenhuma funcao exportada sem uso.

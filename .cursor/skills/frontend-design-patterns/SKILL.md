---
name: frontend-design-patterns
description: >
  Visual language, design tokens, and UX rules for the Market Hub frontend.
  Use when building or restyling UI, choosing color/typography/spacing, implementing
  Buyer/Seller/Ops screens, conversations, notifications, or reviewing visual
  consistency with the marketplace language.
  Do not use for backend, API contracts, or non-UI work.
paths:
  - frontend/**
---

# Frontend Design Patterns

Apply this visual language when creating or changing Market Hub UI. Usability beats visual similarity.

## Objetivo

Definir a linguagem visual e as regras de UX do frontend do Market Hub, buscando forte familiaridade com a experiência de marketplace do Mercado Livre, mas mantendo identidade própria.

**Prioridade:** usabilidade → acessibilidade → clareza → consistência → semelhança visual.

Não copiar literalmente telas, logos, assets ou elementos proprietários. Os termos públicos do Mercado Livre restringem aplicações que possam ser confundidas com produtos oficiais ou que reproduzam sua propriedade intelectual/design de forma similar.

O Mercado Livre também mantém o **Andes** como sua linguagem/design system; referências públicas do Andes reforçam componentes reutilizáveis, views não monolíticas e separação entre UI e lógica de negócio.

---

## 1. Direção Visual

A interface deve parecer:

- marketplace;
- confiável;
- funcional;
- moderna;
- informacionalmente densa, porém organizada;
- simples de operar;
- orientada à tarefa.

Evitar estética de dashboard corporativo genérico, excesso de gráficos, glassmorphism, gradientes decorativos, sombras pesadas e cards excessivamente arredondados.

A identidade pública do Mercado Livre é fortemente associada ao amarelo da marca e ao azul das ações digitais. Como referência visual secundária, usar os tokens abaixo.

---

## 2. Paleta

### Brand

```css
--color-brand-yellow: #FFE600;
--color-brand-blue: #3483FA;
--color-brand-navy: #2D3277;
--color-white: #FFFFFF;
```

### Actions

```css
--color-action-primary: #3483FA;
--color-action-primary-hover: #2968C8;
--color-action-primary-active: #1F4E96;
```

### Surfaces

```css
--color-background: #EEEEEE;
--color-surface: #FFFFFF;
--color-surface-subtle: #F5F5F5;
--color-surface-highlight: #FFF9CC;
```

### Text

```css
--color-text-primary: #333333;
--color-text-secondary: #666666;
--color-text-muted: #999999;
--color-text-disabled: #CCCCCC;
--color-text-inverse: #FFFFFF;
--color-text-link: #3483FA;
```

### Semantic

```css
--color-success: #00A650;
--color-warning: #A6600A;
--color-error: #F23D4F;
--color-info: #3483FA;
```

**Regra:** componentes devem consumir tokens; não espalhar hexadecimais pelo código.

### Uso

- **Amarelo:** identidade/header/destaques; não é o CTA padrão.
- **Azul:** ações primárias, links e elementos interativos.
- **Verde:** sucesso, desconto, benefício e disponibilidade.
- **Vermelho:** erro, cancelamento e ações destrutivas.
- **Amarelo claro:** alertas e destaques contextuais.

---

## 3. Tipografia

Preferir Proxima Nova quando disponível; caso contrário:

```css
font-family:
  "Proxima Nova",
  -apple-system,
  BlinkMacSystemFont,
  "Segoe UI",
  Roboto,
  Arial,
  sans-serif;
```

Hierarquia inicial:

| Uso | Tamanho |
|---|---:|
| Display | 40px |
| H1 | 32px |
| H2 | 28px |
| H3 | 24px |
| H4 | 20px |
| Subtitle | 16–18px |
| Body | 14–16px |
| Caption | 12px |

Não misturar famílias tipográficas sem necessidade.

---

## 4. Espaçamento e Shape

Escala base:

```text
4 / 8 / 12 / 16 / 24 / 32 / 48 / 64
```

Border radius:

```text
4px — pequenos controles
6px — inputs/buttons
8px — cards/containers
999px — pills/badges
```

Preferir bordas e diferenças de superfície a sombras.

---

## 5. Layout

Desktop:

```text
Header
────────────────────────
Main container
Título/contexto
Filtros/ações
Conteúdo
```

Referência inicial:

```css
max-width: 1200px;
margin-inline: auto;
padding-inline: 24px;
```

Telas operacionais podem usar maior largura quando a densidade de informação justificar.

Não criar uma tela cheia de cards se uma lista/tabela for mais eficiente.

---

## 6. Header

Conceito:

```text
┌──────────────────────────────────────────────────────────────┐
│ Market Hub       [ Buscar...                     ]   🔔  👤 │
└──────────────────────────────────────────────────────────────┘
```

Priorizar identidade, busca/contexto, notificações e usuário.

Não sobrecarregar o header.

---

## 7. Buyer / Seller / Ops

### Buyer

Orientado à compra:

```text
Catalog → Product → Offer → Buy → Order → Communication
```

Priorizar produto, preço, oferta, quantidade e acompanhamento.

### Seller

Orientado à operação:

```text
Orders → Order Item → Conversation / Support
```

Priorizar pedidos, status, buyer, produto, valor e comunicação.

### Ops

Orientado à triagem:

```text
Queue → Conversation → Order Item → Priority / Support
```

Priorizar prioridade, idade, contexto e ação.

---

## 8. Componentes

Base inicial:

```text
Button
Input
Select
Badge
Card
Dialog
Dropdown
Tabs
Table
Pagination
Toast
Alert
Skeleton
Spinner
EmptyState
ErrorState
Avatar
Tooltip
```

Criar somente o necessário. Procurar reutilização antes de criar novos componentes.

---

## 9. Botões

### Primary
Azul. Para Comprar, Confirmar, Enviar, Salvar e ação principal.

### Secondary
Branco + borda. Para ações secundárias.

### Tertiary
Texto/link. Para ações auxiliares.

### Destructive
Vermelho. Para cancelar e ações irreversíveis.

Não usar amarelo como CTA padrão apenas para aumentar a semelhança visual.

---

## 10. Ícones

Usar **uma única biblioteca de ícones** no projeto, preferencialmente uma biblioteca de ícones simples/outline com stroke consistente.

Sugestões:

| Função | Ícone |
|---|---|
| Buscar | Search |
| Notificações | Bell |
| Usuário | User |
| Pedidos | Package / ShoppingBag |
| Produto | Box |
| Mensagem | MessageCircle |
| Suporte | LifeBuoy |
| Filtro | SlidersHorizontal |
| Voltar | ArrowLeft |
| Fechar | X |
| Mais | MoreHorizontal |
| Status positivo | CheckCircle |
| Cancelamento | XCircle |
| Prioridade | AlertTriangle |

Não misturar bibliotecas sem necessidade.

Ícone isolado exige contexto óbvio ou `aria-label`/tooltip.

---

## 11. Status e Priority

Status deve usar **texto + cor**, nunca apenas cor:

```text
● Preparando
● Em trânsito
✓ Entregue
× Cancelado
```

Priority:

```text
LOW      → neutro
MEDIUM   → atenção moderada
HIGH     → destaque
CRITICAL → destaque forte
```

A prioridade exibida deve vir do backend. O frontend nunca deve recalculá-la.

---

## 12. Cards, Tables e Lists

Cards devem agrupar informação relacionada, não existir apenas por estética.

Para Orders/Ops, usar tabela quando aumentar a eficiência:

```text
Order | Product | Buyer | Status | Value
```

No mobile, transformar tabelas densas em listas/cards quando necessário.

---

## 13. Conversation

A comunicação Buyer ↔ Seller deve permanecer contextual ao Order Item.

```text
┌─────────────────────────────────────────────┐
│ Buyer / Order Item        Status: Open      │
├─────────────────────────────────────────────┤
│ Buyer                         10:32          │
│ Não recebi meu pedido.                      │
│                                             │
│ Seller                        10:35          │
│ Vou verificar.                              │
├─────────────────────────────────────────────┤
│ [Digite sua mensagem...]             [Enviar]│
└─────────────────────────────────────────────┘
```

Deixar inequívoco quem enviou cada mensagem.

---

## 14. Internal Support

Internal Comments devem possuir aparência diferente da Conversation Buyer ↔ Seller.

Nunca permitir confusão entre:

- comunicação externa;
- comunicação Seller ↔ Ops.

---

## 15. Notifications

Discretas e acionáveis:

```text
🔔 3
```

Ao abrir:

```text
Notificações

Pedido #123 atualizado
Seu pedido está em trânsito.

Conversation atualizada
O Seller respondeu.
```

Cada notificação deve navegar para seu contexto quando houver entidade relacionada.

---

## 16. Loading / Empty / Error

Toda jornada deve tratar:

### Loading
Skeleton/spinner apropriado.

### Empty
Explicar o estado e, quando possível, oferecer próxima ação.

### Error
Mensagem humana + recuperação:

```text
Não foi possível carregar os pedidos.

[Tentar novamente]
```

Nunca expor stack trace ou detalhes internos da API.

Mutations devem comunicar:

```text
Idle → Loading → Success/Error
```

---

## 17. Accessibility

Acessibilidade é requisito funcional.

Aplicar:

- HTML semântico;
- labels persistentes;
- `aria-label` quando necessário;
- foco visível;
- teclado;
- contraste adequado;
- mensagens de erro associadas;
- status não comunicados apenas por cor;
- áreas clicáveis adequadas.

O Mercado Livre declara publicamente investimento em acessibilidade em seus produtos, incluindo suporte para necessidades visuais e motoras.

---

## 18. Responsive

### Desktop
Priorizar tabelas, grids, múltiplas colunas e filtros.

### Mobile
Priorizar listas/cards, conteúdo essencial, ações principais e filtros em drawer/sheet.

Mobile não deve ser apenas um desktop comprimido.

---

## 19. UX Rules

Sempre:

1. priorizar a ação principal;
2. manter informação relevante próxima da ação;
3. evitar navegação desnecessária;
4. dar feedback de operações assíncronas;
5. preservar contexto;
6. evitar modais quando inline/drawer for melhor;
7. confirmar ações destrutivas;
8. manter estados visíveis;
9. usar linguagem clara;
10. favorecer reconhecimento em vez de memorização.

---

## 20. Regras para o agente

Antes de implementar qualquer tela:

1. Ler esta skill.
2. Procurar componentes existentes.
3. Reutilizar design tokens.
4. Não adicionar cores arbitrárias.
5. Não adicionar nova biblioteca de ícones sem justificativa.
6. Não adicionar biblioteca visual sem necessidade.
7. Não copiar telas do Mercado Livre literalmente.
8. Não usar logos/assets proprietários do Mercado Livre.
9. Manter componentes pequenos.
10. Manter lógica de negócio fora dos componentes visuais.
11. Não duplicar regras do backend.
12. Tratar loading/empty/error.
13. Considerar responsive.
14. Considerar accessibility.
15. Revisar hierarquia, espaçamento, contraste e densidade antes de finalizar.

---

## 21. Definition of Done Visual

Uma tela está pronta quando:

- possui hierarquia clara;
- usa tokens;
- segue a paleta;
- usa linguagem única de ícones;
- possui loading/empty/error quando aplicável;
- possui feedback de mutations;
- funciona em desktop;
- possui comportamento mobile adequado;
- possui foco/teclado;
- não depende apenas de cor;
- não possui decoração sem função;
- não duplica regra de negócio;
- é consistente com as demais telas.

---

## 22. Diretriz Final

O objetivo não é criar um clone do Mercado Livre.

O objetivo é criar uma interface que transmita:

> **marketplace moderno + confiança + clareza + eficiência operacional + familiaridade visual com o ecossistema Mercado Livre.**

A inspiração deve vir de princípios visuais e de UX, não de cópia literal.

Quando houver conflito entre semelhança visual e boa UX, **boa UX vence**.

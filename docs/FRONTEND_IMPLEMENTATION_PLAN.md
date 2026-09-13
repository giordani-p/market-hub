# Market Hub — Plano de Implementação do Frontend

## 1. Objetivo

Implementar o frontend do Market Hub de forma incremental, partindo do backend já concluído e evitando antecipar complexidade que ainda não seja necessária.

Stack definida:

- React
- TypeScript
- Backend consumido via API REST
- Frontend orientado às jornadas reais de Seller e Ops

O frontend deve funcionar como uma camada de experiência sobre o domínio já implementado no backend, mantendo o backend como fonte de verdade para regras de negócio, autorização, estados e decisões operacionais.

---

## 2. Contexto do Backend

O backend já possui os principais domínios necessários para a experiência do produto:

- Identity & Access
- Catalog
- Orders
- Communication
- Support / Operations
- Priority / Queue
- Background Processing
- Notifications

As principais jornadas disponíveis são:

### Seller

- Autenticação
- Consulta dos próprios Order Items
- Busca, filtros e paginação
- Visualização do detalhe de um Order Item
- Atualização de status
- Cancelamento quando permitido
- Comunicação Buyer ↔ Seller por Conversation
- Consulta e envio de Internal Comments para Ops
- Recebimento de notificações in-app

### Ops

- Acesso à fila operacional
- Consulta de Conversations abertas
- Visualização de contexto do Seller, Buyer, Product e Order Item
- Consulta de prioridade efetiva
- Override para `critical`, quando aplicável
- Justificativa do override através de Internal Comment
- Consulta e envio de Internal Comments
- Navegação para o contexto operacional relacionado

---

# 3. Estratégia de Implementação

A implementação será dividida em fases pequenas e verificáveis.

A regra geral será:

> **Uma fase por vez → implementar → testar → validar → só então avançar.**

Não devemos construir o frontend inteiro antecipadamente.

Cada fase deverá produzir uma evolução funcional do produto e deixar uma base estável para a próxima.

### Ordem proposta

```text
F0 — Frontend Foundation
        ↓
F1 — Buyer Catalog + Purchase
        ↓
F2 — Seller Orders
        ↓
F3 — Order Item + Communication
        ↓
F4 — Ops Experience
        ↓
F5 — Notifications
        ↓
F6 — UX Polish + Integration
```

---

# 4. F0 — Frontend Foundation

## Objetivo

Criar a fundação técnica e visual do frontend.

## Escopo

- Inicialização/configuração do projeto React + TypeScript
- Estrutura inicial de diretórios
- Configuração de routing
- Configuração do cliente HTTP/API
- Configuração de environment variables
- Modelo inicial de autenticação
- Persistência segura do estado necessário para sessão
- Layout principal da aplicação
- Navegação base
- Estrutura para Seller e Ops
- Componentes UI compartilhados essenciais
- Estados básicos de:
  - loading
  - error
  - empty
- Tratamento inicial de erros da API
- Configuração inicial de lint/testes, se necessária

## Resultado esperado

Ao final da F0 deve existir uma aplicação navegável, com estrutura suficiente para receber as jornadas de negócio sem precisar reorganizar o projeto posteriormente.

A F0 não deve implementar funcionalidades completas de Orders, Conversations ou Ops.

---

# 6. F1 — Buyer Catalog + Purchase

## Objetivo

Construir a jornada inicial do Buyer: descobrir um produto, selecionar uma oferta e iniciar um pedido.

## Jornada

```text
Login
  ↓
Catalog
  ↓
Product / Offer
  ↓
Create Order
  ↓
Order created
```

## Escopo

### Catalog

- Listagem de produtos disponíveis
- Busca e/ou filtros conforme os contratos existentes
- Visualização de produto
- Visualização das ofertas disponíveis

### Purchase

- Seleção de oferta
- Definição da quantidade, quando aplicável
- Criação do pedido
- Feedback de sucesso
- Navegação para o contexto do pedido criado

### Order

O frontend deve refletir o pedido criado pelo Buyer e os respectivos Order Items retornados pelo backend.

O preço apresentado durante a compra deve representar a oferta utilizada naquele momento. Depois da criação, o Order Item deve ser tratado conforme o valor histórico retornado pelo backend.

## Resultado esperado

O Buyer consegue realizar a jornada fundamental do produto:

> "Encontrar um produto → escolher uma oferta → criar um pedido → acompanhar o resultado."

---

# 7. F2 — Seller Orders

## Objetivo

Construir a primeira jornada operacional completa do Seller.

## Jornada

```text
Login
  ↓
Orders
  ↓
Busca / filtros
  ↓
Paginação
  ↓
Selecionar Order Item
```

## Escopo

### Orders List

- Listagem dos Order Items do Seller autenticado
- Busca por identificador
- Filtro por status
- Filtro por período
- Paginação
- Ordenação conforme contrato da API
- Loading state
- Empty state
- Error state

### Navegação

Cada item da lista deve permitir acesso ao detalhe do Order Item.

## Integração

Consumir:

- `GET /v1/order-items`

A implementação deve respeitar os parâmetros e contratos existentes na API.

## Resultado esperado

O Seller consegue entrar no sistema e responder:

> "Quais pedidos estão sob minha responsabilidade e qual é o estado atual de cada item?"

---

# 8. F3 — Order Item + Communication

## Objetivo

Transformar o Order Item em centro da operação do Seller.

## Jornada

```text
Orders
  ↓
Order Item
  ├── Dados do pedido
  ├── Status
  ├── Produto
  ├── Buyer
  ├── Conversation
  └── Internal Support
```

## Escopo

### Order Item Detail

Exibir:

- Produto
- Buyer
- Contexto do pedido
- Preço histórico do item
- Quantidade
- Status
- Informações relevantes disponíveis pela API

A UI deve refletir o status retornado pelo backend.

### Status

Permitir:

- Atualização de status quando disponível
- Cancelamento quando permitido

A validação definitiva das transições permanece no backend.

### Conversation

- Listar Conversations relacionadas ao Order Item
- Identificar Conversation aberta
- Visualizar histórico
- Enviar mensagens
- Exibir status da Conversation
- Permitir fechamento quando o usuário for Seller
- Carregamento progressivo do histórico

### Internal Support

- Listar Internal Comments
- Enviar Internal Comment
- Separar visualmente comunicação interna de comunicação com Buyer

A comunicação interna nunca deve ser apresentada como mensagem do Buyer.

## Resultado esperado

O Seller consegue resolver a maior parte da operação de um Order Item sem sair do seu contexto.

---

# 9. F4 — Ops Experience

## Objetivo

Construir a experiência operacional de suporte.

## Jornada

```text
Ops
  ↓
Queue
  ↓
Conversation
  ↓
Order Item context
  ↓
Priority / Support
```

## Escopo

### Ops Queue

- Listagem de Conversations abertas
- Ordenação pela prioridade efetiva retornada pelo backend
- Visualização de:
  - Seller
  - Buyer
  - Product
  - Order Item
  - Status
  - Purchase Price
  - Priority
- Filtros disponíveis na API
- Paginação

A UI não deve recalcular a prioridade.

### Conversation Detail

- Histórico da Conversation
- Contexto do Order Item
- Seller
- Buyer
- Product
- Status
- Prioridade efetiva

### Priority

Exibir:

- Prioridade calculada
- Override de Ops, quando existente
- Prioridade efetiva

Quando aplicável, permitir alteração para `critical`.

### Critical Override

- Solicitar justificativa
- Enviar a ação ao backend
- Refletir a nova prioridade retornada pela API

A justificativa deve permanecer registrada como Internal Comment conforme o contrato do backend.

### Internal Comments

- Consulta
- Criação
- Separação clara da conversa Buyer ↔ Seller

## Resultado esperado

Ops consegue identificar, priorizar e tratar as Conversations que exigem intervenção sem depender de regras duplicadas no frontend.

---

# 10. F5 — Notifications

## Objetivo

Adicionar notificações in-app como mecanismo transversal da aplicação.

## Escopo

- Indicador de notificações não lidas
- Lista/dropdown de notificações
- Estado lido/não lido
- Ação de marcar como lida
- Ação de marcar todas como lidas, se disponível no contrato da API
- Navegação para a entidade relacionada
- Tratamento de notificações de Seller e Buyer conforme o usuário autenticado

## Deep Linking

As notificações devem utilizar as informações de entidade fornecidas pelo backend para direcionar o usuário ao contexto correto.

Exemplo conceitual:

```text
Notification
   ↓
entity_type
entity_id
   ↓
Frontend Route
   ↓
Order Item / Conversation
```

O frontend não deve reconstruir títulos ou mensagens de negócio quando esses dados forem fornecidos pelo backend.

## Resultado esperado

O usuário consegue perceber mudanças relevantes e navegar diretamente para o contexto que exige atenção.

---

# 11. F6 — UX Polish + Integration

## Objetivo

Consolidar a aplicação antes da entrega final.

## Escopo

### UX

- Responsive behavior
- Melhorias de navegação
- Feedback visual de ações
- Skeletons/loading states
- Empty states
- Error states
- Confirmações para ações destrutivas
- Feedback de sucesso
- Tratamento de erros de validação
- Estados disabled durante operações
- Consistência visual

### Accessibility

- Navegação por teclado
- Labels adequados
- Estados de foco
- Contraste
- Feedback acessível para erros e ações

### Integração

Validar jornadas completas:

```text
Seller
Login
  ↓
Orders
  ↓
Order Item
  ↓
Status
  ↓
Conversation
  ↓
Internal Support
  ↓
Notifications
```

E:

```text
Ops
Login
  ↓
Queue
  ↓
Conversation
  ↓
Priority
  ↓
Critical Override
  ↓
Internal Support
```

### Testes

Adicionar/ajustar:

- Unit tests
- Component tests
- Integration tests
- E2E para jornadas críticas, conforme necessidade

## Resultado esperado

Frontend integrado e pronto para demonstração/avaliação, com as principais jornadas funcionando de ponta a ponta.

---

# 12. Navegação Proposta

A navegação deve refletir os contextos do produto.

## Buyer

```text
┌──────────────────────────────┐
│ Market Hub        🔔  User   │
├──────────────────────────────┤
│ Catalog                      │
│ My Orders                    │
│                              │
│                              │
└──────────────────────────────┘
```

A navegação do Buyer deve priorizar descoberta de produtos, compra e acompanhamento dos próprios pedidos.

## Seller

```text
┌──────────────────────────────┐
│ Market Hub        🔔  User   │
├──────────────────────────────┤
│ Orders                       │
│                              │
│                              │
│                              │
└──────────────────────────────┘
```

A comunicação deve permanecer fortemente contextualizada ao Order Item.

Uma área dedicada de Conversations pode existir futuramente caso seja necessária, mas não deve ser criada apenas porque existe um endpoint de Conversation.

## Ops

```text
┌──────────────────────────────┐
│ Market Hub        🔔  User   │
├──────────────────────────────┤
│ Operations                   │
│   Queue                      │
│                              │
│                              │
└──────────────────────────────┘
```

A experiência de Ops deve ser separada da experiência operacional do Seller.

---

# 11. Princípios de Arquitetura Frontend

## 11.1 Backend como fonte de verdade

O frontend deve:

- consultar dados
- apresentar dados
- enviar comandos
- controlar navegação
- controlar estados de interface

O frontend não deve duplicar:

- regras de autorização
- regras definitivas de transição de status
- cálculo de prioridade
- cálculo de prioridade efetiva
- regras de fechamento automático
- regras de negócio de notificações
- regras de domínio

---

## 11.2 Feature-oriented architecture

A organização deve favorecer domínio/feature:

```text
src/
├── app/
│   ├── router/
│   ├── providers/
│   └── layout/
│
├── features/
│   ├── auth/
│   ├── orders/
│   ├── conversations/
│   ├── support/
│   ├── ops/
│   └── notifications/
│
├── components/
│   ├── ui/
│   ├── feedback/
│   └── navigation/
│
├── lib/
│   ├── api/
│   ├── auth/
│   └── utils/
│
├── types/
│
└── styles/
```

Essa estrutura é uma referência inicial e poderá ser ajustada durante a F0 caso o projeto existente recomende outra organização mais simples.

---

# 12. Integração com a API

O frontend deve utilizar os contratos existentes do backend como referência.

As integrações devem ser organizadas de maneira consistente:

```text
UI
 ↓
Feature
 ↓
API Client
 ↓
HTTP
 ↓
Backend
```

Os tipos TypeScript devem representar os contratos consumidos pela aplicação.

Sempre que possível:

- evitar tipos duplicados
- centralizar tratamento de erros
- centralizar configuração HTTP
- manter endpoints organizados por domínio

---

# 13. Estado da Aplicação

A estratégia deve começar simples.

Prioridade:

1. Estado local do componente quando suficiente
2. Estado da feature quando necessário
3. Estado compartilhado apenas quando realmente necessário
4. Estado global somente para preocupações genuinamente globais

Não introduzir uma solução complexa de gerenciamento de estado antes de existir necessidade real.

---

# 14. Loading, Empty e Error States

Todas as jornadas principais devem considerar explicitamente:

### Loading

Enquanto dados estão sendo carregados.

### Empty

Quando a API retorna uma coleção vazia.

Exemplo:

> Nenhum pedido encontrado.

### Error

Quando a operação falha.

O erro deve fornecer feedback compreensível e, quando possível, uma ação de recuperação.

### Mutation feedback

Operações como:

- alterar status
- cancelar pedido
- enviar mensagem
- fechar Conversation
- adicionar Internal Comment
- alterar prioridade

devem possuir feedback claro de processamento, sucesso ou falha.

---

# 15. Responsabilidade do Frontend x Backend

| Responsabilidade | Frontend | Backend |
|---|---|---|
| Renderizar dados | ✓ | |
| Navegação | ✓ | |
| Loading/Error/Empty | ✓ | |
| Formatação visual | ✓ | |
| Autorização definitiva | | ✓ |
| Status válido | | ✓ |
| Transição de status | | ✓ |
| Cálculo de prioridade | | ✓ |
| Effective priority | | ✓ |
| Fechamento automático | | ✓ |
| Geração de notificações | | ✓ |
| Persistência | | ✓ |
| Regras de domínio | | ✓ |

O frontend pode antecipar feedback de interface, mas a resposta final do backend sempre prevalece.

---

# 16. Estratégia de Desenvolvimento

Cada fase deverá seguir o mesmo ciclo:

```text
1. Revisar contrato/API existente
        ↓
2. Definir UX da fase
        ↓
3. Criar Spec da fase
        ↓
4. Implementar no Cursor
        ↓
5. Executar testes
        ↓
6. Validar integração com backend
        ↓
7. Revisar UX
        ↓
8. Commit
        ↓
9. Próxima fase
```

Não avançar para a próxima fase enquanto a anterior estiver estruturalmente instável.

---

# 17. Definition of Done Global

O frontend será considerado concluído quando:

- Buyer consegue autenticar
- Buyer consegue navegar pelo catálogo
- Buyer consegue visualizar produtos e ofertas
- Buyer consegue criar um pedido
- Buyer consegue acompanhar seus pedidos
- Buyer consegue acessar a comunicação relacionada aos seus pedidos
- Seller consegue autenticar
- Seller consegue consultar seus Order Items
- Seller consegue filtrar e navegar pelos pedidos
- Seller consegue visualizar detalhes
- Seller consegue executar ações permitidas sobre o Order Item
- Seller consegue conversar com Buyer
- Seller consegue utilizar o suporte interno
- Ops consegue acessar sua fila
- Ops consegue tratar Conversations
- Ops consegue trabalhar com prioridade
- Ops consegue registrar suporte interno
- Usuários recebem notificações in-app relevantes
- Notificações permitem navegação para o contexto relacionado
- Estados de loading/empty/error estão tratados
- Interface possui comportamento responsivo adequado
- Jornadas críticas estão testadas
- Frontend está integrado ao backend sem duplicação indevida das regras de negócio

---

# 18. Regra para as próximas Specs

Este documento define **o roadmap**, não a implementação detalhada.

As próximas Specs devem ser criadas individualmente:

```text
FRONTEND_F0_SPEC.md
        ↓
implementação + validação
        ↓
FRONTEND_F1_SPEC.md
        ↓
implementação + validação
        ↓
FRONTEND_F2_SPEC.md
        ↓
...
```

Cada Spec deve conter apenas o nível de detalhe necessário para implementar aquela fase, incluindo:

- objetivo
- contexto
- escopo
- fora de escopo
- UX
- rotas
- componentes
- contratos de API envolvidos
- estados
- comportamento
- critérios de aceite
- testes
- Definition of Done
- instruções específicas para implementação no Cursor

A intenção é manter o desenvolvimento **incremental, verificável e alinhado ao backend existente**, evitando overengineering e decisões prematuras.

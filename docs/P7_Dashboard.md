# Market Hub — Dashboard Specification

## 1. Objetivo

Implementar uma capability de Dashboard simples, funcional e orientada à ação para os três atores do Market Hub:

- Buyer
- Seller
- Ops

O Dashboard deve responder rapidamente às principais perguntas operacionais de cada ator:

### Seller

> Como está minha operação e existe algo que precisa da minha atenção?

### Buyer

> Como estão minhas compras?

### Ops

> O que precisa da minha atenção agora?

O Dashboard **não deve ser transformado em uma solução de analytics**.

Não fazem parte do MVP:

- gráficos;
- analytics históricos;
- faturamento;
- ticket médio;
- conversão;
- ranking;
- metas;
- forecasting;
- comparação entre períodos;
- scoring proprietário.

---

# 2. Princípios Arquiteturais

## 2.1 Dashboard não é um novo domínio

Não criar:

- `DashboardEntity`
- `DashboardAggregate`
- `DashboardRepository` de persistência
- tabela `dashboard`
- estado persistido específico do Dashboard

O Dashboard é uma **capability de leitura** que projeta dados dos domínios existentes.

Conceitualmente:

```text
Orders
Communication
Support / Priority
       │
       ▼
Dashboard Query
       │
       ▼
Read Projection
       │
       ▼
Dashboard API
```

---

## 2.2 DDD

Os domínios existentes continuam sendo responsáveis por seus próprios conceitos e regras.

O Dashboard apenas compõe uma visão de leitura.

Não duplicar no Dashboard:

- regras de status;
- regras de autorização;
- cálculo de prioridade;
- cálculo de effective priority;
- regras de Conversation;
- regras de cancelamento;
- regras de Order;
- regras de notificação.

---

## 2.3 API First

A API do Dashboard deve ser definida como uma superfície de leitura própria.

Endpoint:

```http
GET /v1/dashboard
```

O frontend não deve montar o Dashboard fazendo múltiplas chamadas independentes para Orders, Conversations etc.

A API deve fornecer uma projeção adequada à tela.

---

# 3. Atores

## 3.1 Seller

O Seller trabalha operacionalmente sobre `Order Items`.

A unidade operacional do Dashboard do Seller deve ser:

```text
Order Item
```

Não substituir essa abstração por `Order`.

---

## 3.2 Buyer

O Buyer pensa sua jornada em termos de:

```text
Order
```

Portanto, o Dashboard do Buyer deve trabalhar com Orders.

---

## 3.3 Ops

Ops trabalha principalmente com:

```text
Conversation
Priority
Queue
```

A visão do Dashboard de Ops deve aproveitar as mesmas regras da fila operacional existente.

---

# 4. Modelo Conceitual

A resposta do Dashboard possui três áreas conceituais:

```text
Dashboard
├── Summary
├── Attention
└── Recent
```

Essas áreas são conceitos de apresentação/read model, não entidades de domínio.

---

# 5. Seller Dashboard

## 5.1 Summary

O Seller deve visualizar:

```text
total_order_items
active_order_items
order_items_by_status
```

### Total Order Items

Pergunta:

> Quantos Order Items pertencem à minha operação?

Regra:

```text
COUNT(OrderItem)
WHERE seller_id = authenticated_user.id
```

---

## 5.2 Active Order Items

Considerar ativos:

```text
placed
preparing
in_transit
```

Regra:

```text
COUNT(OrderItem)
WHERE seller_id = authenticated_user.id
AND status IN (
    placed,
    preparing,
    in_transit
)
```

Não considerar ativos:

```text
delivered
cancelled
```

---

## 5.3 Order Items by Status

Retornar contagens para todos os estados:

```text
placed
preparing
in_transit
delivered
cancelled
```

Mesmo que uma contagem seja `0`.

Exemplo:

```json
{
  "placed": 2,
  "preparing": 8,
  "in_transit": 3,
  "delivered": 10,
  "cancelled": 1
}
```

---

## 5.4 Attention

Para Seller:

```text
open_conversations
```

Regra:

```text
COUNT(Conversation)
WHERE seller_id = authenticated_user.id
AND status = open
```

Não criar uma regra adicional de "conversation atrasada" ou "aguardando resposta" sem suporte explícito do domínio.

---

## 5.5 Recent

Mostrar os **5 últimos Order Items**.

Sem filtro temporal.

Regra:

```text
seller_id = authenticated_user.id
ORDER BY created_at DESC
LIMIT 5
```

Cada item deve conter somente informações necessárias para a apresentação:

```json
{
  "order_item_id": "uuid",
  "order_id": "uuid",
  "product": {
    "id": "uuid",
    "name": "Notebook"
  },
  "buyer": {
    "id": "uuid",
    "name": "Buyer"
  },
  "quantity": 1,
  "purchase_price": 2300.00,
  "status": "preparing",
  "created_at": "2026-09-14T01:20:00Z"
}
```

`purchase_price` representa o valor histórico do item no momento da compra.

Nunca reconstruir esse valor a partir do preço atual do Product/Offer.

---

# 6. Buyer Dashboard

## 6.1 Summary

O Buyer deve visualizar:

```text
active_orders
completed_orders
```

---

## 6.2 Active Orders

Uma Order é considerada ativa quando possui pelo menos um Order Item ainda em andamento.

Estados ativos:

```text
placed
preparing
in_transit
```

Exemplo:

```text
Order
├── Item A → delivered
└── Item B → in_transit

=> Order ativa
```

---

## 6.3 Completed Orders

Uma Order é considerada concluída quando todos os seus Order Items estão em estado final de entrega:

```text
delivered
```

Exemplo:

```text
Order
├── Item A → delivered
└── Item B → delivered

=> Order concluída
```

Uma Order com múltiplos itens deve continuar sendo contada como **uma Order**, não como vários pedidos.

---

## 6.4 Attention

Mostrar:

```text
open_conversations
```

Regra:

```text
COUNT(Conversation)
WHERE buyer_id = authenticated_user.id
AND status = open
```

O Buyer nunca deve receber informações de Internal Comments ou dados internos de Ops.

---

## 6.5 Recent

Mostrar os **5 últimos Orders**.

Sem filtro temporal.

Regra:

```text
buyer_id = authenticated_user.id
ORDER BY created_at DESC
LIMIT 5
```

Exemplo conceitual:

```json
{
  "order_id": "uuid",
  "created_at": "2026-09-14T01:20:00Z",
  "status": "in_progress",
  "total_amount": 2420.00,
  "items": [
    {
      "order_item_id": "uuid",
      "product": {
        "id": "uuid",
        "name": "Notebook"
      },
      "quantity": 1,
      "status": "in_transit"
    }
  ]
}
```

Não retornar informações internas de Seller ou Ops.

---

# 7. Ops Dashboard

## 7.1 Summary

Mostrar:

```text
open_conversations
conversations_by_priority
```

---

## 7.2 Open Conversations

Regra:

```text
COUNT(Conversation)
WHERE status = open
```

Considerar somente Conversations disponíveis para o contexto de Ops.

---

## 7.3 Conversations by Priority

Retornar:

```text
critical
high
medium
low
```

Exemplo:

```json
{
  "critical": 2,
  "high": 7,
  "medium": 10,
  "low": 4
}
```

A prioridade deve utilizar o conceito já existente de:

```text
effective_priority
```

Não criar uma nova regra de prioridade para o Dashboard.

---

# 8. Ops Attention

A seção de atenção do Ops será:

```text
priority_queue_preview
```

Limite:

```text
5
```

Ordenação:

```text
effective_priority DESC
last_interaction_at DESC
```

Essa ordenação deve ser a mesma utilizada pela Ops Queue.

O objetivo é permitir que Ops identifique rapidamente os primeiros casos que exigem tratamento.

---

# 9. Ops Queue Preview Item

A projeção deve conter o contexto necessário para triagem.

Exemplo:

```json
{
  "conversation_id": "uuid",
  "order_item_id": "uuid",
  "effective_priority": "critical",
  "calculated_priority": "high",
  "ops_override": "critical",
  "reason": "atraso",
  "last_interaction_at": "2026-09-14T01:45:00Z",
  "seller": {
    "id": "uuid",
    "name": "Seller"
  },
  "buyer": {
    "id": "uuid",
    "name": "Buyer"
  },
  "product": {
    "id": "uuid",
    "name": "Notebook"
  },
  "order_item_status": "in_transit",
  "purchase_price": 2300.00
}
```

Não retornar transcript de Messages.

O Dashboard deve fornecer contexto suficiente para triagem e navegação, não substituir a Conversation Detail.

---

# 10. API Contract

## Endpoint

```http
GET /v1/dashboard
```

Headers:

```http
Authorization: Bearer <token>
```

Sem body.

Sem query parameters no MVP.

Não aceitar:

```text
seller_id
buyer_id
ops_id
date_from
date_to
page
page_size
```

O contexto deve ser derivado do usuário autenticado.

---

# 11. Response

Estrutura geral:

```json
{
  "role": "seller",
  "summary": {},
  "attention": {},
  "recent": {}
}
```

O conteúdo varia de acordo com a role autenticada.

---

# 12. Seller Response

```json
{
  "role": "seller",
  "summary": {
    "total_order_items": 24,
    "active_order_items": 13,
    "order_items_by_status": {
      "placed": 2,
      "preparing": 8,
      "in_transit": 3,
      "delivered": 10,
      "cancelled": 1
    }
  },
  "attention": {
    "open_conversations": 3
  },
  "recent": {
    "order_items": []
  }
}
```

---

# 13. Buyer Response

```json
{
  "role": "buyer",
  "summary": {
    "active_orders": 2,
    "completed_orders": 8
  },
  "attention": {
    "open_conversations": 1
  },
  "recent": {
    "orders": []
  }
}
```

---

# 14. Ops Response

```json
{
  "role": "ops",
  "summary": {
    "open_conversations": 23,
    "conversations_by_priority": {
      "critical": 2,
      "high": 7,
      "medium": 10,
      "low": 4
    }
  },
  "attention": {
    "priority_queue_preview": []
  },
  "recent": {}
}
```

Para Ops, não é necessário criar uma seção `recent` genérica.

A fila prioritária já representa a informação operacional mais relevante.

---

# 15. Empty State da API

O endpoint deve retornar `200 OK` mesmo quando o usuário não possui dados.

Exemplo Seller sem pedidos:

```json
{
  "role": "seller",
  "summary": {
    "total_order_items": 0,
    "active_order_items": 0,
    "order_items_by_status": {
      "placed": 0,
      "preparing": 0,
      "in_transit": 0,
      "delivered": 0,
      "cancelled": 0
    }
  },
  "attention": {
    "open_conversations": 0
  },
  "recent": {
    "order_items": []
  }
}
```

O frontend será responsável pela apresentação do Empty State.

---

# 16. HTTP Errors

## 401

Usuário não autenticado:

```http
401 Unauthorized
```

## 403

Usuário autenticado, porém sem role/contexto permitido:

```http
403 Forbidden
```

Não criar códigos de erro específicos do Dashboard sem necessidade.

Erros de infraestrutura devem seguir o padrão já utilizado pela API.

---

# 17. Application Architecture

A implementação deve seguir aproximadamente:

```text
HTTP
 │
 ▼
Dashboard Router
 │
 ▼
DashboardQueryService
 │
 ├── Seller Dashboard Query
 ├── Buyer Dashboard Query
 └── Ops Dashboard Query
 │
 ▼
Read Projection
 │
 ▼
Dashboard Response
```

---

# 18. DashboardQueryService

Criar um Application Service de leitura equivalente conceitualmente a:

```text
DashboardQueryService
```

Responsabilidade:

```text
get_dashboard(current_user)
```

O serviço deve:

1. receber o usuário autenticado;
2. determinar a role/contexto;
3. executar a query apropriada;
4. montar a projeção;
5. retornar o response DTO.

---

# 19. Queries por Contexto

Conceitualmente:

```text
SellerDashboardQuery
BuyerDashboardQuery
OpsDashboardQuery
```

Cada uma deve conhecer somente os dados necessários para sua projeção.

### Seller

```text
Order Items
Conversations
```

### Buyer

```text
Orders
Conversations
```

### Ops

```text
Conversations
Priority
Order Item context
```

Não criar dependências desnecessárias entre os bounded contexts.

---

# 20. Persistência

Não criar persistência própria para Dashboard.

Não criar:

```text
dashboard table
dashboard entity
dashboard migration
```

As informações devem ser derivadas dos dados existentes.

---

# 21. Queries de Leitura

Queries agregadas devem ser executadas preferencialmente no banco.

Evitar:

```text
buscar todos os registros
↓
carregar em Python
↓
fazer COUNT/GROUP BY em memória
```

Preferir queries agregadas.

Exemplo conceitual:

```sql
COUNT(*)
GROUP BY status
```

---

# 22. N+1

Evitar N+1 queries.

Especialmente para:

```text
Recent Order Items
Ops Queue Preview
Buyer Recent Orders
```

Não fazer:

```text
buscar 5 items
↓
para cada item:
  buscar product
  buscar buyer
  buscar order
```

Preferir uma projeção/query que obtenha os dados necessários de forma eficiente.

---

# 23. DTOs

Criar DTOs específicos para o Dashboard.

Não reutilizar automaticamente DTOs completos de outras APIs apenas para evitar criar novos modelos.

A resposta deve conter somente dados necessários para o Dashboard.

Estrutura conceitual:

```text
DashboardResponse
├── role
├── summary
├── attention
└── recent
```

Os DTOs concretos podem ser especializados por role caso isso produza um contrato mais seguro e legível.

---

# 24. Autorização

O escopo deve ser sempre derivado do usuário autenticado.

### Seller

```text
seller_id = authenticated_user.id
```

### Buyer

```text
buyer_id = authenticated_user.id
```

### Ops

Visão operacional autorizada.

Nunca confiar em IDs fornecidos pelo cliente para determinar o escopo.

---

# 25. Performance

O objetivo do endpoint é produzir o Dashboard completo em uma única requisição.

Não exigir que o frontend faça:

```text
GET /order-items
GET /orders
GET /conversations
GET /ops/conversations
...
```

para montar a tela.

Internamente podem existir múltiplas queries ao banco, desde que sejam eficientes e justificadas.

Não adicionar cache no MVP.

Não adicionar Redis especificamente para o Dashboard.

---

# 26. Cache

Não implementar cache inicialmente.

A estratégia inicial é:

```text
Request
 ↓
Optimized read queries
 ↓
Projection
 ↓
Response
```

Cache só deve ser considerado posteriormente se houver evidência de necessidade.

---

# 27. Frontend

A implementação visual do Dashboard será feita posteriormente em uma fase própria do frontend.

Esta Spec deve produzir primeiro:

```text
Domain
↓
Application
↓
API
↓
Tests
```

Somente depois:

```text
Frontend Dashboard
```

A UI deverá consumir o contrato da API e não reconstruir regras de negócio.

---

# 28. Frontend Responsibility

O frontend pode:

- apresentar métricas;
- apresentar listas;
- apresentar status;
- apresentar prioridade;
- criar links/deep links;
- tratar loading;
- tratar empty;
- tratar error;
- formatar datas;
- formatar valores;
- apresentar feedback.

O frontend não pode:

- recalcular prioridade;
- determinar active/completed com regras próprias;
- recalcular status;
- determinar authorization;
- reconstruir regras de domínio.

---

# 29. Testes

## 29.1 Unit Tests

Testar as regras de projeção:

### Seller

- total de Order Items;
- active Order Items;
- contagem por status;
- Conversations abertas;
- limite de 5 recentes;
- ordenação dos recentes.

### Buyer

- Orders ativas;
- Orders concluídas;
- Conversations abertas;
- limite de 5 Orders recentes;
- ordenação.

### Ops

- Conversations abertas;
- distribuição por prioridade;
- limite de 5 na queue preview;
- ordenação por effective priority;
- desempate por last interaction.

---

# 30. Integration Tests

Validar:

```text
Database
 ↓
Dashboard Query
 ↓
Dashboard Projection
```

Cobrir:

- Seller com dados;
- Seller sem dados;
- Buyer com dados;
- Buyer sem dados;
- Ops com dados;
- Ops sem dados;
- múltiplos Order Items na mesma Order;
- múltiplos Sellers na mesma Order;
- Conversations com diferentes prioridades.

---

# 31. API Tests

Testar:

```http
GET /v1/dashboard
```

para:

- Buyer;
- Seller;
- Ops;
- usuário não autenticado;
- role não autorizada;
- isolamento entre usuários.

Exemplo de isolamento:

```text
Seller A
→ somente seus Order Items

Seller B
→ somente seus Order Items
```

Nunca permitir vazamento de dados entre Sellers/Buyers.

---

# 32. Edge Cases

A implementação deve considerar:

### Seller sem Order Items

Retornar contagens `0` e lista vazia.

### Seller sem Conversations

`open_conversations = 0`.

### Buyer sem Orders

Contagens `0` e lista vazia.

### Buyer com Order contendo múltiplos Items

Contar a Order uma única vez.

### Ops sem Conversations abertas

Contagens de prioridade `0` e preview vazio.

### Mais de 5 itens recentes

Retornar somente 5.

### Mais de 5 Conversations na fila

Retornar somente 5 no preview.

### Prioridade Critical

Utilizar `effective_priority`, respeitando override existente.

---

# 33. Definition of Done

A feature de backend do Dashboard estará concluída quando:

- [ ] `GET /v1/dashboard` estiver implementado;
- [ ] contexto for determinado pelo JWT;
- [ ] Seller receber somente seus dados;
- [ ] Buyer receber somente seus dados;
- [ ] Ops receber sua visão operacional autorizada;
- [ ] Seller Summary estiver implementado;
- [ ] Seller Attention estiver implementado;
- [ ] Seller Recent estiver implementado;
- [ ] Buyer Summary estiver implementado;
- [ ] Buyer Attention estiver implementado;
- [ ] Buyer Recent estiver implementado;
- [ ] Ops Summary estiver implementado;
- [ ] Ops Attention estiver implementado;
- [ ] limite de 5 estiver respeitado;
- [ ] ordenações estiverem corretas;
- [ ] prioridade efetiva não for recalculada pelo Dashboard;
- [ ] não existir persistência específica do Dashboard;
- [ ] não existir agregado `Dashboard`;
- [ ] não houver N+1 evidente;
- [ ] testes unitários estiverem implementados;
- [ ] testes de integração estiverem implementados;
- [ ] testes de API estiverem implementados;
- [ ] OpenAPI estiver atualizado;
- [ ] lint passar;
- [ ] suite existente continuar passando;
- [ ] migrations existentes permanecerem compatíveis;
- [ ] nenhuma regra de domínio existente for duplicada ou alterada sem justificativa.

---

# 34. Instruções para o Cursor

Antes de implementar:

1. Inspecione a estrutura atual do backend.
2. Leia as implementações existentes de Orders, Communication, Support e Priority.
3. Leia os testes existentes desses domínios.
4. Leia `api/openapi.yaml`.
5. Identifique os padrões atuais de Router, Application Service, Repository, DTO e testes.
6. Não introduza uma arquitetura paralela se a estrutura atual já possuir um padrão equivalente.
7. Adapte `DashboardQueryService` aos padrões existentes.
8. Não criar um novo agregado de domínio.
9. Não criar tabela ou migration específica para Dashboard.
10. Não implementar CQRS formal.
11. Não implementar cache.
12. Não adicionar infraestrutura nova sem necessidade.
13. Evitar N+1.
14. Utilizar queries agregadas no banco quando apropriado.
15. Não alterar regras de domínio existentes.
16. Atualizar `api/openapi.yaml`.
17. Implementar testes antes de considerar a feature concluída.
18. Executar lint e suite completa.
19. Verificar isolamento de dados por role/usuário.
20. Ao encontrar conflito entre esta Spec e a implementação atual, **não assumir a solução**: primeiro identifique a diferença e preserve os contratos existentes, salvo decisão explícita de alteração.

---

# 35. Ordem de Implementação

A implementação deve seguir esta ordem:

```text
1. Inspeção do backend existente
        ↓
2. Confirmar arquitetura atual
        ↓
3. Definir DTOs
        ↓
4. Implementar Seller Query
        ↓
5. Implementar Buyer Query
        ↓
6. Implementar Ops Query
        ↓
7. Implementar DashboardQueryService
        ↓
8. Implementar Router
        ↓
9. Atualizar OpenAPI
        ↓
10. Unit Tests
        ↓
11. Integration Tests
        ↓
12. API Tests
        ↓
13. Lint
        ↓
14. Full Test Suite
```

---

# 36. Resultado esperado

Ao final desta implementação teremos uma nova capability:

```text
GET /v1/dashboard
```

capaz de fornecer uma visão simples e contextual para:

```text
Buyer
Seller
Ops
```

sem criar um novo domínio ou persistência específica.

A arquitetura final esperada é:

```text
                         GET /v1/dashboard
                                  │
                                  ▼
                         Dashboard Router
                                  │
                                  ▼
                       DashboardQueryService
                                  │
                 ┌────────────────┼────────────────┐
                 ▼                ▼                ▼
           Seller Query      Buyer Query       Ops Query
                 │                │                │
                 ▼                ▼                ▼
              Orders       Orders + Comm.    Comm. + Priority
                 │                │                │
                 └────────────────┼────────────────┘
                                  ▼
                           Read Projection
                                  │
                                  ▼
                         Dashboard Response
```

O Dashboard deve permanecer pequeno, rápido, previsível e orientado à ação.

> **Não queremos um dashboard que mostre tudo. Queremos um dashboard que mostre o que importa.**
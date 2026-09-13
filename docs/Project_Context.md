# Market Hub — Contexto do Projeto

## 1. Visão Geral

Este projeto é a solução para o desafio Full-Stack:

**"Market Hub: Pedidos e Perguntas"**

O desafio solicita uma aplicação que ajude vendedores a centralizar a operação de pedidos e a comunicação com compradores sobre dúvidas ou problemas relacionados às compras.

O enunciado deixa decisões de produto e arquitetura em aberto de propósito. A solução deve explicitar essas decisões de forma simples, coerente e justificável.

> **Nota de stack:** A direção tecnológica definida para este projeto é **Python FastAPI no backend** e **React + TypeScript no frontend**.

O documento deve ser tratado como **contexto-base do produto, dos domínios e do system design inicial**. Ele não descreve o que já foi implementado nem define a sequência de implementação das fases.

---

## 2. Problema de Negócio

A PM, Clara, apresenta três problemas principais:

1. Vendedores não têm um único lugar para entender o que está acontecendo com seus pedidos.
2. Dúvidas e problemas dos compradores são tratados por threads de e-mail, sem contexto centralizado na compra.
3. Operações precisa saber quais questões não resolvidas devem receber atenção primeiro, mas o negócio não definiu exatamente o que significa "importante".

O produto deve ser:

> **Simples, útil, compreensível e extensível — sem overengineering para o contexto do desafio.**

---

## 3. Objetivos do Produto

### 3.1 Gestão de pedidos pelo Seller

O sistema deve permitir que um Seller:

- visualize seus pedidos;
- identifique o Buyer;
- visualize os itens comprados;
- veja quantidades;
- veja o preço praticado no momento da compra;
- acompanhe o status dos Order Items;
- pesquise e filtre sua operação;
- consulte o contexto necessário para atuar sobre um pedido.

O domínio deve suportar pedidos com múltiplos itens e preservar o preço histórico praticado na compra.

---

### 3.2 Comunicação Buyer ↔ Seller

Buyers e Sellers devem poder se comunicar de forma contextualizada por um **Order Item**.

O sistema deve permitir:

- iniciar uma Conversation;
- visualizar Conversations;
- enviar Messages;
- consultar histórico;
- encerrar uma Conversation quando aplicável.

A comunicação deve preservar o contexto da compra, evitando uma thread independente do pedido.

A experiência completa de frontend do Buyer não é requisito central do desafio; o domínio, entretanto, deve suportar a participação do Buyer na comunicação.

---

### 3.3 Suporte / Operations

Operations deve possuir uma capacidade própria para apoiar a operação do Seller.

O sistema deve permitir:

- consultar contexto operacional;
- trocar comentários internos com o Seller;
- acompanhar questões que demandam atenção;
- utilizar uma política explícita de prioridade para identificar o que merece atenção primeiro.

A comunicação interna entre Ops e Seller deve ser separada da comunicação Buyer ↔ Seller.

---

### 3.4 Priorização

O sistema deve possuir uma política de prioridade:

- determinística;
- transparente;
- explicável;
- fácil de alterar.

A prioridade deve ajudar Operations a identificar Conversations que merecem atenção.

A política deve considerar o contexto da Conversation e do Order Item, sem depender de IA ou de regras opacas.

---

## 4. Usuários / Atores

### Seller

É o principal usuário operacional do produto.

Precisa:

- acompanhar pedidos;
- consultar detalhes de Order Items;
- visualizar e responder Conversations;
- acompanhar suporte interno;
- atuar sobre questões prioritárias.

### Buyer

É participante da compra e da comunicação com o Seller.

Pode:

- iniciar Conversations;
- consultar suas Conversations;
- enviar Messages;
- consultar o histórico permitido.

A experiência completa do Buyer não é o foco principal do produto.

### Operations / Ops

É um usuário operacional responsável por suporte e priorização.

Pode:

- consultar recursos necessários para suporte;
- criar e consultar InternalComments;
- interagir internamente com Sellers;
- aplicar ou remover um override operacional de prioridade.

Ops **não é um superusuário** e não deve assumir automaticamente as responsabilidades de Seller ou Buyer.

---

## 5. Escopo do Produto

A jornada principal do produto é a operação do Seller:

```text
Seller
  |
  +--> Orders
  |      |
  |      +--> Search / Filters
  |      |
  |      +--> Order Item
  |              |
  |              +--> Product
  |              +--> Buyer
  |              +--> Status
  |              +--> Conversation
  |              |       |
  |              |       +--> Messages
  |              |       +--> Close
  |              |
  |              +--> Internal Comments
  |
  +--> Operational Context
         |
         +--> Conversations
         +--> Priority
         +--> Support
```

O produto não pretende construir uma plataforma completa de marketplace. O foco é resolver a operação de pedidos, comunicação contextualizada e suporte operacional.

---

## 6. Domínios Propostos

A organização conceitual inicial é:

```text
Identity & Access
Catalog
Orders
Communication
Support / Operations
```

### 6.1 Identity & Access

Responsável por:

- identidade do usuário;
- autenticação;
- autorização;
- papéis de Buyer, Seller e Ops;
- isolamento de recursos conforme o papel e as relações do usuário.

A identidade usada para autorização deve vir do contexto autenticado, e não de identificadores fornecidos pelo cliente.

---

### 6.2 Catalog

Responsável por:

- Products;
- associação de Products a Sellers;
- preço atual do catálogo;
- disponibilidade/estado do produto.

O preço atual do Product não deve ser usado para reconstruir o histórico de uma compra.

---

### 6.3 Orders

Responsável por:

- Orders;
- Order Items;
- relação entre Buyer, Seller e itens;
- ciclo de vida dos Order Items;
- quantidade;
- preço histórico da compra;
- regras operacionais do pedido, incluindo transições de status e cancelamento.

O **Order Item é a principal unidade operacional** para a jornada do Seller.

O Order fornece contexto agregado; o Order Item representa a unidade específica sobre a qual a operação acontece.

---

### 6.4 Communication

Responsável pela comunicação **Buyer ↔ Seller**.

Modelo conceitual:

```text
Order
  |
  +--> Order Item
          |
          +--> Conversation
                  |
                  +--> Message
```

Uma Conversation é contextualizada por um Order Item.

Um Order Item pode possuir várias Conversations ao longo do tempo, mas apenas uma Conversation pode estar `OPEN` simultaneamente.

Estados da Conversation:

```text
OPEN
CLOSED
```

Uma Conversation fechada não é reaberta. Uma nova necessidade de comunicação pode originar uma nova Conversation.

Messages são textuais e imutáveis.

A Conversation possui um reason que ajuda a contextualizar a necessidade do contato, como atraso, troca, devolução, reclamação, suporte, elogio ou outros.

---

### 6.5 Support / Operations

Responsável pelas necessidades internas de suporte e operação.

Modelo conceitual:

```text
Support / Operations
  |
  +--> Ops
  |
  +--> InternalComment
  |
  +--> PriorityPolicy
```

#### InternalComment

`InternalComment` representa comunicação interna entre Seller e Ops.

Características:

- pertence diretamente a um Order Item;
- é independente de uma Buyer ↔ Seller Conversation;
- Seller e Ops podem criar/consultar conforme autorização;
- Buyer não possui acesso;
- é textual e imutável;
- serve também como registro de contexto operacional.

Não é necessário criar uma Conversation para uma interação interna entre Seller e Ops.

#### PriorityPolicy

`PriorityPolicy` define a regra determinística usada para calcular a prioridade de uma Conversation.

A Policy pertence conceitualmente a Support / Operations, mas utiliza informações de Communication e Orders como entrada.

---

## 7. Modelo de Domínio Inicial

Modelo conceitual:

```text
User
├── Buyer
├── Seller
└── Ops

Seller
  |
  +----< Product
  |
  +----< Order >---- Buyer
              |
              +----< OrderItem >---- Product
                         |
                         +----< Conversation
                         |          |
                         |          +----< Message
                         |
                         +----< InternalComment
```

### User

Representa a identidade autenticada do sistema.

Os papéis principais são:

```text
BUYER
SELLER
OPS
```

### Product

Representa um produto pertencente ao catálogo de um Seller.

Conceitualmente possui:

```text
id
seller_id
name
category
price
active
created_at
```

### Order

Representa a compra e fornece contexto agregado.

Conceitualmente possui:

```text
id
buyer_id
status/contexto operacional
total_amount
created_at
updated_at
```

### OrderItem

Representa um item específico da compra.

Conceitualmente possui:

```text
id
order_id
product_id
quantity
purchase_price
```

`purchase_price` representa o preço histórico praticado no momento da compra.

### Conversation

Representa uma interação Buyer ↔ Seller contextualizada por um Order Item.

Conceitualmente possui:

```text
id
order_item_id
reason
status
calculated_priority
ops_override
created_at
last_interaction_at
```

### Message

Representa uma mensagem de uma Conversation.

Conceitualmente possui:

```text
id
conversation_id
author_id
author_type
content
created_at
```

Os autores relevantes são Buyer e Seller; mensagens de sistema podem existir para eventos operacionais da Conversation.

### InternalComment

Representa uma interação interna entre Seller e Ops.

Conceitualmente possui:

```text
id
order_item_id
author_id
author_type
content
created_at
```

`author_type` representa `SELLER` ou `OPS`.

---

## 8. Regras de Negócio Principais

### 8.1 Order Items

Um Order pode possuir um ou vários Order Items.

Cada Order Item possui:

- Product;
- quantidade;
- preço histórico;
- status próprio.

O preço atual do catálogo pode mudar sem alterar o preço histórico da compra.

---

### 8.2 Conversation

Uma Conversation pertence a um único Order Item.

Um Order Item pode possuir várias Conversations ao longo do tempo, mas somente uma pode estar `OPEN`.

Estados:

```text
OPEN
CLOSED
```

A criação de uma Conversation deve reutilizar a Conversation aberta existente quando aplicável, evitando duas Conversations abertas simultaneamente para o mesmo Order Item.

---

### 8.3 Messages

Messages:

- pertencem a uma Conversation;
- possuem autor;
- possuem texto;
- são imutáveis;
- não são editadas ou removidas.

A Conversation deve manter histórico suficiente para que Buyer e Seller entendam o contexto da interação.

---

### 8.4 Internal Comments

InternalComments:

- pertencem diretamente a Order Items;
- são independentes das Conversations;
- são acessíveis apenas a Seller e Ops autorizados;
- não são visíveis ao Buyer;
- são imutáveis.

---

## 9. Estratégia de Priorização

A prioridade é uma capacidade de Support / Operations.

A V1 utiliza uma política determinística baseada em quatro dimensões:

1. **Conversation reason**
2. **Order Item status**
3. **Conversation age**
4. **Order Item value**

A ideia é produzir uma classificação simples, previsível e explicável.

### 9.1 Reason

Pesos iniciais:

```text
atraso       = 1.00
reclamacao   = 0.75
troca        = 0.50
devolucao    = 0.50
suporte      = 0.40
outros       = 0.25
elogio       = 0.00
```

### 9.2 Order Item status

Pesos iniciais:

```text
in_transit   = 1.00
preparing    = 0.75
placed       = 0.50
delivered    = 0.25
cancelled    = 0.00
```

### 9.3 Conversation age

Pesos iniciais:

```text
< 4h          = 0.00
4h – 12h      = 0.25
12h – 24h     = 0.50
24h – 48h     = 0.75
> 48h         = 1.00
```

### 9.4 Order Item value

Pesos iniciais:

```text
< R$100          = 0.00
R$100 – 499      = 0.25
R$500 – 999      = 0.50
R$1.000 – 4.999  = 0.75
>= R$5.000       = 1.00
```

### 9.5 Score

```text
priority_score =
    reason_score
  + status_score
  + age_score
  + value_score
```

Score máximo:

```text
4.00
```

Classificação:

```text
0.00 – 1.00  → LOW
>1.00 – 2.25 → MEDIUM
>2.25        → HIGH
```

Esses pesos e limites são uma decisão inicial de produto e devem permanecer fáceis de alterar.

---

## 10. Operational Override

A classificação calculada não deve impedir uma decisão operacional excepcional.

Ops pode aplicar manualmente:

```text
ops_override = CRITICAL
```

Nesse caso:

```text
effective_priority =
    ops_override ?? calculated_priority
```

Ou seja:

```text
calculated_priority = HIGH
ops_override        = CRITICAL
effective_priority  = CRITICAL
```

O override:

- é aplicado somente por Ops autorizado;
- exige uma justificativa;
- a justificativa é registrada como `InternalComment`;
- não altera a `calculated_priority`;
- pode ser removido posteriormente;
- quando removido, a prioridade calculada volta a ser efetiva;
- permanece no histórico o registro da decisão operacional.

A Policy nunca deve remover ou alterar automaticamente um override existente.

---

## 11. System Design Inicial

A arquitetura deve permanecer simples e adequada ao escopo.

```text
React + TypeScript
        |
        | REST / HTTP
        v
Python API
        |
        +--> Identity & Access
        |
        +--> Catalog
        |
        +--> Orders
        |
        +--> Communication
        |
        +--> Support / Operations
        |
        v
Relational Database
```

As regras de negócio devem permanecer no domínio/aplicação e não depender do frontend.

A comunicação entre domínios deve respeitar suas responsabilidades.

### Priority

Conceitualmente:

```text
Conversation
     |
     +--> PriorityPolicy
              |
              +--> Conversation reason
              +--> Order Item status
              +--> Conversation age
              +--> Order Item value
              |
              v
       calculated_priority
              |
              +--> Ops override
              |
              v
       effective_priority
```

A prioridade pertence à Conversation porque representa a prioridade daquela necessidade de comunicação, enquanto o Order Item fornece o contexto operacional usado para calculá-la.

### Persistência

A prioridade calculada deve ser persistida para facilitar:

- consulta;
- ordenação;
- filtros;
- destaque operacional;
- futuras integrações.

Os mecanismos automáticos de atualização dessa informação são uma preocupação de evolução e não fazem parte da definição conceitual da Policy.

---

## 12. Direção Tecnológica

### Backend

```text
Python
```

O backend expõe uma API REST.

### Frontend

```text
React
TypeScript
```

### Banco de dados

A solução utiliza um banco relacional como direção arquitetural.

A escolha específica do banco e das bibliotecas de persistência pode ser definida durante a implementação.

---

## 13. Extensibilidade e Evolução Futura

A solução deve deixar espaço para evolução sem antecipar complexidade desnecessária.

Possíveis evoluções:

### Automação de prioridade

A prioridade calculada pode ser atualizada automaticamente quando houver mudanças relevantes, como:

- novas Messages;
- alteração do status do Order Item;
- passagem de tempo;
- outros eventos operacionais.

### Notificações

Prioridades relevantes podem futuramente alimentar mecanismos de notificação ao Seller ou a Operations.

O canal pode evoluir independentemente da regra de prioridade:

```text
Notification
   |
   +--> Email
   +--> Slack
   +--> SMS
```

### Suporte automatizado

No futuro, uma Conversation pode ser atendida inicialmente por automação/IA e encaminhada para suporte humano quando necessário.

Isso não exige alterar o ciclo de vida atual da Conversation:

```text
OPEN
CLOSED
```

Um eventual conceito de `support_mode` ou mecanismo equivalente pode ser introduzido posteriormente se houver necessidade real.

### SLA

SLA pode ser introduzido posteriormente para atendimento humano/operacional.

Não faz parte do núcleo atual da Conversation ou da PriorityPolicy.

---

## 14. Princípios de Design

### Simplicidade

Resolver o problema proposto sem construir uma plataforma completa de marketplace.

### Domínios claros

Cada domínio deve possuir responsabilidades bem definidas:

```text
Identity & Access
→ identidade e autorização

Catalog
→ produtos e catálogo

Orders
→ pedidos e itens

Communication
→ Buyer ↔ Seller

Support / Operations
→ suporte interno e priorização
```

### Regras de negócio explícitas

Regras importantes devem ser visíveis, testáveis e independentes da interface.

### Order Item como unidade operacional

O Order Item deve ser utilizado como contexto central para as operações específicas de uma compra.

### Extensibilidade onde existe necessidade

Principalmente:

- PriorityPolicy;
- suporte operacional;
- futuros canais de notificação;
- futura automação/IA.

### Evitar overengineering

Não introduzir complexidade arquitetural sem necessidade concreta.

Não há necessidade inicial de:

- microservices;
- Kafka;
- Kubernetes;
- event sourcing;
- CQRS;
- bancos vetoriais;
- infraestrutura distribuída complexa.

### Decisões justificáveis

Quando o requisito permitir diferentes interpretações, a solução deve deixar claro:

- o que foi decidido;
- por que foi decidido;
- quais trade-offs existem;
- como a decisão poderia evoluir.

---

## 15. Definição de Sucesso

A solução deve permitir demonstrar claramente que:

1. O Seller consegue entender sua operação de pedidos em um único lugar.
2. Orders suportam múltiplos Order Items e preservam preços históricos.
3. A comunicação fica contextualizada pelo Order Item.
4. Buyer e Seller conseguem trocar Messages dentro de Conversations.
5. Conversations possuem ciclo de vida claro.
6. Seller e Ops conseguem manter comunicação interna separada da comunicação com o Buyer.
7. Ops consegue identificar Conversations prioritárias por uma política determinística.
8. A prioridade é explicável e pode receber override operacional.
9. O desenho permite evolução para automação, notificações e suporte humano sem exigir uma reestruturação completa do domínio.
10. A arquitetura permanece simples, clara e adequada ao contexto do desafio.

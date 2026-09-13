# P3 — Seller Journey

## Objetivo
Implementar a jornada operacional do Seller sobre os `Order Items` das suas próprias Offers.

A P3 materializa as capacidades já definidas no domínio de Orders na P2, sem criar novas regras de negócio e sem antecipar Communication.

O `Order Item` é a unidade principal da jornada do Seller. O `Order` aparece apenas como contexto complementar.

## Escopo
1. Consulta dos `Order Items` do Seller.
2. Paginação, filtros e busca.
3. Detalhe de um `Order Item`.
4. Alteração normal de status.
5. Cancelamento.
6. Isolamento/autorização por Seller.
7. Tratamento de concorrência.
8. Testes e integração com eventos existentes.

Não implementar frontend, Dashboard/Reporting ou Communication.

## 1. Listagem

### Endpoint
`GET /v1/order-items`

### Autorização
O Seller é identificado pelo JWT. O backend deriva o Seller autenticado do token e nunca aceita `seller_id` enviado pelo cliente como fonte de autorização.

Retornar somente `Order Items` associados a Offers daquele Seller.

### Parâmetros
- `page`
- `page_size`
- `status`
- `from`
- `to`
- `order_item_id`

Todos opcionais.

### Paginação
- padrão: 20 itens;
- máximo: 100 itens.

### Filtros
`status` filtra o status atual do Order Item.

`from` e `to` filtram por `OrderItem.created_at`.

Os filtros são combináveis.

`order_item_id` é um filtro da própria listagem. Não criar endpoint separado. Como o ID é único, retorna no máximo um item, respeitando isolamento e demais filtros.

### Ordenação
Padrão: `created_at DESC`.

### Nenhum resultado
Retornar `200 OK` com lista vazia e metadados de paginação.

Exemplo:
```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

## 2. Payload da listagem

Payload enxuto, suficiente para o Seller localizar o item e decidir se precisa executar uma ação:

- `order_item_id`
- produto (identificação/nome)
- `quantity`
- `purchase_price`
- `status`
- `created_at`
- buyer: `id`, `name`
- `order_id`

Não incluir a Offer completa.

## 3. Detalhe

### Endpoint
`GET /v1/order-items/{item_id}`

O Seller pode chegar ao detalhe pela listagem ou diretamente pelo ID.

Payload:

- `id`
- `quantity`
- `purchase_price`
- `status`
- `created_at`
- `updated_at`
- Product: `id`, `name` e demais informações relevantes já existentes
- Buyer: `id`, `name`
- Order: `id`, `created_at`

Não misturar o estado atual da Offer com o contexto histórico da venda. Não retornar a Offer completa; quando necessário, disponibilizar apenas uma referência para consulta separada.

## 4. Isolamento do Seller

Todas as consultas e operações devem respeitar o Seller autenticado.

```text
JWT
 ↓
Seller autenticado
 ↓
Order Item pertence a Offer desse Seller?
 ├── Sim → operação permitida
 └── Não → 404 Not Found
```

Seller tentando acessar ou operar item de outro Seller recebe `404 Not Found`, sem revelar a existência do recurso.

## 5. Alteração normal de status

### Endpoint
`PATCH /v1/order-items/{item_id}`

Body:
```json
{
  "status": "preparing"
}
```

O backend:
1. identifica o Seller pelo JWT;
2. localiza o item dentro do escopo do Seller;
3. revalida o estado atual;
4. valida a transição;
5. executa a alteração;
6. retorna o item atualizado.

Transições normais:
```text
placed → preparing
preparing → in_transit
in_transit → delivered
```

Transições inválidas retornam `409 Conflict`.

Se o status solicitado já for o atual, a operação é idempotente e não produz efeitos adicionais.

## 6. Cancelamento

### Endpoint
`POST /v1/order-items/{item_id}/cancel`

`cancelled` é um status, mas o cancelamento é uma operação específica por possuir regras e efeitos próprios.

| Status | Seller pode cancelar? | Estoque restaurado? |
|---|---:|---:|
| `placed` | Sim | Sim |
| `preparing` | Sim | Sim |
| `in_transit` | Sim | Não |
| `delivered` | Não | Não |
| `cancelled` | Não | Não |

Quando permitido, alteração de status e restauração de estoque devem ser atômicas.

Cancelamento repetido de item já `cancelled` deve ser idempotente e não produzir efeitos adicionais.

Cancelamento em estado não permitido retorna `409 Conflict`.

## 7. Concorrência

Alterações de status devem revalidar o estado atual dentro da transação.

Se outro request alterar o item antes da execução, a transição deve ser validada contra o estado atual.

Se a transição não for mais válida, retornar `409 Conflict`.

Não introduzir versionamento ou optimistic locking nesta etapa.

## 8. Respostas

Alteração de status: `200 OK` com Order Item atualizado.

Cancelamento: `200 OK` com Order Item atualizado.

## 9. Erros

Reutilizar o padrão de erros da P2:

| Situação | HTTP |
|---|---:|
| Seller não autenticado | `401 Unauthorized` |
| Item inexistente ou de outro Seller | `404 Not Found` |
| Transição inválida | `409 Conflict` |
| Cancelamento não permitido | `409 Conflict` |
| Payload inválido | `422 Unprocessable Entity` |

Não criar nova convenção de erros.

## 10. Eventos

Manter:
- `OrderCreated`
- `OrderItemStatusChanged`
- `OrderItemCancelled`

Publicar eventos somente após commit bem-sucedido.

Não implementar consumidores, notificações ou novos mecanismos de eventos.

## 11. Communication

Fora do escopo.

Preservar o `Order Item` como contexto futuro:

```text
Order → Order Item → Conversation → Messages
```

Não criar entidades, endpoints ou regras de Communication.

## 12. Dashboard / Reporting

Fora do escopo da P3.

Indicadores e KPIs serão tratados posteriormente, potencialmente como domínio próprio.

## 13. Atualização

A atualização da lista será feita por consulta/refresh.

Não implementar WebSocket, SSE ou atualização em tempo real.

## 14. Testes

### Consultas
- Seller lista somente seus itens;
- paginação funciona;
- padrão 20 e máximo 100;
- ordenação `created_at DESC`;
- filtros de status e período;
- combinação de filtros;
- busca por `order_item_id`;
- lista vazia retorna `200` com paginação;
- detalhe retorna payload completo;
- acesso a item de outro Seller retorna `404`.

### Operações
- transições válidas;
- transições inválidas → `409`;
- mesma transição repetida é idempotente;
- cancelamento respeita regras;
- cancelamento em `placed` e `preparing` restaura estoque;
- cancelamento em `in_transit` não restaura;
- cancelamento de item entregue é rejeitado;
- cancelamento repetido é idempotente;
- operações sobre item de outro Seller → `404`;
- concorrência revalida estado na transação.

### Segurança
- Seller não consulta dados de outro Seller;
- Seller não opera item de outro Seller;
- `seller_id` não é fonte de autorização;
- todos os endpoints respeitam o Seller do JWT.

### Integração
- eventos existentes continuam funcionando;
- eventos somente após commit;
- nenhuma funcionalidade de Communication é introduzida.

## 15. Critérios de aceite

A P3 estará concluída quando:
1. Seller autenticado listar seus Order Items;
2. listagem possuir paginação, filtros e busca;
3. ordenação padrão for por itens mais recentes;
4. Seller consultar detalhe;
5. Seller alterar status respeitando a máquina de estados;
6. Seller cancelar quando permitido;
7. estoque for restaurado corretamente;
8. isolamento entre Sellers estiver garantido;
9. operações repetidas forem idempotentes;
10. concorrência for tratada pela revalidação transacional;
11. erros estiverem alinhados com P2;
12. eventos forem publicados somente após commit;
13. Communication e Dashboard não forem implementados.

## Princípios
- API First;
- simplicidade;
- baixo acoplamento;
- responsabilidades claras;
- evitar abstrações prematuras;
- backend como fonte de verdade;
- não duplicar regras de domínio no frontend;
- manter o domínio preparado para evolução;
- não implementar funcionalidades fora do escopo por antecipação.

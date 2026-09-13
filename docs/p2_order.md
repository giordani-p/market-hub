# P2 — Order Domain

## Objetivo

Implementar o domínio de pedidos do Marketplace, mantendo a jornada simples e preparando o domínio para evolução futura.

A P2 considera que um pedido pode conter itens de diferentes Sellers. A unidade operacional do pedido é o `Order Item`.

## 1. Modelo de domínio

### Order

Representa uma compra realizada por um Buyer.

Campos:
- `id`
- `buyer_id`
- `created_at`
- `updated_at`

Não adicionar informações desnecessárias ao escopo atual.

### Order Item

Representa cada ocorrência específica de compra dentro de um Order.

Campos:
- `id`
- `order_id`
- `offer_id`
- `quantity`
- `purchase_price`
- `status`
- `created_at`
- `updated_at`

Relação:

`Order → Order Item → Offer → Product + Seller`

Importante:
- `Offer.price` é o preço comercial atual.
- `OrderItem.purchase_price` é o preço efetivamente praticado no momento da compra e fica congelado.
- `Offer.stock` é o estoque atual.
- `OrderItem.quantity` é a quantidade comprada.

## 2. Status do Order Item

O status pertence ao `Order Item`, não ao `Order` nem à `Offer`.

Fluxo normal:

`Realizado → Em preparação → Em trânsito → Entregue`

Estado alternativo final:

`Cancelado`

`Em preparação` representa o aceite do fornecedor e o início do processamento.

O Seller é responsável por evoluir seus próprios itens:

`Realizado → Em preparação → Em trânsito → Entregue`

Um Seller nunca pode alterar Order Items de outro Seller.

## 3. Cancelamento

### Buyer
Pode cancelar enquanto estiver em:
- `Realizado`
- `Em preparação`

Não pode cancelar em `Em trânsito`.

### Seller
Pode cancelar seu Order Item durante toda a jornada, inclusive em `Em trânsito`.

### Estados finais
- `Entregue` não pode ser cancelado.
- `Cancelado` é estado final.

## 4. Estoque

O estoque só é consumido quando a compra é efetivamente finalizada.

Não implementar reserva de estoque durante a navegação do carrinho.

Na compra:

`Offer.stock -= OrderItem.quantity`

No cancelamento:
- Antes de `Em trânsito`: devolver a quantidade ao estoque.
- Em `Em trânsito`: não recompor automaticamente o estoque.

A mudança de status e a atualização de estoque devem ser consistentes e atômicas.

## 5. Finalização da compra

O carrinho envia pelo menos:
- `offer_id`
- `quantity`

O backend deve revalidar as Offers no momento da finalização.

Para cada item:
1. Verificar existência e disponibilidade da Offer.
2. Considerar o preço atual.
3. Verificar estoque suficiente.

Se houver alteração relevante na Offer, como preço ou disponibilidade:
- não efetivar a compra;
- manter o carrinho;
- informar quais itens precisam de ajuste;
- retornar os dados atuais necessários para revisão;
- permitir nova tentativa após ajuste/reconfirmação.

Se todos os itens forem válidos:
1. Criar um único `Order`.
2. Criar um `Order Item` para cada item.
3. Copiar o preço atual da Offer para `purchase_price`.
4. Definir status inicial como `Realizado`.
5. Consumir os respectivos estoques.

## 6. Atomicidade

A criação de um pedido com múltiplos itens deve ser atômica.

Se um único item falhar:
- nenhum item é comprado;
- nenhum estoque é alterado;
- nenhum Order é criado;
- o carrinho permanece disponível;
- o Buyer recebe informação clara sobre o ajuste necessário.

Somente quando todos os itens forem validados a compra deve ser efetivada.

## 7. Concorrência de estoque

A implementação deve evitar overselling em compras simultâneas.

Exemplo: se uma Offer possui estoque 1 e dois Buyers tentam comprar uma unidade simultaneamente, somente uma compra pode ser efetivada.

O consumo deve ser condicional e atômico no PostgreSQL, garantindo estoque suficiente no momento da atualização.

Conceitualmente:

`UPDATE offers SET stock = stock - quantity WHERE id = offer_id AND stock >= quantity`

A aplicação deve verificar o resultado. Se nenhuma linha for afetada, o estoque não é suficiente.

Não introduzir Redis, locks distribuídos ou outra infraestrutura adicional nesta fase.

## 8. Transação

A finalização deve ocorrer dentro de uma transação de banco.

Conceitualmente:

`BEGIN`
- validar Offers;
- consumir estoque de forma segura;
- criar Order;
- criar Order Items;

Sucesso:

`COMMIT`

Falha em qualquer etapa:

`ROLLBACK`

Não permitir compras parciais.

## 9. Escopo do Seller

O Seller pode:
- visualizar seus Products;
- visualizar suas Offers;
- criar/alterar/remover suas Offers;
- visualizar Order Items relacionados às suas Offers;
- evoluir seus Order Items;
- cancelar seus Order Items.

Não pode:
- visualizar Offers de outros Sellers em suas áreas de gestão;
- acessar Order Items de outros Sellers;
- alterar recursos pertencentes a outros Sellers.

### Catálogo público

No contexto de compra, a listagem geral de Offers continua disponível para o Buyer visualizar ofertas de diferentes Sellers.

Essa restrição deve ser garantida pelo backend, não apenas pelo frontend.

## 10. Eventos

O domínio deve ser preparado para eventos de negócio futuros.

Exemplos:
- `OrderCreated`
- `OrderItemStatusChanged`
- `OrderItemCancelled`

Nesta fase não implementar infraestrutura completa de mensageria/event bus.

O objetivo é permitir que futuramente notificações, tratamentos e relatórios possam reagir aos eventos sem acoplamento excessivo ao domínio de Order.

## 11. Princípios

Manter os princípios da P1:
- simplicidade;
- baixo acoplamento;
- alta coesão;
- responsabilidades claras;
- testabilidade;
- capacidade de evolução;
- evitar abstrações prematuras;
- não criar infraestrutura desnecessária.

Integrar à arquitetura existente da P1, preservando seus padrões e decisões.

Não alterar desnecessariamente o domínio de Catalog.

## 12. Critérios funcionais

A P2 estará atendida quando:
- Buyer puder finalizar carrinho com múltiplos itens;
- um Order puder conter itens de diferentes Sellers;
- cada Order Item estiver vinculado à sua Offer;
- preço histórico for preservado;
- estoque for consumido na efetivação;
- concorrência não permitir overselling;
- criação do Order for atômica;
- falha em um item não gerar compra parcial;
- carrinho permanecer disponível após tentativa inválida;
- regras de cancelamento forem respeitadas;
- cancelamentos antes de `Em trânsito` recompuserem estoque;
- Seller só opere sobre seus próprios Order Items;
- evolução de status respeite o fluxo;
- domínio fique preparado para futura publicação de eventos.

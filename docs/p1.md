# Marketplace — Plano de Desenvolvimento v0

## 1. Objetivo

Criar a primeira versão funcional do backend do Marketplace utilizando Python + FastAPI, seguindo uma abordagem API First e uma organização orientada a domínios.

A v0 deve estabelecer uma base simples, organizada e evolutiva para o projeto e implementar o primeiro domínio funcional: **Catálogo**.

O objetivo não é construir o Marketplace completo nesta etapa.

---

## 2. Contexto do domínio

O Marketplace possui três públicos principais:

- Comprador
- Vendedor
- Operação (Ops)

O foco principal da aplicação é a jornada do **Vendedor**.

Comprador e Ops serão desenvolvidos posteriormente na medida necessária para suportar a jornada completa de compra e venda.

Nesta v0, o foco estará exclusivamente no domínio de Catálogo.

---

## 3. Escopo da v0

Implementar:

- Estrutura inicial do backend;
- API REST utilizando FastAPI;
- Domínio de Catálogo;
- Entidades Produto, Oferta e Vendedor;
- CRUD mínimo de Produto;
- CRUD mínimo de Oferta;
- Persistência dos dados;
- Validações básicas;
- Testes automatizados dos principais comportamentos;
- Documentação automática da API através do FastAPI.

Não implementar nesta etapa:

- Pedidos;
- Carrinho;
- Pagamentos;
- Entrega;
- Comunicação entre comprador e vendedor;
- Notificações;
- Tratativas;
- Funcionalidades de Ops;
- Frontend;
- Autenticação/autorização;
- Funcionalidades avançadas de marketplace.

Esses itens serão tratados em etapas posteriores.

---

## 4. Modelo de domínio

### Produto

Produto representa o item comercializado no Marketplace.

O Produto é uma entidade independente do vendedor.

Um mesmo Produto pode possuir ofertas de diferentes vendedores.

O Produto deve conter apenas informações próprias do item comercializado.

Preço e estoque não pertencem ao Produto.

### Vendedor

Vendedor representa o participante responsável pela comercialização de produtos.

Um vendedor pode possuir várias ofertas.

Nesta v0, o Vendedor deve existir de forma mínima apenas para permitir o relacionamento com as Ofertas.

Não implementar ainda funcionalidades completas de gestão de vendedores.

### Oferta

Oferta representa a comercialização de um Produto por um determinado Vendedor.

Uma Oferta relaciona:

- um Produto;
- um Vendedor;
- preço;
- estoque;
- disponibilidade.

Exemplo:

Produto:
> Tênis XYZ

Oferta:
> Vendedor: Loja A  
> Preço: R$ 299,00  
> Estoque: 10  
> Disponível: sim

Outro vendedor pode possuir outra Oferta para o mesmo Produto:

> Vendedor: Loja B  
> Preço: R$ 279,00  
> Estoque: 5  
> Disponível: sim

As ofertas são independentes entre si.

---

## 5. Relacionamentos

O modelo conceitual deve seguir:

- Vendedor 1:N Oferta
- Produto 1:N Oferta

A Oferta é a entidade que conecta Produto e Vendedor.

```text
             Produto
                │
                │ 1:N
                ▼
              Oferta
                ▲
                │ N:1
                │
             Vendedor
```

---

## 6. Responsabilidades

### Produto

Responsável por representar:

- identidade do produto;
- informações próprias do produto.

Não deve ser responsável por:

- preço de venda;
- estoque;
- vendedor;
- disponibilidade comercial.

### Oferta

Responsável por representar:

- vendedor responsável pela oferta;
- produto ofertado;
- preço;
- estoque;
- disponibilidade.

### Vendedor

Responsável por representar a identidade mínima do vendedor necessária para criação e gerenciamento das ofertas.

---

## 7. Casos de uso

### Produto

Implementar:

- Criar Produto;
- Consultar Produto;
- Listar Produtos;
- Atualizar Produto;
- Excluir Produto.

### Oferta

Implementar:

- Criar Oferta;
- Consultar Oferta;
- Listar Ofertas;
- Atualizar Oferta;
- Excluir Oferta.

Também deve ser possível consultar as ofertas relacionadas a um determinado vendedor.

---

## 8. Regras mínimas de negócio

### Produto

- Produto deve possuir identificação válida;
- Não permitir criação de Produto com dados obrigatórios ausentes;
- Não permitir atualização de Produto inexistente;
- Não permitir exclusão de Produto inexistente.

### Oferta

- Uma Oferta deve estar associada a um Produto existente;
- Uma Oferta deve estar associada a um Vendedor existente;
- Preço deve possuir valor válido;
- Estoque não pode ser negativo;
- Oferta deve possuir estado de disponibilidade válido;
- Não permitir atualização de Oferta inexistente;
- Não permitir exclusão de Oferta inexistente.

Regras adicionais não devem ser inventadas nesta etapa.

---

## 9. API

Criar uma API REST para expor os casos de uso do domínio.

A API deve permitir operações relacionadas a:

```text
/products
/offers
```

Os endpoints devem refletir de forma clara os casos de uso definidos anteriormente.

A implementação deve utilizar os recursos nativos do FastAPI para:

- definição das rotas;
- validação das entradas;
- serialização das respostas;
- documentação da API.

A estrutura dos endpoints pode ser definida durante a implementação, desde que mantenha consistência REST e esteja alinhada aos casos de uso.

---

## 10. Organização do projeto

Organizar o código de forma que as responsabilidades estejam claramente separadas.

A estrutura deve facilitar a evolução para novos domínios posteriormente.

A implementação não precisa seguir obrigatoriamente Clean Architecture, Hexagonal Architecture ou qualquer outro padrão específico.

Priorizar:

- simplicidade;
- coesão;
- baixo acoplamento;
- separação clara de responsabilidades;
- facilidade de testes;
- facilidade de evolução.

Evitar abstrações prematuras.

---

## 11. Persistência

A v0 deve possuir persistência real dos dados.

Produtos, vendedores e ofertas não devem depender exclusivamente de memória da aplicação.

A escolha do banco, ORM e estratégia de migrations deve ser feita de forma compatível com os objetivos acima, mantendo a solução simples e adequada ao estágio atual do projeto.

Não criar uma camada de abstração excessiva apenas para antecipar necessidades futuras.

---

## 12. Testes

Criar testes automatizados cobrindo pelo menos:

### Produto

- criação;
- consulta;
- listagem;
- atualização;
- exclusão;
- tentativa de operações sobre produto inexistente.

### Oferta

- criação com Produto válido;
- criação com Vendedor válido;
- criação com relacionamentos inexistentes;
- atualização de preço;
- atualização de estoque;
- atualização de disponibilidade;
- validação de estoque negativo;
- consulta;
- listagem;
- exclusão.

Os testes devem validar principalmente comportamento e regras de negócio, evitando acoplamento desnecessário à implementação interna.

---

## 13. Documentação

A API deve possuir documentação acessível através da documentação automática do FastAPI.

Também criar um README inicial contendo:

- objetivo do projeto;
- escopo da v0;
- como executar o backend;
- como executar os testes;
- como acessar a documentação da API;
- visão simplificada do domínio de Catálogo.

---

## 14. Critérios de conclusão da v0

A v0 será considerada concluída quando:

- o backend FastAPI estiver executando;
- o domínio de Catálogo estiver implementado;
- Produto puder ser criado, consultado, atualizado e excluído;
- Vendedor puder ser utilizado para criação de Ofertas;
- Oferta puder ser criada, consultada, atualizada e excluída;
- Oferta estiver corretamente relacionada a Produto e Vendedor;
- preço, estoque e disponibilidade forem tratados na Oferta;
- os dados forem persistidos;
- validações básicas estiverem funcionando;
- os principais fluxos estiverem cobertos por testes;
- a API estiver documentada;
- o projeto estiver organizado de forma que novos domínios possam ser adicionados posteriormente.

---

## 15. Diretriz para implementação

Implementar a solução de forma incremental.

Não antecipar a implementação dos demais domínios.

Não criar funcionalidades que não sejam necessárias para cumprir o escopo da v0.

Quando houver uma decisão técnica relevante não definida neste documento, interromper a implementação e apresentar as opções antes de decidir.

A prioridade é construir uma primeira versão funcional, simples e bem organizada, que possa evoluir posteriormente para os demais domínios do Marketplace.

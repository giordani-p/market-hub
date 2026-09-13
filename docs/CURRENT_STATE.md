# Estado atual do projeto

- **Versão**: 0.1.0
- **Fase**: v0 (P1) concluída — domínio de Catálogo implementado
- **Commit de referência**: não versionado (repositório sem git até o momento)

## Do que se trata

Backend de um Marketplace em Python com FastAPI. A fase atual, especificada em
`docs/p1.md`, cobre apenas o domínio de Catálogo. O plano da fase não deve ser
copiado para cá: este documento descreve o que **existe hoje**.

## Arquitetura

Aplicação FastAPI única, organizada por domínio e não por camada técnica. Não
há Clean Architecture nem Hexagonal: o plano da fase pede simplicidade e proíbe
abstração prematura. Cada domínio novo entra como um módulo próprio em `app/`.

`app/core/` guarda o que é transversal entre domínios: configuração e tradução
de erros de negócio para resposta HTTP.

## Mapa do código

| Caminho | O que contém |
| --- | --- |
| `app/main.py` | `create_app()`, registro de handlers de erro e inclusão dos routers com o prefixo de versão |
| `app/core/config.py` | `Settings` (pydantic-settings) e `get_settings()` com cache |
| `app/core/errors.py` | `DomainError`, `ResourceNotFoundError`, `ResourceInUseError`, `ErrorResponse` e o handler que os traduz para JSON |
| `app/database.py` | `Base` declarativa, `get_engine()`, `get_session_factory()` e a dependência `get_session()` |
| `app/health.py` | router e schema do health check |
| `app/catalog/models.py` | `Seller`, `Product` e `Offer` (SQLAlchemy) |
| `app/catalog/schemas.py` | request/response Pydantic do Catálogo |
| `app/catalog/products.py` | CRUD de Produto |
| `app/catalog/offers.py` | CRUD de Oferta |
| `app/catalog/seed.py` | vendedores fixos, sem rotas |
| `api/openapi.yaml` | contrato da API escrito à mão |
| `migrations/` | Alembic: `env.py` resolve a URL pelas Settings; `versions/` tem a migration do Catálogo |
| `tests/unit/` | testes sem dependência de aplicação montada |
| `tests/integration/` | testes que sobem a aplicação via `TestClient` |

## Contratos de API

Rotas implementadas, todas sob o prefixo `/v1`:

| Rota | Resposta |
| --- | --- |
| `GET /v1/health` | `HealthResponse` (`status`, `version`) |
| `GET /v1/products` | array de `Product` |
| `POST /v1/products` | `201` + `Product` |
| `GET /v1/products/{product_id}` | `Product` |
| `PATCH /v1/products/{product_id}` | `Product` |
| `DELETE /v1/products/{product_id}` | `204`; `409` se o produto ainda tiver ofertas |
| `GET /v1/offers` | array de `Offer`; filtro opcional `?seller_id=` |
| `POST /v1/offers` | `201` + `Offer`; `404` se produto ou vendedor não existir |
| `GET /v1/offers/{offer_id}` | `Offer` |
| `PATCH /v1/offers/{offer_id}` | `Offer` |
| `DELETE /v1/offers/{offer_id}` | `204` |

Erros de negócio respondem com `ErrorResponse` (`code`, `message`):
`resource_not_found` com status 404 e `resource_in_use` com status 409.

O contrato `api/openapi.yaml` é a fonte da verdade e é escrito antes do código.
`tests/integration/test_openapi_contract.py` compara os paths e métodos do
contrato com o OpenAPI gerado pela aplicação e falha em caso de divergência.

## Decisões de contrato e de stack já tomadas

- Atualização apenas por `PATCH`, com todos os campos opcionais. Não há `PUT`.
- Ofertas de um vendedor por filtro na listagem: `GET /v1/offers?seller_id=`.
  Não existe árvore `/sellers` na v0.
- Preço como string decimal com duas casas (`"299.00"`), mapeado para `Decimal`
  e `NUMERIC(12,2)`.
- Listagens retornam array simples, sem envelope nem paginação.
- Exclusão bem-sucedida responde `204` sem corpo.
- Validação de campo fica com o Pydantic e responde `422` no formato padrão do
  FastAPI. Referência a recurso inexistente responde `404` com `ErrorResponse`
  e `code: resource_not_found`.
- `offers.product_id` e `offers.seller_id` usam `ON DELETE RESTRICT`. Excluir um
  Produto que ainda tem Ofertas responde `409` com `code: resource_in_use`. Não
  há soft delete nem estados extras.
- Persistência: PostgreSQL via docker-compose, SQLAlchemy e Alembic.
- Vendedores criados por seed, sem rotas — o plano pede identidade mínima,
  apenas para permitir o relacionamento com as ofertas.

## Configuração

Lida de variáveis de ambiente, com `.env` local e `.env.example` como
referência: `ENVIRONMENT` (`local`, `staging` ou `production`), `API_PREFIX`,
`DATABASE_URL` e `TEST_DATABASE_URL`. O `docker-compose.yml` consome
`POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_DB`, e falha com mensagem
explícita se alguma estiver ausente. Nenhum valor de credencial existe no
repositório.

## Persistência

PostgreSQL 16 em container local (`docker-compose.yml`, com healthcheck),
SQLAlchemy 2.0 e Alembic. A engine é criada sob demanda, não no import, para
que a aplicação e os testes possam ser importados sem banco disponível.

Tabelas `sellers`, `products` e `offers` existem na migration
`001_create_catalog`. Os testes de Catálogo usam o mesmo Postgres, em um banco
separado (`TEST_DATABASE_URL`). `make db-up` cria esse banco se ele ainda não
existir. `make test` exige o Postgres no ar.

## Convenções

- Gerenciador de pacotes `uv`; comandos de uso comum no `Makefile`
  (`install`, `run`, `lint`, `format`, `test`, `db-up`, `migrate`, `seed`).
- Lint e formatação com `ruff`, linha de 100 colunas.
- Testes com `pytest`, divididos em `tests/unit/` e `tests/integration/`.
- Idioma conforme `.cursor/rules/language-conventions.mdc`: docstrings e
  comentários em português sem acentos, identificadores e contratos em inglês.

## O que ainda não existe

- Repositório git, pipeline de CI e qualquer artefato de deploy.
- Autenticação, autorização e observabilidade.
- Spec da próxima fase (pedidos, carrinho, pagamentos, frontend).
- Soft delete ou diferenciação entre excluir e deixar de disponibilizar.

## Próxima etapa

Definir a spec da fase seguinte do Marketplace. A v0 do Catálogo está
fechada.

## Histórico de versões

- **0.1.0** — domínio de Catálogo implementado: CRUD de Produto e Oferta,
  persistência com FKs `RESTRICT`, seed de vendedores, `409 resource_in_use`
  quando o produto ainda tem ofertas, e testes de comportamento no Postgres
  de teste.
- **0.1.0** — contrato do Catálogo especificado em `api/openapi.yaml` e
  infraestrutura de persistência montada (PostgreSQL em docker-compose,
  SQLAlchemy e Alembic). Rotas ainda não implementadas.
- **0.1.0** — base do backend FastAPI simplificada para o escopo da v0: pacote
  movido para `app/`, remoção das camadas `domain/`, `application/` e
  `infrastructure/`, do logging estruturado, da suíte e2e e do exportador de
  OpenAPI. Mantidos o health check e o teste de contrato.

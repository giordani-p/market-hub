# Marketplace

Backend de um Marketplace, construído com Python e FastAPI seguindo uma
abordagem API First. Projeto de estudo, em fase inicial.

O foco principal da aplicação é a jornada do Vendedor. Comprador e Operação
serão desenvolvidos depois, na medida necessária.

## Escopo da v0

A v0 implementa apenas o domínio de **Catálogo**: as entidades Produto,
Vendedor e Oferta, com CRUD mínimo de Produto e de Oferta, persistência,
validações básicas e testes dos principais comportamentos.

Fora do escopo desta etapa: pedidos, carrinho, pagamentos, entrega,
notificações, funcionalidades de Operação, frontend e autenticação.

O plano completo da fase está em [`docs/p1.md`](docs/p1.md) e o estado atual do
código em [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md).

## Domínio de Catálogo

```text
   Produto ──1:N──▶ Oferta ◀──N:1── Vendedor
```

- **Produto** representa o item comercializado e é independente do vendedor.
  Não carrega preço, estoque nem disponibilidade.
- **Vendedor** representa a identidade mínima de quem comercializa.
- **Oferta** conecta um Produto a um Vendedor e concentra preço, estoque e
  disponibilidade. Um mesmo Produto pode ter ofertas de vendedores diferentes,
  independentes entre si.
- A exclusão de Produto ou de Vendedor é física e restritiva: se ainda houver
  Ofertas associadas, o banco recusa a operação (`ON DELETE RESTRICT`). No
  `DELETE` de produto, a API responde `409` com `code: resource_in_use`.

## Requisitos

- Python 3.12 ou superior
- [uv](https://docs.astral.sh/uv/)
- Docker, para o Postgres local

## Como executar

```bash
cp .env.example .env   # preencha as credenciais do Postgres local
make install
make db-up             # sobe o Postgres, espera ficar saudavel e cria o banco de teste
make migrate           # aplica as migrations
make seed              # cria os vendedores locais (sem rotas na v0)
make run
```

A API sobe em `http://localhost:8000` e as rotas ficam sob o prefixo `/v1`.
`make db-down` derruba o banco.

## Persistência

PostgreSQL com SQLAlchemy e migrations via Alembic. O banco local vem do
`docker-compose.yml` e as credenciais saem de variáveis de ambiente — não há
valor de credencial no repositório.

Para criar uma migration depois de alterar os modelos:

```bash
make revision m="create catalog tables"
make migrate
```

## Como executar os testes

Os testes de Catálogo usam o mesmo Postgres do `docker-compose`, no banco
indicado por `TEST_DATABASE_URL`. Preencha essa variável no `.env` e suba o
banco antes de testar.

```bash
make db-up         # sobe o Postgres e cria o banco de teste
make test          # suíte completa
make lint          # ruff (lint e formatação)
```

## Documentação da API

- Documentação interativa gerada pelo FastAPI: `http://localhost:8000/docs`
- Contrato OpenAPI escrito à mão: [`api/openapi.yaml`](api/openapi.yaml)

O contrato em `api/openapi.yaml` é a fonte da verdade e é escrito **antes** da
implementação. O fluxo de qualquer mudança na API é:

1. editar `api/openapi.yaml` e revisar o contrato;
2. implementar as rotas e os schemas em `app/`;
3. rodar `make test` — `tests/integration/test_openapi_contract.py` falha se a
   implementação divergir do contrato.

## Organização do código

| Caminho | Responsabilidade |
| --- | --- |
| `api/openapi.yaml` | contrato da API, fonte da verdade |
| `app/main.py` | montagem da aplicação FastAPI |
| `app/core/` | configuração e tradução de erros de negócio para HTTP |
| `app/database.py` | engine, sessão e base declarativa do SQLAlchemy |
| `app/health.py` | health check |
| `app/catalog/` | rotas, schemas, modelos e seed do Catálogo |
| `migrations/` | migrations do Alembic |
| `tests/` | testes de unidade e de integração |

O código é organizado por domínio: cada domínio novo entra como um módulo
próprio em `app/`, com suas rotas, schemas e regras.

## Configuração

Toda a configuração vem de variáveis de ambiente, descritas em `.env.example`.
O arquivo `.env` nunca é commitado, nem qualquer valor de credencial.

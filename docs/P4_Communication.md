# P4 — Communication

## Objetivo

Implementar uma comunicação simples entre Buyer e Seller, contextualizada por um `Order Item`.

A solução deve permitir que:

- o Buyer inicie uma conversa relacionada a uma compra;
- o Seller visualize a conversa relacionada ao seu `Order Item`;
- Buyer e Seller enviem mensagens;
- ambos consultem o histórico da comunicação.

A Communication deve complementar a jornada operacional criada na P3, sem alterar as regras existentes do domínio de Orders.

O `Order Item` é o contexto de negócio da Conversation.

---

## Escopo

Implementar:

1. Conversation contextualizada por `Order Item`;
2. abertura de Conversation;
3. seleção de motivo;
4. envio de Messages;
5. consulta de Conversations;
6. consulta do histórico de Messages;
7. autorização Buyer/Seller;
8. ciclo de vida `OPEN` / `CLOSED`;
9. encerramento manual pelo Seller;
10. encerramento automático após 5 dias de inatividade;
11. mensagem sistêmica de encerramento;
12. preservação do histórico;
13. ordenação por última interação;
14. eventos relacionados à Communication;
15. testes unitários e de integração.

Não implementar frontend, realtime, notificações externas ou fluxo de Ops nesta fase.

---

# 1. Conceito de Conversation

Uma Conversation representa uma comunicação entre um Buyer e um Seller sobre um único `Order Item`.

```text
Order
 └── Order Item
       └── Conversation
             └── Messages
```

Um `Order Item` pode possuir várias Conversations ao longo do tempo.

Porém:

> Um `Order Item` pode possuir somente uma Conversation `OPEN` simultaneamente.

Quando uma Conversation é fechada, uma nova dúvida deve gerar uma nova Conversation.

A Conversation anterior não é reaberta.

---

# 2. Ciclo de vida

A Conversation possui dois estados:

```text
OPEN
CLOSED
```

### OPEN

Conversation ativa e capaz de receber novas Messages.

### CLOSED

Conversation encerrada.

Uma Conversation `CLOSED`:

- não recebe novas Messages;
- não pode ser reaberta;
- permanece disponível para consulta;
- mantém todo seu histórico;
- não impede a criação de uma nova Conversation para o mesmo `Order Item`.

---

# 3. Criação da Conversation

A Conversation é criada sob demanda.

Buyer ou Seller podem iniciar uma nova Conversation.

A criação acontece a partir de um `Order Item`.

Antes de criar:

1. identificar o usuário pelo JWT;
2. validar que ele possui relação com o `Order Item`;
3. verificar se existe Conversation `OPEN`;
4. se existir, utilizar a Conversation existente;
5. se não existir, criar uma nova Conversation.

A criação de uma Conversation não cria automaticamente uma Message.

A primeira Message é enviada posteriormente pelo participante.

---

# 4. Motivo da Conversation

Ao iniciar uma nova Conversation, o usuário deve selecionar obrigatoriamente um motivo.

Motivos iniciais:

```text
ATRASO
TROCA
DEVOLUÇÃO
RECLAMAÇÃO
SUPORTE
ELOGIO
OUTROS
```

O motivo pertence à Conversation e deve permanecer registrado como parte de seu contexto.

Não implementar classificação automática ou IA para definição do motivo.

---

# 5. Contagem de inatividade

A contagem de inatividade começa **no momento em que a Conversation é criada**, após a seleção do motivo.

Qualquer nova Message enviada pelo Buyer ou Seller reinicia o contador.

```text
Conversation criada
      ↓
contador inicia
      ↓
Message
      ↓
contador reinicia
      ↓
Message
      ↓
contador reinicia
      ↓
5 dias sem Message
      ↓
Conversation CLOSED
```

Considerar 5 dias corridos desde a última Message ou, caso não exista Message, desde a criação da Conversation.

---

# 6. Encerramento manual

Somente o Seller pode encerrar manualmente uma Conversation.

Buyer não possui essa capacidade.

Ao ser encerrada:

```text
OPEN → CLOSED
```

A Conversation não pode voltar para `OPEN`.

Uma nova necessidade de comunicação deve criar uma nova Conversation.

---

# 7. Encerramento automático

Uma Conversation `OPEN` que permanecer 5 dias corridos sem novas Messages deve ser encerrada automaticamente.

O sistema deve:

1. identificar a Conversation elegível;
2. registrar uma Message sistêmica;
3. alterar o estado para `CLOSED`.

Mensagem padrão:

> Esta conversa foi encerrada automaticamente após 5 dias sem novas mensagens. Se precisar de ajuda novamente, inicie uma nova conversa.

A Message sistêmica faz parte do histórico normal da Conversation.

Nesta fase, mensagens sistêmicas serão utilizadas somente para esse encerramento automático.

---

# 8. Messages

Uma Message possui, no mínimo:

- identificador;
- Conversation;
- autor;
- conteúdo;
- data/hora de criação.

Messages podem ser enviadas somente enquanto a Conversation estiver `OPEN`.

O conteúdo é exclusivamente texto.

Limite máximo:

```text
2.000 caracteres
```

Conteúdo vazio ou composto somente por espaços deve ser rejeitado.

---

# 9. Imutabilidade

Depois de criada, uma Message não pode:

- ser editada;
- ser excluída.

O histórico deve permanecer íntegro.

---

# 10. Histórico

Todo o histórico da Conversation deve permanecer armazenado e consultável, inclusive depois do encerramento.

A experiência de consulta deve considerar o histórico por período.

Inicialmente devem ser carregadas as Messages do último dia.

O usuário deve poder carregar progressivamente períodos anteriores.

Conceitualmente:

```text
Hoje
  Message
  Message
  Message

+ Ver mensagens anteriores

Ontem
  Message
  Message

+ Ver mensagens anteriores
```

A implementação deve permitir recuperar todo o histórico sem limite artificial de retenção.

---

# 11. Localização da Conversation

Nesta fase, não criar uma inbox global de Conversations.

A Conversation deve ser encontrada a partir do `Order Item`.

Fluxo do Seller:

```text
Seller
  ↓
Order Items
  ↓
Order Item
  ↓
Conversation
```

Fluxo do Buyer:

```text
Buyer
  ↓
Order
  ↓
Order Item
  ↓
Conversation
```

Quando não existir uma Conversation `OPEN`, o usuário deve possuir uma ação para iniciar uma nova Conversation.

A interface dessa ação será definida posteriormente no frontend.

---

# 12. Histórico de Conversations

Um `Order Item` pode possuir múltiplas Conversations.

Todas permanecem disponíveis para consulta.

A ordenação deve considerar a última interação:

```text
Conversation mais recentemente atualizada
        ↓
Conversation anterior
        ↓
Conversation mais antiga
```

Uma nova Message atualiza a Conversation e faz com que ela passe para o topo.

---

# 13. Autorização

Somente os envolvidos na Conversation podem interagir com ela:

```text
Buyer ↔ Seller
```

### Seller

Pode acessar somente Conversations relacionadas aos seus próprios `Order Items`.

### Buyer

Pode acessar somente Conversations relacionadas aos seus próprios Orders/Order Items.

A identidade do usuário deve ser obtida pelo JWT.

Nunca utilizar `buyer_id` ou `seller_id` enviado pelo cliente como fonte de autorização.

Usuário sem relação com o recurso deve receber:

```text
404 Not Found
```

Não revelar a existência de recursos pertencentes a outros usuários.

---

# 14. Operações de Conversation

Implementar operações equivalentes a:

### Criar Conversation

```http
POST /v1/order-items/{item_id}/conversation
```

Deve:

- validar autorização;
- validar motivo;
- verificar Conversation `OPEN`;
- reutilizar a existente quando aplicável;
- criar nova quando não existir;
- iniciar a contagem de inatividade após a criação.

### Consultar Conversations do Order Item

```http
GET /v1/order-items/{item_id}/conversations
```

Retornar as Conversations relacionadas ao item, ordenadas pela última interação.

### Consultar Conversation

```http
GET /v1/conversations/{conversation_id}
```

Somente participantes autorizados.

### Fechar Conversation

```http
POST /v1/conversations/{conversation_id}/close
```

Somente Seller.

### Enviar Message

```http
POST /v1/conversations/{conversation_id}/messages
```

Somente participantes autorizados e somente para Conversation `OPEN`.

### Consultar Messages

```http
GET /v1/conversations/{conversation_id}/messages
```

Implementar recuperação paginada/progressiva do histórico, permitindo carregar inicialmente o último dia e posteriormente períodos anteriores.

Os nomes finais de schemas/services/repositories devem seguir os padrões já existentes no projeto.

---

# 15. Concorrência

A regra abaixo deve ser garantida pelo backend:

> Nunca podem existir duas Conversations `OPEN` para o mesmo `Order Item`.

A criação deve ser segura contra requests concorrentes.

Não confiar somente na validação feita pela aplicação.

Utilizar a estratégia de persistência/transação já adotada pelo projeto para garantir a unicidade da Conversation `OPEN`.

---

# 16. Fechamento automático

O mecanismo responsável pelo fechamento automático deve ser compatível com a infraestrutura existente do projeto.

Não criar uma arquitetura complexa de scheduling se o projeto já possuir mecanismo adequado.

O processo deve encontrar Conversations:

```text
status = OPEN
AND
última interação/criação >= 5 dias sem Message
```

Para cada Conversation elegível:

1. registrar Message sistêmica;
2. alterar status para `CLOSED`;
3. garantir consistência transacional.

O processo deve ser idempotente: executar novamente não pode gerar múltiplas Messages de encerramento ou alterar uma Conversation já fechada.

---

# 17. Eventos

Reutilizar o mecanismo de eventos existente.

Eventos de Communication:

```text
ConversationCreated
MessageCreated
ConversationClosed
```

Os nomes devem seguir a convenção existente no projeto.

Eventos devem ser publicados somente após commit bem-sucedido.

Não implementar consumidores, notificações ou integrações externas nesta fase.

---

# 18. Erros

Reutilizar a convenção estabelecida em P2/P3.

| Situação | HTTP |
|---|---:|
| Usuário não autenticado | `401 Unauthorized` |
| Conversation/Order Item inexistente ou inacessível | `404 Not Found` |
| Payload inválido | `422 Unprocessable Entity` |
| Operação inválida/conflitante | `409 Conflict` |

Não criar nova convenção de erros.

---

# 19. Ops e prioridade

O desafio menciona que Ops gostaria de identificar perguntas importantes, mas a definição de "importante" ainda não existe.

Portanto:

- não implementar prioridade nesta fase;
- não criar algoritmo de classificação;
- não criar score;
- não criar IA para priorização;
- não criar acesso de Ops às Conversations.

A arquitetura deve permanecer simples e preparada para futura evolução.

---

# 20. Fora do escopo

Não implementar nesta fase:

- frontend;
- inbox global;
- WebSocket;
- SSE;
- realtime;
- polling automático;
- push notification;
- e-mail;
- WhatsApp;
- anexos;
- imagens;
- edição de Messages;
- exclusão de Messages;
- IA para classificação;
- prioridade de Conversations;
- Dashboard de Ops;
- acesso de Ops;
- arquivamento;
- novas regras de Orders;
- novas regras de estoque.

---

# 21. Testes

## Conversation

- Buyer consegue iniciar Conversation de seu Order Item;
- Seller consegue iniciar Conversation de seu Order Item;
- motivo é obrigatório;
- motivos válidos são aceitos;
- motivo inválido é rejeitado;
- não é possível criar duas Conversations `OPEN` para o mesmo Order Item;
- nova Conversation pode ser criada depois que a anterior estiver `CLOSED`;
- Conversation `CLOSED` permanece consultável;
- Conversation `CLOSED` não pode ser reaberta;
- somente Seller pode fechar manualmente;
- Buyer não pode fechar manualmente.

## Messages

- Buyer consegue enviar Message;
- Seller consegue enviar Message;
- Message pertence à Conversation correta;
- Conversation `CLOSED` não recebe Message;
- Message vazia é rejeitada;
- Message acima de 2.000 caracteres é rejeitada;
- Message de até 2.000 caracteres é aceita;
- Message não pode ser editada;
- Message não pode ser excluída;
- histórico permanece disponível.

## Inatividade

- contador começa na criação da Conversation;
- envio de Message reinicia o contador;
- Conversation é fechada após 5 dias sem Message;
- mensagem sistêmica é registrada;
- mensagem sistêmica não é duplicada;
- Conversation já fechada não é processada novamente.

## Autorização

- Seller acessa somente seus Order Items;
- Buyer acessa somente seus Orders;
- Seller não acessa Conversation de outro Seller;
- Buyer não acessa Conversation de outro Buyer;
- usuário sem relação recebe `404`;
- IDs enviados pelo cliente não substituem a identidade derivada do JWT.

## Histórico

- Conversations são ordenadas pela última interação;
- nova Message move Conversation para o topo;
- histórico inicial retorna o último dia;
- períodos anteriores podem ser carregados;
- histórico antigo permanece preservado.

## Concorrência

- requests concorrentes não criam duas Conversations `OPEN`;
- fechamento automático e fechamento manual não produzem estado inconsistente;
- fechamento automático não gera mensagens duplicadas.

## Eventos

- `ConversationCreated` ocorre após commit;
- `MessageCreated` ocorre após commit;
- `ConversationClosed` ocorre após commit;
- rollback não publica evento correspondente.

---

# 22. Critérios de aceite

A P4 estará concluída quando:

1. Buyer e Seller puderem iniciar Conversations a partir de seus `Order Items`;
2. uma Conversation exigir a seleção de um motivo;
3. os sete motivos definidos estiverem disponíveis;
4. apenas uma Conversation `OPEN` existir por `Order Item`;
5. Buyer e Seller puderem enviar Messages em Conversations `OPEN`;
6. Messages forem somente texto e limitadas a 2.000 caracteres;
7. Messages forem imutáveis;
8. histórico puder ser consultado progressivamente;
9. Conversations forem ordenadas pela última interação;
10. Seller puder fechar manualmente uma Conversation;
11. Conversations forem fechadas automaticamente após 5 dias de inatividade;
12. o encerramento automático gerar a Message sistêmica padrão;
13. Conversations `CLOSED` permanecerem disponíveis para consulta;
14. uma Conversation `CLOSED` não puder ser reaberta;
15. uma nova dúvida puder gerar uma nova Conversation;
16. Buyer e Seller permanecerem isolados corretamente;
17. eventos forem publicados somente após commit;
18. concorrência não permitir duas Conversations `OPEN` para o mesmo `Order Item`;
19. nenhuma funcionalidade de Ops, prioridade, realtime, notificações ou frontend seja introduzida.

---

# 23. Princípios de implementação

- API First;
- reutilizar padrões estabelecidos em P2/P3;
- `Order Item` como contexto da comunicação;
- backend como fonte de verdade;
- JWT como fonte de identidade;
- baixo acoplamento;
- simplicidade;
- evitar abstrações prematuras;
- garantir integridade na persistência;
- não duplicar regras de domínio;
- não antecipar funcionalidades de Ops;
- não antecipar frontend;
- não criar mecanismos de realtime sem necessidade;
- manter o domínio preparado para evolução futura.

## Instrução final

Antes de implementar:

1. analisar a estrutura atual do projeto;
2. identificar os padrões utilizados em P2 e P3;
3. reutilizar models, schemas, services, repositories, autenticação, erros, eventos e testes existentes sempre que aplicável;
4. não alterar funcionalidades existentes fora do escopo da P4;
5. implementar a P4 incrementalmente;
6. executar os testes existentes após cada etapa relevante;
7. ao final, executar a suíte completa de testes e reportar eventuais impactos nas fases anteriores.

Não implementar funcionalidades fora deste escopo sem validação prévia.

---

# 24. Contrato da API (decidido para implementacao)

Valores persistidos e expostos na API usam lowercase, no padrao de P2/P3.

- Status: `open`, `closed`.
- Motivos: `atraso`, `troca`, `devolucao`, `reclamacao`, `suporte`, `elogio`, `outros`.
- `author_type`: `buyer`, `seller`, `system`.

## Semantica HTTP

- `POST /v1/order-items/{item_id}/conversation`: `201` se criar (evento `ConversationCreated`); `200` se reutilizar a OPEN (motivo do body ignorado, sem evento).
- `POST /v1/conversations/{conversation_id}/close`: somente Seller; `200` se fechar; ja `closed` responde `409 invalid_transition`. Close manual nao cria Message sistemica.
- `POST .../messages` em Conversation `closed`: `409 invalid_transition`.
- Buyer em `POST .../close`: `403`. Recurso de outro usuario: `404`. Sem token: `401`. Payload invalido: `422`.

## Historico de Messages

Janela rolante de 24h em UTC. Query `before` opcional, timezone-aware e nao futura (senao `422`).

- Sem `before`: `to = now`, `from = now - 24h`; items com `from <= created_at <= to`.
- Com `before`: `to = before` (exclusivo), `from = before - 24h`; items com `from <= created_at < before`.
- Envelope: `items` (ASC), `from`, `to`, `has_older`.

## Inatividade

Cinco dias corridos = 120 horas a partir de `last_interaction_at` (`CONVERSATION_INACTIVITY_HOURS`, padrao 120).

Leitura de Conversation/Messages pode encerrar uma OPEN expirada (write-on-read): Message sistemica + `closed` + eventos, persistidos no commit do request.

Unicidade de OPEN por Order Item e garantida por indice unico parcial no Postgres.
# Segurança

Este projeto é didático, mas segue práticas de segurança reais. Na versão em microsserviços,
as proteções do monólito foram mantidas e adaptadas: o token passou a ser conferido em cada serviço.

## O que está protegido

| Risco | Proteção |
|---|---|
| Acesso sem login | O gateway serve a tela e `/saude` sem token; todas as rotas de dados exigem `Authorization: Bearer ...`. Cada serviço valida o JWT **antes** de responder. |
| Token falsificado | Assinatura HS256 com `JWT_SEGREDO` do `.env`, validade, emissor, algoritmo fixo e claims obrigatórios (`alg: none` é recusado). |
| Serviço desconfiando de outro serviço | O Chamados repassa o token do usuário ao chamar Usuários e Inventário; esses serviços validam o token de novo. |
| Banco de outro serviço | Cada serviço tem o seu banco e não lê/escreve o dos outros. O perfil usado nas permissões vem do token validado; o status `ativo` é conferido no banco do serviço de Usuários. |
| Senhas vazadas do banco | Hash **scrypt** com sal aleatório; a senha nunca é salva nem devolvida pela API. |
| Adivinhar senhas | Bloqueio temporário após 5 tentativas erradas (por e-mail e endereço), com a mesma mensagem para e-mail inexistente e senha errada. |
| Ver ou mexer no que não é seu | Solicitante vê só os próprios chamados e notificações; só técnicos/admin atribuem e resolvem; só admin cria usuários. Chamado alheio responde 404. |
| Agir em nome de outra pessoa | Solicitante e autor do comentário vêm do token. Campos extras são recusados (`extra="forbid"`). |
| XSS na tela | Texto da API escapado antes de entrar no HTML; CSP só permite scripts da própria origem. |
| Clickjacking e outros | `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`. |
| Dados enormes | Limites nos campos e corpo limitado a 64 KB no gateway e nos serviços. |
| SQL injection | Acesso ao banco só pelo SQLAlchemy com parâmetros. |
| Erros que vazam detalhes | Mensagens genéricas para conflitos de banco; falha de serviço vira 503 com texto claro, sem stack trace. |
| Exposição dos serviços | Só o gateway publica porta (em `127.0.0.1`); serviços e bancos ficam na rede interna do Docker. |
| Contêiner | Usuário sem privilégios, raiz somente leitura, `/tmp` em tmpfs, sem capacidades extras, `no-new-privileges`. |
| Segredos no código | `JWT_SEGREDO` e `SENHA_EXEMPLO` vêm do `.env`/ambiente; `.env` está no `.gitignore`. |

## Diferenças em relação ao monólito

- O **perfil** viaja no JWT. Se um admin mudar o perfil de alguém, a pessoa precisa entrar de novo
  para o novo perfil valer nos serviços que validam apenas o token.
- O limite de tentativas de login fica em memória no serviço de Usuários. Com várias réplicas,
  use um armazenamento compartilhado (Redis).
- Falhas de rede são tratadas com timeout (2 s nos serviços, 5 s no gateway) e respondem 503;
  isso é uma nova superfície de falha que não existia quando tudo era chamada de função.

## Antes de usar em produção

- Defina `JWT_SEGREDO` aleatório com pelo menos 32 caracteres e **o mesmo valor em todos os serviços**.
- Rode com `DADOS_EXEMPLO=0` e `DOCS=0`.
- Coloque o gateway atrás de HTTPS com certificado.
- Troque o SQLite por um banco gerenciado com backup, um por serviço.
- Considere uma fila de eventos para notificações e um barramento/observabilidade para as chamadas HTTP.

## Como relatar um problema

Encontrou uma falha? Não abra uma issue pública: envie os detalhes diretamente ao professor.

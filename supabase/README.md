# Supabase - Plataforma GD

## Visão Geral

Este diretório contém as migrações SQL para configurar o banco de dados PostgreSQL no Supabase.

## Estrutura de Arquivos

```
supabase/
├── migrations/
│   ├── 001_initial_schema.sql    # Tabelas e ENUMs (28 tabelas)
│   ├── 002_rls_policies.sql      # Políticas de segurança (RLS)
│   └── 003_seed_data.sql         # Dados iniciais e configurações
└── README.md                     # Este arquivo
```

## Setup

### 1. Criar Projeto no Supabase

1. Acesse [supabase.com](https://supabase.com) e crie uma conta
2. Clique em "New Project"
3. Preencha:
   - **Name**: `plataforma-gd`
   - **Database Password**: (guarde esta senha!)
   - **Region**: `South America (São Paulo)`
4. Aguarde a criação do projeto (~2 minutos)

### 2. Executar Migrações

#### Opção A: Via SQL Editor (Mais Simples)

1. No Supabase Dashboard, vá em **SQL Editor**
2. Clique em **New Query**
3. Cole o conteúdo de cada arquivo de migração NA ORDEM:
   - Primeiro: `001_initial_schema.sql`
   - Segundo: `002_rls_policies.sql`
   - Terceiro: `003_seed_data.sql`
4. Clique em **Run** para cada um

#### Opção B: Via Supabase CLI

```bash
# Instalar CLI
npm install -g supabase

# Login
supabase login

# Linkar projeto
supabase link --project-ref SEU_PROJECT_REF

# Rodar migrações
supabase db push
```

### 3. Configurar Variáveis de Ambiente

No Supabase Dashboard, vá em **Settings > API** e copie:

- **Project URL**: `https://xxx.supabase.co`
- **anon public key**: `eyJhbGc...`
- **service_role key**: `eyJhbGc...` (NÃO expor no frontend!)

Crie um arquivo `.env` na raiz do projeto:

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...

# Frontend (apenas anon key)
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
```

## Tabelas Criadas

### Módulo Core (18 tabelas)

| # | Tabela | Descrição |
|---|--------|-----------|
| 1 | `usuarios` | Usuários da plataforma (integrado com Supabase Auth) |
| 2 | `perfis_usuario` | Perfis de cada usuário (multi-perfil) |
| 3 | `tokens_energisa` | Tokens de autenticação da Energisa (24h) |
| 4 | `tokens_plataforma` | Refresh tokens JWT da plataforma |
| 5 | `unidades_consumidoras` | UCs vinculadas aos usuários |
| 6 | `empresas` | Empresas proprietárias de usinas |
| 7 | `usinas` | Usinas de geração distribuída |
| 8 | `gestores_usina` | Relação gestor ↔ usina |
| 9 | `beneficiarios` | Beneficiários que recebem créditos |
| 10 | `convites` | Convites para beneficiários/gestores |
| 11 | `contratos` | Contratos entre partes |
| 12 | `faturas` | Faturas da Energisa (histórico completo) |
| 13 | `historico_gd` | Histórico de créditos GD |
| 14 | `cobrancas` | Cobranças para beneficiários |
| 15 | `saques` | Solicitações de saque |
| 16 | `notificacoes` | Notificações do sistema |
| 17 | `config_plataforma` | Configurações globais |
| 18 | `leads` | Leads da landing page |

### Módulo Marketplace (10 tabelas)

| # | Tabela | Descrição |
|---|--------|-----------|
| 19 | `parceiros` | Parceiros/Integradores |
| 20 | `equipe_parceiro` | Membros da equipe do parceiro |
| 21 | `produtos_marketplace` | Produtos anunciados |
| 22 | `kanban_pipelines` | Pipelines customizáveis |
| 23 | `kanban_colunas` | Colunas/etapas do pipeline |
| 24 | `formularios_dinamicos` | Formulários customizáveis |
| 25 | `projetos` | Projetos solares em andamento |
| 26 | `projeto_historico` | Histórico de movimentações |
| 27 | `projeto_tarefas` | Tarefas do projeto |
| 28 | `transacoes_marketplace` | Transações financeiras |

## ENUMs Criados

| ENUM | Valores |
|------|---------|
| `perfil_tipo` | superadmin, proprietario, gestor, beneficiario, usuario, parceiro |
| `convite_tipo` | BENEFICIARIO, GESTOR |
| `convite_status` | PENDENTE, ACEITO, EXPIRADO, CANCELADO |
| `contrato_tipo` | GESTOR_PROPRIETARIO, GESTOR_BENEFICIARIO, PROPRIETARIO_BENEFICIARIO |
| `contrato_status` | RASCUNHO, AGUARDANDO_ASSINATURA, ATIVO, EXPIRADO, CANCELADO |
| `cobranca_status` | PENDENTE, PAGA, VENCIDA, CANCELADA |
| `saque_status` | PENDENTE, APROVADO, REJEITADO, PAGO |
| `notificacao_tipo` | FATURA, CONTRATO, SAQUE, CONVITE, COBRANCA, GD, SISTEMA |
| `lead_status` | NOVO, CONTATADO, QUALIFICADO, CONVERTIDO, PERDIDO |
| `parceiro_status` | PENDENTE, ATIVO, SUSPENSO, INATIVO |
| `membro_papel` | ADMIN, VENDEDOR, TECNICO, FINANCEIRO, VISUALIZADOR |
| `produto_tipo` | PROJETO_SOLAR, ENERGIA_COMPARTILHADA, KIT_EQUIPAMENTOS, SERVICO |
| `produto_status` | RASCUNHO, PENDENTE, ATIVO, PAUSADO, REPROVADO, VENDIDO |
| `projeto_status` | LEAD, QUALIFICADO, ORCAMENTO, ... , CONCLUIDO, PERDIDO, CANCELADO |
| `tarefa_status` | PENDENTE, EM_ANDAMENTO, CONCLUIDA, CANCELADA |
| `tarefa_prioridade` | BAIXA, MEDIA, ALTA, URGENTE |
| `transacao_tipo` | VENDA, COMISSAO, REPASSE, ESTORNO |
| `transacao_status` | PENDENTE, PROCESSANDO, CONCLUIDA, FALHOU, ESTORNADA |

## Row Level Security (RLS)

Todas as tabelas têm RLS habilitado. As políticas principais:

- **Usuários**: Veem apenas seus próprios dados (exceto superadmin)
- **UCs**: Usuário vê suas UCs, gestor vê UCs das usinas que gerencia
- **Beneficiários**: Gestor vê/edita beneficiários das suas usinas
- **Faturas**: Acesso baseado na propriedade da UC
- **Marketplace**: Membros do parceiro acessam dados do parceiro

### Funções Auxiliares

```sql
-- Verificar se é superadmin
SELECT is_superadmin();

-- Obter ID do usuário atual
SELECT get_usuario_id();

-- Verificar se tem perfil específico
SELECT has_perfil('gestor');

-- Verificar se é membro de um parceiro
SELECT is_membro_parceiro(1);
```

## Formato de Exibição de UC

**SEMPRE** mostrar UC no formato: `cod_empresa/cdc-digito_verificador`

Exemplos:
- `6/4242904-3`
- `6/4160693-0`

```sql
-- Formatar UC
SELECT formatar_uc(6, 4242904, 3);  -- Retorna: '6/4242904-3'

-- Buscar UC pelo formato
SELECT * FROM buscar_uc_por_formato('6/4242904-3');
```

## Triggers Automáticos

Todas as tabelas com `atualizado_em` têm trigger que atualiza automaticamente ao fazer UPDATE.

## Próximos Passos

1. [ ] Configurar Supabase Auth (email/senha ou social login)
2. [ ] Criar usuário admin inicial via Supabase Dashboard
3. [ ] Testar conexão do backend com as variáveis de ambiente
4. [ ] Implementar sincronização com API Energisa

## Comandos Úteis

```sql
-- Ver todas as tabelas
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Ver políticas RLS
SELECT * FROM pg_policies WHERE schemaname = 'public';

-- Ver configurações
SELECT * FROM config_plataforma;

-- Contar registros em todas as tabelas
SELECT schemaname, relname, n_live_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
```

## Suporte

Em caso de dúvidas ou problemas:
- Documentação Supabase: https://supabase.com/docs
- Issues do projeto: [GitHub Issues]

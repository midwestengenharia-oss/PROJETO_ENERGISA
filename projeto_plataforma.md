# Projeto Plataforma GD - Acompanhamento

## Visão Geral
Sistema de gestão de Geração Distribuída de energia solar, integrando Gateway Energisa + Gestor de UCs/Usinas/Beneficiários.

**URL Supabase**: `https://supabase.midwestengenharia.com.br`

---

## Progresso de Implementação

### Banco de Dados (Supabase)
- [x] Schema inicial (28 tabelas) - `001_initial_schema.sql`
- [x] Políticas RLS - `002_rls_policies.sql`
- [x] Seed data - `003_seed_data.sql`
- [x] Migração executada no Supabase

### Backend Unificado

#### Fase 1: Infraestrutura Base ✅
- [x] Estrutura de pastas `backend/`
- [x] `config.py` - Configurações e variáveis de ambiente
- [x] `core/database.py` - Conexão com Supabase
- [x] `core/security.py` - Autenticação JWT/Supabase
- [x] `core/exceptions.py` - Exceções customizadas
- [x] `dependencies.py` - Dependências globais
- [x] `main.py` - Aplicação FastAPI principal
- [x] `requirements.txt` - Dependências Python
- [x] `.env.example` - Template de configuração
- [x] `__init__.py` para todos os módulos

#### Fase 2: Autenticação ✅
- [x] `auth/schemas.py` - Schemas Pydantic
- [x] `auth/service.py` - Lógica de autenticação
- [x] `auth/router.py` - Endpoints de auth
- [x] Integrado ao main.py

#### Fase 3: Gateway Energisa ✅
- [x] `energisa/service.py` - Lógica de scraping
- [x] `energisa/session_manager.py` - Gerenciamento de sessões
- [x] `energisa/aneel_api.py` - API ANEEL
- [x] `energisa/calculadora.py` - Cálculos de economia
- [x] `energisa/constants.py` - Constantes
- [x] `energisa/router.py` - Endpoints
- [x] Integrado ao main.py

#### Fase 4: Módulos Core ✅
- [x] `usuarios/` - CRUD + perfis (schemas, service, router)
- [x] `ucs/` - Unidades Consumidoras (schemas, service, router)
- [x] `usinas/` - GD e rateio (schemas, service, router)
- [x] `beneficiarios/` - CRUD + convites (schemas, service, router)
- [x] `faturas/` - Histórico + sync (schemas, service, router)

#### Fase 5: Módulos Financeiros ✅
- [x] `cobrancas/` - Geração e pagamento (schemas, service, router)
- [x] `contratos/` - Geração e assinatura digital (schemas, service, router)
- [x] `saques/` - Solicitação e aprovação (schemas, service, router)

#### Fase 6: Admin e Extras ✅
- [x] `admin/` - Dashboard, configurações, logs, relatórios
- [x] `leads/` - CRM para landing page
- [x] `notificacoes/` - Sistema de notificações multi-canal

#### Fase 7: Marketplace (futuro)
- [ ] `marketplace/parceiros/`
- [ ] `marketplace/produtos/`
- [ ] `marketplace/projetos/`
- [ ] `marketplace/kanban/`

---

## Estrutura de Arquivos Criados

```
backend/
├── __init__.py
├── main.py                  ✅
├── config.py                ✅
├── dependencies.py          ✅
├── requirements.txt         ✅
├── .env.example             ✅
│
├── core/
│   ├── __init__.py          ✅
│   ├── database.py          ✅
│   ├── security.py          ✅
│   └── exceptions.py        ✅
│
├── auth/
│   ├── __init__.py          ✅
│   ├── schemas.py           ✅
│   ├── service.py           ✅
│   └── router.py            ✅
│
├── energisa/
│   ├── __init__.py          ✅
│   ├── constants.py         ✅
│   ├── session_manager.py   ✅
│   ├── aneel_api.py         ✅
│   ├── calculadora.py       ✅
│   ├── service.py           ✅
│   └── router.py            ✅
│
├── usuarios/
│   ├── __init__.py          ✅
│   ├── schemas.py           ✅
│   ├── service.py           ✅
│   └── router.py            ✅
│
├── ucs/
│   ├── __init__.py          ✅
│   ├── schemas.py           ✅
│   ├── service.py           ✅
│   └── router.py            ✅
│
├── usinas/
│   ├── __init__.py          ✅
│   ├── schemas.py           ✅
│   ├── service.py           ✅
│   └── router.py            ✅
│
├── beneficiarios/
│   ├── __init__.py          ✅
│   ├── schemas.py           ✅
│   ├── service.py           ✅
│   └── router.py            ✅
│
├── faturas/
│   ├── __init__.py          ✅
│   ├── schemas.py           ✅
│   ├── service.py           ✅
│   └── router.py            ✅
│
├── cobrancas/
│   ├── __init__.py          ✅
│   ├── schemas.py           ✅
│   ├── service.py           ✅
│   └── router.py            ✅
│
├── contratos/
│   ├── __init__.py          ✅
│   ├── schemas.py           ✅
│   ├── service.py           ✅
│   └── router.py            ✅
│
├── saques/
│   ├── __init__.py          ✅
│   ├── schemas.py           ✅
│   ├── service.py           ✅
│   └── router.py            ✅
│
├── leads/
│   ├── __init__.py          ✅
│   ├── schemas.py           ✅
│   ├── service.py           ✅
│   └── router.py            ✅
│
├── notificacoes/
│   ├── __init__.py          ✅
│   ├── schemas.py           ✅
│   ├── service.py           ✅
│   └── router.py            ✅
│
├── admin/
│   ├── __init__.py          ✅
│   ├── schemas.py           ✅
│   ├── service.py           ✅
│   └── router.py            ✅
│
├── tests/
│   ├── __init__.py          ✅
│   ├── conftest.py          ✅
│   ├── test_health.py       ✅
│   ├── test_auth.py         ✅
│   ├── test_ucs.py          ✅
│   ├── test_usinas.py       ✅
│   ├── test_beneficiarios.py ✅
│   ├── test_faturas.py      ✅
│   ├── test_cobrancas.py    ✅
│   ├── test_contratos.py    ✅
│   ├── test_saques.py       ✅
│   ├── test_leads.py        ✅
│   ├── test_notificacoes.py ✅
│   └── test_admin.py        ✅
│
└── marketplace/
    └── __init__.py          ⏳ (Fase 7)
```

---

## Endpoints Implementados

### Auth (`/api/auth`) ✅
| Método | Rota | Status |
|--------|------|--------|
| POST | `/signup` | ✅ |
| POST | `/signin` | ✅ |
| POST | `/refresh` | ✅ |
| POST | `/logout` | ✅ |
| GET | `/me` | ✅ |
| PUT | `/me` | ✅ |
| POST | `/me/senha` | ✅ |
| GET | `/perfis` | ✅ |

### Energisa (`/api/energisa`) ✅
| Método | Rota | Status |
|--------|------|--------|
| POST | `/simulacao/iniciar` | ✅ |
| POST | `/simulacao/enviar-sms` | ✅ |
| POST | `/simulacao/validar-sms` | ✅ |
| GET | `/simulacao/ucs/{session_id}` | ✅ |
| GET | `/simulacao/faturas/{session_id}/{codigo_uc}` | ✅ |
| POST | `/login/start` | ✅ |
| POST | `/login/select-option` | ✅ |
| POST | `/login/finish` | ✅ |
| POST | `/ucs` | ✅ |
| POST | `/ucs/info` | ✅ |
| POST | `/faturas/listar` | ✅ |
| POST | `/faturas/pdf` | ✅ |
| POST | `/gd/info` | ✅ |
| POST | `/gd/details` | ✅ |
| POST | `/gd/alterar-beneficiaria` | ✅ |

### Usuarios (`/api/usuarios`) ✅
| Método | Rota | Status |
|--------|------|--------|
| GET | `/` | ✅ |
| POST | `/` | ✅ |
| GET | `/perfil/{perfil}` | ✅ |
| GET | `/{usuario_id}` | ✅ |
| PUT | `/{usuario_id}` | ✅ |
| POST | `/{usuario_id}/desativar` | ✅ |
| POST | `/{usuario_id}/ativar` | ✅ |
| GET | `/{usuario_id}/perfis` | ✅ |
| POST | `/{usuario_id}/perfis` | ✅ |
| DELETE | `/{usuario_id}/perfis/{perfil}` | ✅ |

### UCs (`/api/ucs`) ✅
| Método | Rota | Status |
|--------|------|--------|
| GET | `/` | ✅ |
| GET | `/minhas` | ✅ |
| GET | `/geradoras` | ✅ |
| POST | `/vincular` | ✅ |
| POST | `/vincular-formato` | ✅ |
| GET | `/{uc_id}` | ✅ |
| PUT | `/{uc_id}` | ✅ |
| POST | `/{uc_id}/gd` | ✅ |
| GET | `/{uc_id}/gd` | ✅ |
| GET | `/{uc_id}/beneficiarias` | ✅ |
| DELETE | `/{uc_id}` | ✅ |

### Usinas (`/api/usinas`) ✅
| Método | Rota | Status |
|--------|------|--------|
| GET | `/` | ✅ |
| GET | `/minhas` | ✅ |
| POST | `/` | ✅ |
| GET | `/{usina_id}` | ✅ |
| PUT | `/{usina_id}` | ✅ |
| GET | `/{usina_id}/gestores` | ✅ |
| POST | `/{usina_id}/gestores` | ✅ |
| DELETE | `/{usina_id}/gestores/{gestor_id}` | ✅ |
| GET | `/{usina_id}/beneficiarios` | ✅ |

### Beneficiários (`/api/beneficiarios`) ✅
| Método | Rota | Status |
|--------|------|--------|
| GET | `/` | ✅ |
| POST | `/` | ✅ |
| GET | `/meus` | ✅ |
| GET | `/usina/{usina_id}` | ✅ |
| GET | `/{beneficiario_id}` | ✅ |
| PUT | `/{beneficiario_id}` | ✅ |
| POST | `/{beneficiario_id}/convite` | ✅ |
| POST | `/{beneficiario_id}/ativar` | ✅ |
| POST | `/{beneficiario_id}/suspender` | ✅ |
| POST | `/{beneficiario_id}/cancelar` | ✅ |

### Faturas (`/api/faturas`) ✅
| Método | Rota | Status |
|--------|------|--------|
| GET | `/` | ✅ |
| GET | `/uc/{uc_id}` | ✅ |
| GET | `/uc/{uc_id}/estatisticas` | ✅ |
| GET | `/uc/{uc_id}/comparativo` | ✅ |
| GET | `/uc/{uc_id}/gd` | ✅ |
| GET | `/uc/{uc_id}/{ano}/{mes}` | ✅ |
| GET | `/{fatura_id}` | ✅ |
| POST | `/manual` | ✅ |

---

## Endpoints Implementados (Fase 5 e 6)

### Cobranças (`/api/cobrancas`) ✅
| Método | Rota | Status |
|--------|------|--------|
| GET | `/` | ✅ |
| GET | `/minhas` | ✅ |
| GET | `/estatisticas` | ✅ |
| GET | `/usina/{usina_id}` | ✅ |
| GET | `/beneficiario/{beneficiario_id}` | ✅ |
| GET | `/{cobranca_id}` | ✅ |
| POST | `/` | ✅ |
| POST | `/lote` | ✅ |
| PUT | `/{cobranca_id}` | ✅ |
| POST | `/{cobranca_id}/pagamento` | ✅ |
| POST | `/{cobranca_id}/cancelar` | ✅ |

### Contratos (`/api/contratos`) ✅
| Método | Rota | Status |
|--------|------|--------|
| GET | `/` | ✅ |
| GET | `/meus` | ✅ |
| GET | `/estatisticas` | ✅ |
| GET | `/usina/{usina_id}` | ✅ |
| GET | `/{contrato_id}` | ✅ |
| POST | `/` | ✅ |
| PUT | `/{contrato_id}` | ✅ |
| POST | `/{contrato_id}/enviar-assinatura` | ✅ |
| POST | `/{contrato_id}/assinar` | ✅ |
| POST | `/{contrato_id}/rescindir` | ✅ |
| POST | `/{contrato_id}/suspender` | ✅ |
| POST | `/{contrato_id}/reativar` | ✅ |

### Saques (`/api/saques`) ✅
| Método | Rota | Status |
|--------|------|--------|
| GET | `/` | ✅ |
| GET | `/meus` | ✅ |
| GET | `/saldo` | ✅ |
| GET | `/comissoes` | ✅ |
| GET | `/estatisticas` | ✅ |
| GET | `/pendentes` | ✅ |
| GET | `/{saque_id}` | ✅ |
| POST | `/` | ✅ |
| POST | `/{saque_id}/aprovar` | ✅ |
| POST | `/{saque_id}/rejeitar` | ✅ |
| POST | `/{saque_id}/pagar` | ✅ |
| POST | `/{saque_id}/cancelar` | ✅ |

### Leads (`/api/leads`) ✅
| Método | Rota | Status |
|--------|------|--------|
| POST | `/captura` | ✅ (público) |
| POST | `/simular` | ✅ (público) |
| GET | `/` | ✅ |
| GET | `/estatisticas` | ✅ |
| GET | `/funil` | ✅ |
| GET | `/{lead_id}` | ✅ |
| PUT | `/{lead_id}` | ✅ |
| POST | `/{lead_id}/contato` | ✅ |
| POST | `/{lead_id}/atribuir` | ✅ |
| POST | `/{lead_id}/converter` | ✅ |
| POST | `/{lead_id}/perder` | ✅ |

### Notificações (`/api/notificacoes`) ✅
| Método | Rota | Status |
|--------|------|--------|
| GET | `/` | ✅ |
| GET | `/contador` | ✅ |
| GET | `/preferencias` | ✅ |
| PUT | `/preferencias` | ✅ |
| GET | `/estatisticas` | ✅ |
| GET | `/{notificacao_id}` | ✅ |
| POST | `/` | ✅ |
| POST | `/lote` | ✅ |
| POST | `/{notificacao_id}/lida` | ✅ |
| POST | `/marcar-todas-lidas` | ✅ |
| DELETE | `/{notificacao_id}` | ✅ |

### Admin (`/api/admin`) ✅
| Método | Rota | Status |
|--------|------|--------|
| GET | `/dashboard/stats` | ✅ |
| POST | `/dashboard/grafico` | ✅ |
| GET | `/configuracoes` | ✅ |
| PUT | `/configuracoes/{chave}` | ✅ |
| GET | `/logs` | ✅ |
| POST | `/relatorios` | ✅ |
| GET | `/integracoes` | ✅ |
| GET | `/health-detailed` | ✅ |

---

## Próximos Passos

1. **Testes e Validação**
   - Executar `pytest tests/ -v`
   - Verificar todos os endpoints no Swagger `/docs`
   - Validar integrações com Supabase

2. **Deploy**
   - Configurar .env de produção
   - Deploy no servidor
   - Configurar nginx/traefik

3. **Fase 7: Marketplace (futuro)**
   - `marketplace/parceiros/` - Cadastro de integradores
   - `marketplace/produtos/` - Catálogo de equipamentos
   - `marketplace/projetos/` - Gestão de projetos
   - `marketplace/kanban/` - Board de acompanhamento

---

## Notas

- **Gateway Energisa**: Coração do sistema - scraping + integração com portal Energisa
- **Auth Híbrido**: Supabase Auth para login + tabela `usuarios` para dados extras
- **6 Perfis**: superadmin, proprietario, gestor, beneficiario, usuario, parceiro
- **RLS**: Políticas de segurança configuradas no Supabase

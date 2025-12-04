-- ============================================================================
-- PLATAFORMA GD - MIGRAÇÃO INICIAL SUPABASE
-- ============================================================================
-- Este arquivo cria todas as 28 tabelas do banco de dados PostgreSQL
-- Executar no Supabase SQL Editor ou via CLI
-- ============================================================================

-- ============================================================================
-- PARTE 1: ENUM TYPES
-- ============================================================================

-- Tipos de perfil do usuário
CREATE TYPE perfil_tipo AS ENUM (
    'superadmin',    -- Administrador da plataforma
    'proprietario',  -- Dono de usina geradora (GD)
    'gestor',        -- Gerencia usinas de terceiros (GD)
    'beneficiario',  -- Recebe créditos de energia (GD)
    'usuario',       -- Usuário comum (apenas visualiza suas UCs)
    'parceiro'       -- Integrador/empresa que vende projetos solares (Marketplace)
);

-- Tipos de convite
CREATE TYPE convite_tipo AS ENUM ('BENEFICIARIO', 'GESTOR');
CREATE TYPE convite_status AS ENUM ('PENDENTE', 'ACEITO', 'EXPIRADO', 'CANCELADO');

-- Tipos de contrato
CREATE TYPE contrato_tipo AS ENUM ('GESTOR_PROPRIETARIO', 'GESTOR_BENEFICIARIO', 'PROPRIETARIO_BENEFICIARIO');
CREATE TYPE contrato_status AS ENUM ('RASCUNHO', 'AGUARDANDO_ASSINATURA', 'ATIVO', 'EXPIRADO', 'CANCELADO');

-- Status de cobrança
CREATE TYPE cobranca_status AS ENUM ('PENDENTE', 'PAGA', 'VENCIDA', 'CANCELADA');

-- Status de saque
CREATE TYPE saque_status AS ENUM ('PENDENTE', 'APROVADO', 'REJEITADO', 'PAGO');

-- Tipos de notificação
CREATE TYPE notificacao_tipo AS ENUM ('FATURA', 'CONTRATO', 'SAQUE', 'CONVITE', 'COBRANCA', 'GD', 'SISTEMA');

-- Status de lead
CREATE TYPE lead_status AS ENUM ('NOVO', 'CONTATADO', 'QUALIFICADO', 'CONVERTIDO', 'PERDIDO');

-- Status de parceiro (Marketplace)
CREATE TYPE parceiro_status AS ENUM ('PENDENTE', 'ATIVO', 'SUSPENSO', 'INATIVO');

-- Papéis na equipe do parceiro
CREATE TYPE membro_papel AS ENUM ('ADMIN', 'VENDEDOR', 'TECNICO', 'FINANCEIRO', 'VISUALIZADOR');

-- Tipos de produto no marketplace
CREATE TYPE produto_tipo AS ENUM ('PROJETO_SOLAR', 'ENERGIA_COMPARTILHADA', 'KIT_EQUIPAMENTOS', 'SERVICO');
CREATE TYPE produto_status AS ENUM ('RASCUNHO', 'PENDENTE', 'ATIVO', 'PAUSADO', 'REPROVADO', 'VENDIDO');

-- Status de projeto solar
CREATE TYPE projeto_status AS ENUM (
    'LEAD', 'QUALIFICADO', 'ORCAMENTO', 'PROPOSTA', 'NEGOCIACAO',
    'VENDA', 'DOCUMENTACAO', 'INSTALACAO', 'HOMOLOGACAO', 'CONCLUIDO',
    'PERDIDO', 'CANCELADO'
);

-- Status e prioridade de tarefas
CREATE TYPE tarefa_status AS ENUM ('PENDENTE', 'EM_ANDAMENTO', 'CONCLUIDA', 'CANCELADA');
CREATE TYPE tarefa_prioridade AS ENUM ('BAIXA', 'MEDIA', 'ALTA', 'URGENTE');

-- Transações do marketplace
CREATE TYPE transacao_tipo AS ENUM ('VENDA', 'COMISSAO', 'REPASSE', 'ESTORNO');
CREATE TYPE transacao_status AS ENUM ('PENDENTE', 'PROCESSANDO', 'CONCLUIDA', 'FALHOU', 'ESTORNADA');

-- ============================================================================
-- PARTE 2: TABELAS DO MÓDULO CORE (18 tabelas)
-- ============================================================================

-- 1. USUARIOS
-- Tabela principal de usuários (integrada com Supabase Auth)
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Dados pessoais
    nome_completo VARCHAR(200) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    telefone VARCHAR(20),

    -- Avatar e preferências
    avatar_url VARCHAR(500),
    preferencias JSONB DEFAULT '{}',

    -- Controle de acesso
    is_superadmin BOOLEAN DEFAULT FALSE,
    ativo BOOLEAN DEFAULT TRUE,
    email_verificado BOOLEAN DEFAULT FALSE,

    -- Timestamps
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),
    ultimo_acesso TIMESTAMPTZ
);

CREATE INDEX idx_usuarios_cpf ON usuarios(cpf);
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_auth_id ON usuarios(auth_id);

-- 2. PERFIS_USUARIO
-- Perfis disponíveis para cada usuário (um usuário pode ter múltiplos perfis)
CREATE TABLE perfis_usuario (
    id SERIAL PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    perfil perfil_tipo NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    dados_perfil JSONB DEFAULT '{}',

    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(usuario_id, perfil)
);

CREATE INDEX idx_perfis_usuario_id ON perfis_usuario(usuario_id);

-- 3. TOKENS_ENERGISA
-- Tokens de autenticação da Energisa (expira em 24h)
CREATE TABLE tokens_energisa (
    id SERIAL PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,

    -- Tokens principais
    utk TEXT,                    -- User Token
    rtk TEXT,                    -- Request Token
    udk TEXT,                    -- User Data Key
    refresh_token TEXT,          -- Para renovação

    -- Cookies de sessão (todos os cookies como JSON)
    cookies JSONB,

    -- Controle de expiração
    expira_em TIMESTAMPTZ,       -- 24h após criação
    ultimo_uso TIMESTAMPTZ,
    renovacoes INTEGER DEFAULT 0,

    -- Status
    ativo BOOLEAN DEFAULT TRUE,
    erro_ultimo TEXT,
    requer_reautenticacao BOOLEAN DEFAULT FALSE,

    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(usuario_id)
);

CREATE INDEX idx_tokens_energisa_usuario ON tokens_energisa(usuario_id);
CREATE INDEX idx_tokens_energisa_expira ON tokens_energisa(expira_em);

-- 4. TOKENS_PLATAFORMA
-- Refresh tokens JWT da plataforma
CREATE TABLE tokens_plataforma (
    id SERIAL PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,

    refresh_token TEXT NOT NULL UNIQUE,
    device_info VARCHAR(500),    -- User-Agent, IP, etc

    expira_em TIMESTAMPTZ NOT NULL,
    ultimo_uso TIMESTAMPTZ,
    revogado BOOLEAN DEFAULT FALSE,
    revogado_em TIMESTAMPTZ,

    criado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tokens_plataforma_usuario ON tokens_plataforma(usuario_id);
CREATE INDEX idx_tokens_plataforma_token ON tokens_plataforma(refresh_token);

-- 5. UNIDADES_CONSUMIDORAS
-- UCs - baseado nos responses reais da API Energisa
CREATE TABLE unidades_consumidoras (
    id SERIAL PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id),

    -- Identificação da UC (formato exibição: cod_empresa/cdc-digito_verificador)
    cod_empresa INTEGER NOT NULL DEFAULT 6,    -- codigoEmpresaWeb (6 = Energisa MT)
    cdc INTEGER NOT NULL,                       -- numeroUc (CDC)
    digito_verificador INTEGER NOT NULL,        -- digitoVerificador

    -- Dados do titular
    cpf_cnpj_titular VARCHAR(20),               -- CPF/CNPJ do titular real da UC
    nome_titular VARCHAR(200),                   -- Nome do titular
    usuario_titular BOOLEAN NOT NULL,            -- true = dono, false = gestor

    -- Endereço
    endereco VARCHAR(300),
    numero_imovel VARCHAR(20),
    complemento VARCHAR(200),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    uf VARCHAR(2),
    cep VARCHAR(10),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),

    -- Dados técnicos
    tipo_ligacao VARCHAR(20),                   -- MONOFASICO, BIFASICO, TRIFASICO
    classe_leitura VARCHAR(50),                 -- RESIDENCIAL, COMERCIAL, etc
    grupo_leitura VARCHAR(10),                  -- A, B
    numero_medidor VARCHAR(50),

    -- Status
    uc_ativa BOOLEAN DEFAULT TRUE,
    uc_cortada BOOLEAN DEFAULT FALSE,
    contrato_ativo BOOLEAN DEFAULT TRUE,
    baixa_renda BOOLEAN DEFAULT FALSE,

    -- GD (Geração Distribuída)
    is_geradora BOOLEAN DEFAULT FALSE,
    geradora_id INTEGER REFERENCES unidades_consumidoras(id),
    percentual_rateio DECIMAL(5, 2),
    saldo_acumulado INTEGER DEFAULT 0,

    -- Snapshot completo da API
    dados_api JSONB,
    ultima_sincronizacao TIMESTAMPTZ,

    -- Timestamps
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(cod_empresa, cdc, digito_verificador)
);

CREATE INDEX idx_uc_usuario ON unidades_consumidoras(usuario_id);
CREATE INDEX idx_uc_formato ON unidades_consumidoras(cod_empresa, cdc, digito_verificador);
CREATE INDEX idx_uc_geradora ON unidades_consumidoras(geradora_id);
CREATE INDEX idx_uc_is_geradora ON unidades_consumidoras(is_geradora);

-- 6. EMPRESAS
-- Empresas (proprietárias de usinas)
CREATE TABLE empresas (
    id SERIAL PRIMARY KEY,
    proprietario_id UUID NOT NULL REFERENCES usuarios(id),

    cnpj VARCHAR(18) UNIQUE,
    razao_social VARCHAR(200),
    nome_fantasia VARCHAR(200),
    inscricao_estadual VARCHAR(20),

    -- Endereço
    endereco VARCHAR(300),
    cidade VARCHAR(100),
    uf VARCHAR(2),
    cep VARCHAR(10),

    -- Contato
    telefone VARCHAR(20),
    email VARCHAR(100),

    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_empresas_proprietario ON empresas(proprietario_id);
CREATE INDEX idx_empresas_cnpj ON empresas(cnpj);

-- 7. USINAS
-- Usinas de geração distribuída
CREATE TABLE usinas (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    uc_geradora_id INTEGER NOT NULL REFERENCES unidades_consumidoras(id),

    nome VARCHAR(200),
    capacidade_kwp DECIMAL(10, 2),              -- Capacidade em kWp
    tipo_geracao VARCHAR(50) DEFAULT 'SOLAR',   -- SOLAR, EOLICA, etc
    data_conexao DATE,

    -- Configurações
    desconto_padrao DECIMAL(5, 4) DEFAULT 0.30, -- 30% desconto padrão

    -- Status
    status VARCHAR(20) DEFAULT 'ATIVA',         -- ATIVA, INATIVA, PENDENTE

    -- Localização
    endereco VARCHAR(300),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),

    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_usinas_empresa ON usinas(empresa_id);
CREATE INDEX idx_usinas_uc_geradora ON usinas(uc_geradora_id);

-- 8. GESTORES_USINA
-- Relacionamento gestor <-> usina
CREATE TABLE gestores_usina (
    id SERIAL PRIMARY KEY,
    usina_id INTEGER NOT NULL REFERENCES usinas(id) ON DELETE CASCADE,
    gestor_id UUID NOT NULL REFERENCES usuarios(id),

    ativo BOOLEAN DEFAULT TRUE,
    comissao_percentual DECIMAL(5, 4) DEFAULT 0,
    contrato_id INTEGER,  -- FK será adicionada depois

    criado_em TIMESTAMPTZ DEFAULT NOW(),
    desativado_em TIMESTAMPTZ,

    UNIQUE(usina_id, gestor_id)
);

CREATE INDEX idx_gestores_usina_usina ON gestores_usina(usina_id);
CREATE INDEX idx_gestores_usina_gestor ON gestores_usina(gestor_id);

-- 9. BENEFICIARIOS
-- Beneficiários de geração distribuída
CREATE TABLE beneficiarios (
    id SERIAL PRIMARY KEY,
    usuario_id UUID REFERENCES usuarios(id),     -- NULL até criar conta
    uc_id INTEGER NOT NULL REFERENCES unidades_consumidoras(id),
    usina_id INTEGER NOT NULL REFERENCES usinas(id),
    contrato_id INTEGER,  -- FK será adicionada depois

    -- Dados cadastrais (preenchidos antes de criar conta)
    cpf VARCHAR(14) NOT NULL,
    nome VARCHAR(200),
    email VARCHAR(100),
    telefone VARCHAR(20),

    -- Configurações do benefício
    percentual_rateio DECIMAL(5, 2) NOT NULL,   -- % do rateio
    desconto DECIMAL(5, 4) NOT NULL,            -- % desconto oferecido

    -- Status
    status VARCHAR(20) DEFAULT 'PENDENTE',      -- PENDENTE, ATIVO, SUSPENSO, CANCELADO
    convite_enviado_em TIMESTAMPTZ,
    ativado_em TIMESTAMPTZ,

    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(uc_id, usina_id)
);

CREATE INDEX idx_beneficiarios_usuario ON beneficiarios(usuario_id);
CREATE INDEX idx_beneficiarios_uc ON beneficiarios(uc_id);
CREATE INDEX idx_beneficiarios_usina ON beneficiarios(usina_id);
CREATE INDEX idx_beneficiarios_cpf ON beneficiarios(cpf);

-- 10. CONVITES
-- Convites para beneficiários e gestores
CREATE TABLE convites (
    id SERIAL PRIMARY KEY,
    tipo convite_tipo NOT NULL,

    email VARCHAR(100) NOT NULL,
    cpf VARCHAR(14),
    nome VARCHAR(200),

    beneficiario_id INTEGER REFERENCES beneficiarios(id),
    usina_id INTEGER REFERENCES usinas(id),
    convidado_por_id UUID NOT NULL REFERENCES usuarios(id),

    token VARCHAR(100) UNIQUE NOT NULL,
    expira_em TIMESTAMPTZ NOT NULL,

    status convite_status DEFAULT 'PENDENTE',
    aceito_em TIMESTAMPTZ,
    usuario_criado_id UUID REFERENCES usuarios(id),

    criado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_convites_token ON convites(token);
CREATE INDEX idx_convites_email ON convites(email);

-- 11. CONTRATOS
-- Contratos entre partes
CREATE TABLE contratos (
    id SERIAL PRIMARY KEY,
    tipo contrato_tipo NOT NULL,

    parte_a_id UUID NOT NULL REFERENCES usuarios(id),
    parte_b_id UUID NOT NULL REFERENCES usuarios(id),
    usina_id INTEGER REFERENCES usinas(id),
    beneficiario_id INTEGER REFERENCES beneficiarios(id),

    -- Documento
    template_id INTEGER,
    conteudo_html TEXT,
    hash_documento VARCHAR(64),

    -- Assinaturas
    assinado_a_em TIMESTAMPTZ,
    assinado_b_em TIMESTAMPTZ,
    ip_assinatura_a INET,
    ip_assinatura_b INET,

    -- Vigência
    status contrato_status DEFAULT 'RASCUNHO',
    vigencia_inicio DATE,
    vigencia_fim DATE,

    -- Valores do contrato
    percentual_rateio DECIMAL(5, 2),
    desconto DECIMAL(5, 4),
    comissao DECIMAL(5, 4),

    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

-- Adicionar FK nos gestores_usina e beneficiarios
ALTER TABLE gestores_usina ADD CONSTRAINT fk_gestores_contrato
    FOREIGN KEY (contrato_id) REFERENCES contratos(id);
ALTER TABLE beneficiarios ADD CONSTRAINT fk_beneficiarios_contrato
    FOREIGN KEY (contrato_id) REFERENCES contratos(id);

CREATE INDEX idx_contratos_parte_a ON contratos(parte_a_id);
CREATE INDEX idx_contratos_parte_b ON contratos(parte_b_id);
CREATE INDEX idx_contratos_usina ON contratos(usina_id);

-- 12. FATURAS
-- Faturas da Energisa (histórico completo - API só retorna 13 meses)
CREATE TABLE faturas (
    id SERIAL PRIMARY KEY,
    uc_id INTEGER NOT NULL REFERENCES unidades_consumidoras(id),

    -- Identificação (da API)
    numero_fatura BIGINT UNIQUE,                -- numeroFatura
    mes_referencia INTEGER NOT NULL,            -- mesReferencia (1-12)
    ano_referencia INTEGER NOT NULL,            -- anoReferencia

    -- Valores principais
    valor_fatura DECIMAL(10, 2) NOT NULL,       -- valorFatura
    valor_liquido DECIMAL(10, 2),               -- valorLiquido
    consumo INTEGER,                            -- consumo (kWh)
    leitura_atual INTEGER,                      -- leituraAtual
    leitura_anterior INTEGER,                   -- leituraAnterior
    media_consumo INTEGER,                      -- mediaConsumo
    quantidade_dias INTEGER,                    -- quantidadeDiaConsumo

    -- Impostos e taxas
    valor_iluminacao_publica DECIMAL(10, 2),   -- valorIluminacaoPublica
    valor_icms DECIMAL(10, 2),                 -- valorICMS
    bandeira_tarifaria VARCHAR(20),            -- bandeiraTarifaria

    -- Datas
    data_leitura DATE,                         -- dataLeitura
    data_vencimento DATE NOT NULL,             -- dataVencimento
    data_pagamento DATE,                       -- dataPagamento

    -- Status
    indicador_situacao INTEGER,                -- indicadorSituacao
    indicador_pagamento BOOLEAN,               -- indicadorPagamento
    situacao_pagamento VARCHAR(30),            -- situacaoPagamento

    -- Detalhamento
    servico_distribuicao DECIMAL(10, 2),
    compra_energia DECIMAL(10, 2),
    servico_transmissao DECIMAL(10, 2),
    encargos_setoriais DECIMAL(10, 2),
    impostos_encargos DECIMAL(10, 2),

    -- PIX/Boleto
    qr_code_pix TEXT,
    codigo_barras VARCHAR(100),

    -- PDF
    pdf_path VARCHAR(500),
    pdf_baixado_em TIMESTAMPTZ,

    -- JSON completo da API (GUARDAR TUDO para histórico permanente)
    dados_api JSONB NOT NULL,

    -- Controle
    sincronizado_em TIMESTAMPTZ DEFAULT NOW(),
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(uc_id, mes_referencia, ano_referencia)
);

CREATE INDEX idx_faturas_uc ON faturas(uc_id);
CREATE INDEX idx_faturas_referencia ON faturas(ano_referencia, mes_referencia);
CREATE INDEX idx_faturas_vencimento ON faturas(data_vencimento);
CREATE INDEX idx_faturas_numero ON faturas(numero_fatura);

-- 13. HISTORICO_GD
-- Histórico de créditos GD (endpoint /gd/details)
CREATE TABLE historico_gd (
    id SERIAL PRIMARY KEY,
    uc_id INTEGER NOT NULL REFERENCES unidades_consumidoras(id),

    -- Referência
    mes_referencia INTEGER NOT NULL,
    ano_referencia INTEGER NOT NULL,

    -- Saldos e valores (campos do gd_details)
    saldo_anterior_conv INTEGER,               -- saldoAnteriorConv
    injetado_conv INTEGER,                     -- injetadoConv
    total_recebido_rede INTEGER,               -- totalRecebidoRede
    consumo_recebido_conv INTEGER,             -- consumoRecebidoConv
    consumo_injetado_compensado INTEGER,       -- consumoInjetadoCompensadoConv
    consumo_transferido_conv INTEGER,          -- consumoTransferidoConv
    consumo_compensado_conv INTEGER,           -- consumoCompensadoConv
    saldo_compensado_anterior INTEGER,         -- saldoCompensadoAnteriorConv

    -- Composição da energia (JSON arrays)
    composicao_energia JSONB,                  -- composicaoEnergiaInjetadas
    discriminacao_energia JSONB,               -- discriminacaoEnergiaInjetadas

    -- Metadados
    chave_primaria VARCHAR(50),                -- chavePrimaria
    data_modificacao_registro TIMESTAMPTZ,     -- dataModificacaoRegistro

    -- JSON completo da API
    dados_api JSONB NOT NULL,

    sincronizado_em TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(uc_id, mes_referencia, ano_referencia)
);

CREATE INDEX idx_historico_gd_uc ON historico_gd(uc_id);
CREATE INDEX idx_historico_gd_referencia ON historico_gd(ano_referencia, mes_referencia);

-- 14. COBRANCAS
-- Cobranças geradas para beneficiários
CREATE TABLE cobrancas (
    id SERIAL PRIMARY KEY,
    beneficiario_id INTEGER NOT NULL REFERENCES beneficiarios(id),
    fatura_id INTEGER REFERENCES faturas(id),

    mes INTEGER NOT NULL,
    ano INTEGER NOT NULL,

    -- Valores calculados
    kwh_creditado INTEGER NOT NULL,
    tarifa_energisa DECIMAL(10, 6) NOT NULL,
    desconto_aplicado DECIMAL(5, 4) NOT NULL,

    valor_energia DECIMAL(10, 2) NOT NULL,
    valor_piso DECIMAL(10, 2) NOT NULL,
    valor_iluminacao DECIMAL(10, 2) NOT NULL,
    valor_total DECIMAL(10, 2) NOT NULL,
    valor_sem_desconto DECIMAL(10, 2),
    economia DECIMAL(10, 2),

    -- Pagamento
    vencimento DATE NOT NULL,
    status cobranca_status DEFAULT 'PENDENTE',
    pago_em TIMESTAMPTZ,
    forma_pagamento VARCHAR(20),
    comprovante_path VARCHAR(500),

    -- Boleto/PIX
    codigo_barras VARCHAR(100),
    pix_copia_cola TEXT,

    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(beneficiario_id, mes, ano)
);

CREATE INDEX idx_cobrancas_beneficiario ON cobrancas(beneficiario_id);
CREATE INDEX idx_cobrancas_vencimento ON cobrancas(vencimento);
CREATE INDEX idx_cobrancas_status ON cobrancas(status);

-- 15. SAQUES
-- Solicitações de saque
CREATE TABLE saques (
    id SERIAL PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id),

    valor DECIMAL(10, 2) NOT NULL,

    -- Dados bancários
    banco VARCHAR(100),
    agencia VARCHAR(10),
    conta VARCHAR(20),
    tipo_conta VARCHAR(20),
    pix_chave VARCHAR(100),

    -- Nota fiscal
    nf_numero VARCHAR(50),
    nf_path VARCHAR(500),
    nf_validada BOOLEAN DEFAULT FALSE,

    -- Status
    status saque_status DEFAULT 'PENDENTE',
    aprovado_por_id UUID REFERENCES usuarios(id),
    aprovado_em TIMESTAMPTZ,
    motivo_rejeicao TEXT,
    pago_em TIMESTAMPTZ,
    comprovante_path VARCHAR(500),

    criado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_saques_usuario ON saques(usuario_id);
CREATE INDEX idx_saques_status ON saques(status);

-- 16. NOTIFICACOES
-- Notificações do sistema
CREATE TABLE notificacoes (
    id SERIAL PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id),

    tipo notificacao_tipo NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    mensagem TEXT,
    link VARCHAR(500),
    acao VARCHAR(50),

    -- Referência opcional a outra entidade
    referencia_tipo VARCHAR(50),
    referencia_id INTEGER,

    lida BOOLEAN DEFAULT FALSE,
    lida_em TIMESTAMPTZ,

    criado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notificacoes_usuario ON notificacoes(usuario_id);
CREATE INDEX idx_notificacoes_lida ON notificacoes(usuario_id, lida);

-- 17. CONFIG_PLATAFORMA
-- Configurações globais da plataforma
CREATE TABLE config_plataforma (
    id SERIAL PRIMARY KEY,
    chave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT NOT NULL,
    tipo VARCHAR(20) DEFAULT 'STRING',         -- STRING, NUMBER, BOOLEAN, JSON
    descricao TEXT,
    editavel BOOLEAN DEFAULT TRUE,

    atualizado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_por_id UUID REFERENCES usuarios(id)
);

-- Configurações iniciais
INSERT INTO config_plataforma (chave, valor, tipo, descricao) VALUES
('taxa_plataforma_percentual', '0.05', 'NUMBER', 'Taxa da plataforma sobre valor energia (5%)'),
('dias_vencimento_antes_energisa', '1', 'NUMBER', 'Dias antes do vencimento Energisa'),
('template_contrato_beneficiario', '', 'STRING', 'Template HTML do contrato beneficiário'),
('template_contrato_gestor', '', 'STRING', 'Template HTML do contrato gestor'),
('notificacao_vencimento_dias', '5', 'NUMBER', 'Dias antes para notificar vencimento'),
('email_suporte', 'suporte@plataformagd.com', 'STRING', 'Email de suporte'),
('telefone_suporte', '', 'STRING', 'Telefone de suporte');

-- 18. LEADS
-- Leads capturados da landing page (simulação)
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,

    -- Dados do lead
    cpf VARCHAR(14),
    nome VARCHAR(200),
    email VARCHAR(100),
    telefone VARCHAR(20),

    -- Dados da simulação
    consumo_medio INTEGER,                   -- kWh médio informado
    valor_conta_media DECIMAL(10, 2),        -- Valor médio da conta
    tipo_ligacao VARCHAR(20),                -- MONOFASICO, BIFASICO, TRIFASICO
    cidade VARCHAR(100),
    uf VARCHAR(2),

    -- Resultado da simulação (JSON)
    dados_simulacao JSONB,

    -- Atribuição
    usina_id INTEGER REFERENCES usinas(id),
    gestor_id UUID REFERENCES usuarios(id),

    -- Status e acompanhamento
    status lead_status DEFAULT 'NOVO',
    origem VARCHAR(50),                       -- landing_page, indicacao, etc
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),

    -- Histórico de interações (JSON array)
    interacoes JSONB DEFAULT '[]',

    convertido_em TIMESTAMPTZ,
    usuario_convertido_id UUID REFERENCES usuarios(id),

    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_leads_cpf ON leads(cpf);
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_gestor ON leads(gestor_id);

-- ============================================================================
-- PARTE 3: TABELAS DO MÓDULO MARKETPLACE (10 tabelas)
-- ============================================================================

-- 19. PARCEIROS
-- Parceiros/Integradores que vendem projetos solares
CREATE TABLE parceiros (
    id SERIAL PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id),

    -- Dados da empresa
    cnpj VARCHAR(18) UNIQUE NOT NULL,
    razao_social VARCHAR(200) NOT NULL,
    nome_fantasia VARCHAR(200),
    inscricao_estadual VARCHAR(20),

    -- Endereço
    endereco VARCHAR(300),
    cidade VARCHAR(100),
    uf VARCHAR(2),
    cep VARCHAR(10),

    -- Contato
    telefone VARCHAR(20),
    email VARCHAR(100),
    website VARCHAR(200),

    -- Configurações
    logo_url VARCHAR(500),
    descricao TEXT,
    areas_atuacao JSONB,                     -- ["MT", "MS", "GO"]
    tipos_projeto JSONB,                      -- ["residencial", "comercial", "industrial"]

    -- Financeiro
    comissao_plataforma DECIMAL(5, 4) DEFAULT 0.05,
    dados_bancarios JSONB,

    -- Status
    status parceiro_status DEFAULT 'PENDENTE',
    aprovado_por_id UUID REFERENCES usuarios(id),
    aprovado_em TIMESTAMPTZ,

    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_parceiros_usuario ON parceiros(usuario_id);
CREATE INDEX idx_parceiros_cnpj ON parceiros(cnpj);
CREATE INDEX idx_parceiros_status ON parceiros(status);

-- 20. EQUIPE_PARCEIRO
-- Membros da equipe do parceiro
CREATE TABLE equipe_parceiro (
    id SERIAL PRIMARY KEY,
    parceiro_id INTEGER NOT NULL REFERENCES parceiros(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuarios(id),

    papel membro_papel NOT NULL,
    permissoes JSONB DEFAULT '{}',

    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(parceiro_id, usuario_id)
);

CREATE INDEX idx_equipe_parceiro ON equipe_parceiro(parceiro_id);
CREATE INDEX idx_equipe_usuario ON equipe_parceiro(usuario_id);

-- 21. PRODUTOS_MARKETPLACE
-- Produtos anunciados no marketplace
CREATE TABLE produtos_marketplace (
    id SERIAL PRIMARY KEY,
    parceiro_id INTEGER NOT NULL REFERENCES parceiros(id),

    -- Identificação
    tipo produto_tipo NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    slug VARCHAR(200) UNIQUE,

    -- Para PROJETO_SOLAR
    potencia_kwp DECIMAL(10, 2),
    producao_estimada INTEGER,
    economia_estimada DECIMAL(10, 2),

    -- Para ENERGIA_COMPARTILHADA
    usina_id INTEGER REFERENCES usinas(id),
    desconto_oferecido DECIMAL(5, 4),
    kwh_disponiveis INTEGER,

    -- Preço
    preco DECIMAL(12, 2),
    preco_kwp DECIMAL(10, 2),
    aceita_financiamento BOOLEAN DEFAULT TRUE,
    parcelas_max INTEGER DEFAULT 60,

    -- Mídia
    imagens JSONB DEFAULT '[]',
    video_url VARCHAR(500),
    documentos JSONB DEFAULT '[]',

    -- Localização (para projetos)
    cidade VARCHAR(100),
    uf VARCHAR(2),
    cep VARCHAR(10),

    -- Status e aprovação
    status produto_status DEFAULT 'RASCUNHO',
    aprovado_por_id UUID REFERENCES usuarios(id),
    aprovado_em TIMESTAMPTZ,
    motivo_reprovacao TEXT,

    -- Métricas
    visualizacoes INTEGER DEFAULT 0,
    leads_gerados INTEGER DEFAULT 0,

    -- Destaque
    destaque BOOLEAN DEFAULT FALSE,
    destaque_ate TIMESTAMPTZ,

    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_produtos_parceiro ON produtos_marketplace(parceiro_id);
CREATE INDEX idx_produtos_tipo ON produtos_marketplace(tipo);
CREATE INDEX idx_produtos_status ON produtos_marketplace(status);
CREATE INDEX idx_produtos_uf ON produtos_marketplace(uf);
CREATE INDEX idx_produtos_destaque ON produtos_marketplace(destaque) WHERE destaque = TRUE;

-- 22. KANBAN_PIPELINES
-- Pipelines customizáveis (cada parceiro pode criar seus próprios)
CREATE TABLE kanban_pipelines (
    id SERIAL PRIMARY KEY,
    parceiro_id INTEGER NOT NULL REFERENCES parceiros(id) ON DELETE CASCADE,

    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    padrao BOOLEAN DEFAULT FALSE,

    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(parceiro_id, nome)
);

CREATE INDEX idx_pipelines_parceiro ON kanban_pipelines(parceiro_id);

-- 23. KANBAN_COLUNAS
-- Colunas/etapas do pipeline (totalmente customizáveis)
CREATE TABLE kanban_colunas (
    id SERIAL PRIMARY KEY,
    pipeline_id INTEGER NOT NULL REFERENCES kanban_pipelines(id) ON DELETE CASCADE,

    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    cor VARCHAR(7) DEFAULT '#3b82f6',
    icone VARCHAR(50),

    ordem INTEGER NOT NULL,
    limite_cards INTEGER,

    -- Ações automáticas
    automacoes JSONB DEFAULT '{}',

    criado_em TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(pipeline_id, ordem)
);

CREATE INDEX idx_colunas_pipeline ON kanban_colunas(pipeline_id);

-- 24. FORMULARIOS_DINAMICOS
-- Formulários customizáveis por etapa/coluna
CREATE TABLE formularios_dinamicos (
    id SERIAL PRIMARY KEY,
    parceiro_id INTEGER NOT NULL REFERENCES parceiros(id) ON DELETE CASCADE,
    coluna_id INTEGER REFERENCES kanban_colunas(id) ON DELETE SET NULL,

    nome VARCHAR(100) NOT NULL,
    descricao TEXT,

    -- Campos do formulário (JSON Schema)
    campos JSONB NOT NULL,
    /*
    Exemplo de campos:
    [
        { "id": "nome_cliente", "tipo": "text", "label": "Nome do Cliente", "obrigatorio": true },
        { "id": "consumo_medio", "tipo": "number", "label": "Consumo Médio (kWh)", "min": 0 },
        { "id": "tipo_telhado", "tipo": "select", "label": "Tipo de Telhado", "opcoes": ["Cerâmico", "Metálico"] },
        { "id": "fotos_local", "tipo": "file", "label": "Fotos", "multiplo": true, "aceita": ["image/*"] }
    ]
    */

    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_formularios_parceiro ON formularios_dinamicos(parceiro_id);
CREATE INDEX idx_formularios_coluna ON formularios_dinamicos(coluna_id);

-- 25. PROJETOS
-- Projetos solares em andamento
CREATE TABLE projetos (
    id SERIAL PRIMARY KEY,
    parceiro_id INTEGER NOT NULL REFERENCES parceiros(id),
    pipeline_id INTEGER NOT NULL REFERENCES kanban_pipelines(id),
    coluna_id INTEGER NOT NULL REFERENCES kanban_colunas(id),
    produto_id INTEGER REFERENCES produtos_marketplace(id),

    -- Origem
    lead_id INTEGER REFERENCES leads(id),
    origem VARCHAR(50),

    -- Cliente
    cliente_nome VARCHAR(200) NOT NULL,
    cliente_cpf_cnpj VARCHAR(18),
    cliente_email VARCHAR(100),
    cliente_telefone VARCHAR(20),
    cliente_endereco VARCHAR(300),
    cliente_cidade VARCHAR(100),
    cliente_uf VARCHAR(2),
    cliente_cep VARCHAR(10),

    -- Dados técnicos do projeto
    potencia_kwp DECIMAL(10, 2),
    producao_estimada INTEGER,
    consumo_medio INTEGER,
    tipo_instalacao VARCHAR(50),
    tipo_telhado VARCHAR(50),
    area_disponivel DECIMAL(10, 2),

    -- Equipamentos (JSON)
    equipamentos JSONB,

    -- Valores
    valor_total DECIMAL(12, 2),
    custo_equipamentos DECIMAL(12, 2),
    custo_instalacao DECIMAL(12, 2),
    margem DECIMAL(12, 2),
    desconto DECIMAL(10, 2),
    valor_final DECIMAL(12, 2),

    -- Financiamento
    financiado BOOLEAN DEFAULT FALSE,
    banco_financiamento VARCHAR(100),
    parcelas INTEGER,
    valor_parcela DECIMAL(10, 2),
    taxa_juros DECIMAL(5, 4),

    -- Status
    status projeto_status DEFAULT 'LEAD',
    probabilidade INTEGER DEFAULT 50,

    -- Responsáveis
    vendedor_id UUID REFERENCES usuarios(id),
    tecnico_id UUID REFERENCES usuarios(id),

    -- Datas importantes
    data_visita TIMESTAMPTZ,
    data_proposta TIMESTAMPTZ,
    data_venda TIMESTAMPTZ,
    data_instalacao_prevista DATE,
    data_instalacao_real DATE,
    data_homologacao DATE,
    previsao_conclusao DATE,

    -- Formulários preenchidos (respostas)
    formularios_dados JSONB DEFAULT '{}',

    -- Arquivos
    arquivos JSONB DEFAULT '[]',

    -- Observações
    observacoes TEXT,

    -- Comissão da plataforma
    comissao_plataforma DECIMAL(10, 2),
    comissao_paga BOOLEAN DEFAULT FALSE,
    comissao_paga_em TIMESTAMPTZ,

    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_projetos_parceiro ON projetos(parceiro_id);
CREATE INDEX idx_projetos_pipeline ON projetos(pipeline_id);
CREATE INDEX idx_projetos_coluna ON projetos(coluna_id);
CREATE INDEX idx_projetos_status ON projetos(status);
CREATE INDEX idx_projetos_vendedor ON projetos(vendedor_id);
CREATE INDEX idx_projetos_cliente_cpf ON projetos(cliente_cpf_cnpj);

-- 26. PROJETO_HISTORICO
-- Histórico de movimentações do projeto
CREATE TABLE projeto_historico (
    id SERIAL PRIMARY KEY,
    projeto_id INTEGER NOT NULL REFERENCES projetos(id) ON DELETE CASCADE,
    usuario_id UUID REFERENCES usuarios(id),

    -- Tipo de evento
    tipo VARCHAR(50) NOT NULL,
    descricao TEXT,

    -- Dados da alteração
    dados_anteriores JSONB,
    dados_novos JSONB,

    criado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_historico_projeto ON projeto_historico(projeto_id);
CREATE INDEX idx_historico_criado ON projeto_historico(criado_em);

-- 27. PROJETO_TAREFAS
-- Tarefas/atividades do projeto
CREATE TABLE projeto_tarefas (
    id SERIAL PRIMARY KEY,
    projeto_id INTEGER NOT NULL REFERENCES projetos(id) ON DELETE CASCADE,

    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    prioridade tarefa_prioridade DEFAULT 'MEDIA',

    responsavel_id UUID REFERENCES usuarios(id),
    data_vencimento DATE,

    status tarefa_status DEFAULT 'PENDENTE',
    concluida_em TIMESTAMPTZ,
    concluida_por_id UUID REFERENCES usuarios(id),

    criado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tarefas_projeto ON projeto_tarefas(projeto_id);
CREATE INDEX idx_tarefas_responsavel ON projeto_tarefas(responsavel_id);
CREATE INDEX idx_tarefas_status ON projeto_tarefas(status);

-- 28. TRANSACOES_MARKETPLACE
-- Transações financeiras do marketplace
CREATE TABLE transacoes_marketplace (
    id SERIAL PRIMARY KEY,
    projeto_id INTEGER REFERENCES projetos(id),
    parceiro_id INTEGER NOT NULL REFERENCES parceiros(id),

    tipo transacao_tipo NOT NULL,
    valor DECIMAL(12, 2) NOT NULL,
    descricao TEXT,

    -- Para comissões
    percentual_comissao DECIMAL(5, 4),
    valor_base DECIMAL(12, 2),

    status transacao_status DEFAULT 'PENDENTE',
    processado_em TIMESTAMPTZ,
    comprovante_url VARCHAR(500),

    criado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transacoes_projeto ON transacoes_marketplace(projeto_id);
CREATE INDEX idx_transacoes_parceiro ON transacoes_marketplace(parceiro_id);
CREATE INDEX idx_transacoes_status ON transacoes_marketplace(status);

-- ============================================================================
-- PARTE 4: TRIGGERS E FUNÇÕES AUXILIARES
-- ============================================================================

-- Função para atualizar o campo atualizado_em automaticamente
CREATE OR REPLACE FUNCTION update_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger nas tabelas que têm atualizado_em
CREATE TRIGGER tr_usuarios_atualizado_em
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_perfis_usuario_atualizado_em
    BEFORE UPDATE ON perfis_usuario
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_tokens_energisa_atualizado_em
    BEFORE UPDATE ON tokens_energisa
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_unidades_consumidoras_atualizado_em
    BEFORE UPDATE ON unidades_consumidoras
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_empresas_atualizado_em
    BEFORE UPDATE ON empresas
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_usinas_atualizado_em
    BEFORE UPDATE ON usinas
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_beneficiarios_atualizado_em
    BEFORE UPDATE ON beneficiarios
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_contratos_atualizado_em
    BEFORE UPDATE ON contratos
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_faturas_atualizado_em
    BEFORE UPDATE ON faturas
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_cobrancas_atualizado_em
    BEFORE UPDATE ON cobrancas
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_leads_atualizado_em
    BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_parceiros_atualizado_em
    BEFORE UPDATE ON parceiros
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_produtos_marketplace_atualizado_em
    BEFORE UPDATE ON produtos_marketplace
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_kanban_pipelines_atualizado_em
    BEFORE UPDATE ON kanban_pipelines
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_formularios_dinamicos_atualizado_em
    BEFORE UPDATE ON formularios_dinamicos
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

CREATE TRIGGER tr_projetos_atualizado_em
    BEFORE UPDATE ON projetos
    FOR EACH ROW EXECUTE FUNCTION update_atualizado_em();

-- ============================================================================
-- PARTE 5: FUNÇÕES ÚTEIS
-- ============================================================================

-- Função para formatar UC no padrão de exibição (cod_empresa/cdc-digito)
CREATE OR REPLACE FUNCTION formatar_uc(
    cod_empresa INTEGER,
    cdc INTEGER,
    digito_verificador INTEGER
) RETURNS TEXT AS $$
BEGIN
    RETURN cod_empresa::TEXT || '/' || cdc::TEXT || '-' || digito_verificador::TEXT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Exemplo de uso: SELECT formatar_uc(6, 4242904, 3); -- Retorna: '6/4242904-3'

-- Função para buscar UC pelo formato
CREATE OR REPLACE FUNCTION buscar_uc_por_formato(uc_formatada TEXT)
RETURNS TABLE(id INTEGER, cod_empresa INTEGER, cdc INTEGER, digito_verificador INTEGER) AS $$
DECLARE
    partes TEXT[];
    empresa INT;
    cdc_val INT;
    dv INT;
BEGIN
    -- Parse do formato: 6/4242904-3
    partes := regexp_split_to_array(uc_formatada, '[/-]');

    IF array_length(partes, 1) != 3 THEN
        RETURN;
    END IF;

    empresa := partes[1]::INTEGER;
    cdc_val := partes[2]::INTEGER;
    dv := partes[3]::INTEGER;

    RETURN QUERY
    SELECT uc.id, uc.cod_empresa, uc.cdc, uc.digito_verificador
    FROM unidades_consumidoras uc
    WHERE uc.cod_empresa = empresa
      AND uc.cdc = cdc_val
      AND uc.digito_verificador = dv;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FIM DA MIGRAÇÃO
-- ============================================================================

-- Verificação final: contar tabelas criadas
DO $$
DECLARE
    qtd_tabelas INTEGER;
BEGIN
    SELECT COUNT(*) INTO qtd_tabelas
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE';

    RAISE NOTICE 'Migração concluída! Total de tabelas criadas: %', qtd_tabelas;
END;
$$;

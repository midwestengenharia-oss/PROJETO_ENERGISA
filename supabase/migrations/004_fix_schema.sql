-- ============================================================================
-- CORREÇÃO DO SCHEMA - PLATAFORMA GD
-- Execute no Supabase SQL Editor
-- ============================================================================

-- 1. Atualizar enum lead_status para incluir valores usados no código
ALTER TYPE lead_status ADD VALUE IF NOT EXISTS 'SIMULACAO';
ALTER TYPE lead_status ADD VALUE IF NOT EXISTS 'CONTATO';
ALTER TYPE lead_status ADD VALUE IF NOT EXISTS 'NEGOCIACAO';

-- 2. Criar view 'ucs' como alias para unidades_consumidoras
CREATE OR REPLACE VIEW ucs AS SELECT * FROM unidades_consumidoras;

-- 3. Criar tabela de simulações de leads
CREATE TABLE IF NOT EXISTS simulacoes (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    valor_fatura_media DECIMAL(10, 2),
    consumo_medio_kwh INTEGER,
    quantidade_ucs INTEGER DEFAULT 1,

    desconto_aplicado DECIMAL(5, 4),
    economia_mensal DECIMAL(10, 2),
    economia_anual DECIMAL(10, 2),
    percentual_economia DECIMAL(5, 2),

    criado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_simulacoes_lead ON simulacoes(lead_id);

-- 4. Criar tabela de contatos de leads
CREATE TABLE IF NOT EXISTS contatos (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    tipo_contato VARCHAR(50) NOT NULL,
    descricao TEXT,
    proximo_contato TIMESTAMPTZ,
    realizado_por UUID REFERENCES usuarios(id),

    criado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contatos_lead ON contatos(lead_id);

-- 5. Criar tabela de configurações do sistema
CREATE TABLE IF NOT EXISTS configuracoes_sistema (
    id SERIAL PRIMARY KEY,
    chave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT,
    tipo VARCHAR(20) DEFAULT 'STRING',
    descricao TEXT,
    editavel BOOLEAN DEFAULT TRUE,

    atualizado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_por UUID REFERENCES usuarios(id)
);

-- 6. Criar tabela de logs de auditoria
CREATE TABLE IF NOT EXISTS logs_auditoria (
    id SERIAL PRIMARY KEY,
    usuario_id UUID REFERENCES usuarios(id),

    acao VARCHAR(50) NOT NULL,
    entidade VARCHAR(50),
    entidade_id INTEGER,

    dados_anteriores JSONB,
    dados_novos JSONB,
    ip_address INET,
    user_agent TEXT,

    criado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_usuario ON logs_auditoria(usuario_id);
CREATE INDEX IF NOT EXISTS idx_logs_criado ON logs_auditoria(criado_em);

-- 7. Adicionar campos faltantes na tabela leads (se não existirem)
DO $$
BEGIN
    -- Adiciona responsavel_id se não existir
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'leads' AND column_name = 'responsavel_id') THEN
        ALTER TABLE leads ADD COLUMN responsavel_id UUID REFERENCES usuarios(id);
    END IF;

    -- Adiciona observacoes se não existir
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'leads' AND column_name = 'observacoes') THEN
        ALTER TABLE leads ADD COLUMN observacoes TEXT;
    END IF;

    -- Adiciona beneficiario_id se não existir
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'leads' AND column_name = 'beneficiario_id') THEN
        ALTER TABLE leads ADD COLUMN beneficiario_id INTEGER REFERENCES beneficiarios(id);
    END IF;
END;
$$;

-- ============================================================================
-- Verificação
-- ============================================================================
DO $$
DECLARE
    qtd_tabelas INTEGER;
BEGIN
    SELECT COUNT(*) INTO qtd_tabelas
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name IN ('simulacoes', 'contatos', 'configuracoes_sistema', 'logs_auditoria');

    RAISE NOTICE 'Correção concluída! Novas tabelas criadas: %', qtd_tabelas;
END;
$$;

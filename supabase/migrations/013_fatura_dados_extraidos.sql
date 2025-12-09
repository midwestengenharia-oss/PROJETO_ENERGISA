-- ===================================================================
-- Migração 013: Suporte para Extração de Dados das Faturas
-- ===================================================================
-- Adiciona campos para armazenar dados estruturados extraídos das faturas
-- via OCR/IA para posterior geração automatizada de cobranças

-- Adicionar campos de extração na tabela faturas
ALTER TABLE faturas
ADD COLUMN IF NOT EXISTS dados_extraidos JSONB,
ADD COLUMN IF NOT EXISTS extracao_status VARCHAR(20) DEFAULT 'PENDENTE',
ADD COLUMN IF NOT EXISTS extracao_error TEXT,
ADD COLUMN IF NOT EXISTS extraido_em TIMESTAMPTZ;

-- Comentários das colunas
COMMENT ON COLUMN faturas.dados_extraidos IS 'Dados estruturados extraídos do PDF da fatura via IA';
COMMENT ON COLUMN faturas.extracao_status IS 'Status da extração: PENDENTE, PROCESSANDO, CONCLUIDA, ERRO';
COMMENT ON COLUMN faturas.extracao_error IS 'Mensagem de erro caso a extração falhe';
COMMENT ON COLUMN faturas.extraido_em IS 'Timestamp de quando os dados foram extraídos';

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_faturas_extracao_status
ON faturas(extracao_status);

CREATE INDEX IF NOT EXISTS idx_faturas_dados_extraidos
ON faturas USING GIN(dados_extraidos);

-- Validação: extracao_status só pode ter valores específicos
ALTER TABLE faturas
ADD CONSTRAINT check_extracao_status
CHECK (extracao_status IN ('PENDENTE', 'PROCESSANDO', 'CONCLUIDA', 'ERRO'));

-- View auxiliar para faturas pendentes de extração
CREATE OR REPLACE VIEW faturas_pendentes_extracao AS
SELECT
    f.id,
    f.uc_id,
    f.numero_fatura,
    f.mes_referencia,
    f.ano_referencia,
    f.extracao_status,
    CASE
        WHEN f.pdf_base64 IS NOT NULL THEN true
        ELSE false
    END as tem_pdf
FROM faturas f
WHERE f.extracao_status = 'PENDENTE'
  AND f.pdf_base64 IS NOT NULL
ORDER BY f.ano_referencia DESC, f.mes_referencia DESC;

COMMENT ON VIEW faturas_pendentes_extracao IS 'Faturas com PDF disponível mas ainda não processadas';

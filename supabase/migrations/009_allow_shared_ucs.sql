-- Migration: Permite que a mesma UC seja vinculada a diferentes usuários
-- E permite que mesmas faturas existam para diferentes vínculos de UC

-- =====================
-- TABELA unidades_consumidoras
-- =====================

-- Remove a constraint antiga (UC única globalmente)
ALTER TABLE unidades_consumidoras
DROP CONSTRAINT IF EXISTS unidades_consumidoras_cod_empresa_cdc_digito_verificador_key;

-- Adiciona nova constraint (UC única por usuário)
ALTER TABLE unidades_consumidoras
ADD CONSTRAINT unidades_consumidoras_usuario_uc_unique
UNIQUE (usuario_id, cod_empresa, cdc, digito_verificador);

COMMENT ON CONSTRAINT unidades_consumidoras_usuario_uc_unique ON unidades_consumidoras
IS 'Cada usuário pode vincular uma UC apenas uma vez, mas diferentes usuários podem vincular a mesma UC';

-- =====================
-- TABELA faturas
-- =====================

-- Remove constraint única de numero_fatura (mesmo número pode existir para UCs diferentes)
ALTER TABLE faturas
DROP CONSTRAINT IF EXISTS faturas_numero_fatura_key;

-- O upsert já usa (uc_id, mes_referencia, ano_referencia) que é a chave correta

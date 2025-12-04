-- ============================================================================
-- PLATAFORMA GD - SEED DATA (DADOS INICIAIS)
-- ============================================================================
-- Este arquivo cria dados iniciais para desenvolvimento/testes
-- Executar APÓS as migrações anteriores
-- ============================================================================

-- ============================================================================
-- 1. CONFIGURAÇÕES DA PLATAFORMA
-- ============================================================================

-- Inserir configurações padrão (se não existirem)
INSERT INTO config_plataforma (chave, valor, tipo, descricao)
VALUES
    -- Taxas e valores
    ('taxa_plataforma_percentual', '0.05', 'NUMBER', 'Taxa da plataforma sobre valor energia (5%)'),
    ('taxa_plataforma_kwh', '0.01', 'NUMBER', 'Taxa por kWh movimentado (R$ 0,01)'),

    -- Vencimentos
    ('dias_vencimento_antes_energisa', '1', 'NUMBER', 'Dias antes do vencimento Energisa para cobrança'),
    ('notificacao_vencimento_dias', '5', 'NUMBER', 'Dias antes para notificar vencimento'),
    ('dias_expiracao_convite', '7', 'NUMBER', 'Dias para expirar um convite'),

    -- Contratos (templates serão adicionados depois)
    ('template_contrato_beneficiario', '', 'STRING', 'Template HTML do contrato com beneficiário'),
    ('template_contrato_gestor', '', 'STRING', 'Template HTML do contrato com gestor'),

    -- Contato
    ('email_suporte', 'suporte@plataformagd.com', 'STRING', 'Email de suporte'),
    ('telefone_suporte', '', 'STRING', 'Telefone de suporte'),
    ('whatsapp_suporte', '', 'STRING', 'WhatsApp de suporte'),

    -- Limites
    ('limite_beneficiarios_por_usina', '100', 'NUMBER', 'Máximo de beneficiários por usina'),
    ('limite_ucs_por_usuario', '50', 'NUMBER', 'Máximo de UCs por usuário'),

    -- Fio B - Escalonamento ANEEL (2023-2028)
    ('fiob_2023', '0.15', 'NUMBER', 'Fator Fio B para 2023 (15%)'),
    ('fiob_2024', '0.30', 'NUMBER', 'Fator Fio B para 2024 (30%)'),
    ('fiob_2025', '0.45', 'NUMBER', 'Fator Fio B para 2025 (45%)'),
    ('fiob_2026', '0.60', 'NUMBER', 'Fator Fio B para 2026 (60%)'),
    ('fiob_2027', '0.75', 'NUMBER', 'Fator Fio B para 2027 (75%)'),
    ('fiob_2028', '0.90', 'NUMBER', 'Fator Fio B para 2028 (90%)'),

    -- Taxa mínima por tipo de ligação (kWh/mês)
    ('taxa_minima_monofasico', '30', 'NUMBER', 'Taxa mínima em kWh para ligação monofásica'),
    ('taxa_minima_bifasico', '50', 'NUMBER', 'Taxa mínima em kWh para ligação bifásica'),
    ('taxa_minima_trifasico', '100', 'NUMBER', 'Taxa mínima em kWh para ligação trifásica'),

    -- Tributos (referência, podem ser atualizados)
    ('pis_percentual', '0.012102', 'NUMBER', 'Alíquota PIS'),
    ('cofins_percentual', '0.055743', 'NUMBER', 'Alíquota COFINS'),
    ('icms_percentual', '0.17', 'NUMBER', 'Alíquota ICMS MT'),

    -- Marketplace
    ('comissao_marketplace_padrao', '0.05', 'NUMBER', 'Comissão padrão do marketplace (5%)'),
    ('destaque_produto_dias', '30', 'NUMBER', 'Duração padrão do destaque em dias'),
    ('destaque_produto_valor', '99.90', 'NUMBER', 'Valor para destacar produto (R$)'),

    -- URLs
    ('url_landing_page', '', 'STRING', 'URL da landing page'),
    ('url_termos_uso', '', 'STRING', 'URL dos termos de uso'),
    ('url_politica_privacidade', '', 'STRING', 'URL da política de privacidade'),

    -- Integração Energisa
    ('energisa_gateway_url', 'http://localhost:8000', 'STRING', 'URL do gateway Energisa'),
    ('energisa_token_expiracao_horas', '24', 'NUMBER', 'Horas de expiração do token Energisa')

ON CONFLICT (chave) DO NOTHING;

-- ============================================================================
-- 2. PIPELINE KANBAN PADRÃO (Template para novos parceiros)
-- ============================================================================

-- Nota: Este é um template. Quando um novo parceiro for criado,
-- copiar este pipeline para ele.

-- Para uso em desenvolvimento, criar um parceiro fictício primeiro (se necessário)
-- Este bloco é comentado pois requer um usuário real

/*
-- Exemplo de criação de pipeline padrão para um parceiro
DO $$
DECLARE
    v_parceiro_id INTEGER;
    v_pipeline_id INTEGER;
BEGIN
    -- Buscar ou criar parceiro de desenvolvimento
    SELECT id INTO v_parceiro_id FROM parceiros LIMIT 1;

    IF v_parceiro_id IS NOT NULL THEN
        -- Criar pipeline padrão
        INSERT INTO kanban_pipelines (parceiro_id, nome, descricao, padrao)
        VALUES (v_parceiro_id, 'Pipeline Padrão Solar', 'Pipeline padrão para projetos solares', TRUE)
        RETURNING id INTO v_pipeline_id;

        -- Criar colunas do pipeline
        INSERT INTO kanban_colunas (pipeline_id, nome, descricao, cor, icone, ordem) VALUES
        (v_pipeline_id, 'Lead', 'Leads recebidos', '#94a3b8', 'inbox', 1),
        (v_pipeline_id, 'Qualificação', 'Em qualificação', '#3b82f6', 'filter', 2),
        (v_pipeline_id, 'Visita Técnica', 'Agendada/realizada visita', '#8b5cf6', 'map-pin', 3),
        (v_pipeline_id, 'Orçamento', 'Orçamento em elaboração', '#f59e0b', 'calculator', 4),
        (v_pipeline_id, 'Proposta', 'Proposta enviada', '#ec4899', 'file-text', 5),
        (v_pipeline_id, 'Negociação', 'Em negociação', '#14b8a6', 'message-circle', 6),
        (v_pipeline_id, 'Venda', 'Venda fechada!', '#22c55e', 'check-circle', 7),
        (v_pipeline_id, 'Instalação', 'Em instalação', '#0ea5e9', 'tool', 8),
        (v_pipeline_id, 'Homologação', 'Aguardando homologação', '#a855f7', 'clock', 9),
        (v_pipeline_id, 'Concluído', 'Projeto concluído', '#10b981', 'award', 10);

        RAISE NOTICE 'Pipeline padrão criado com ID: %', v_pipeline_id;
    END IF;
END;
$$;
*/

-- ============================================================================
-- 3. FORMULÁRIOS DINÂMICOS PADRÃO (Templates)
-- ============================================================================

-- Template de campos para formulário de lead
-- Armazenado como configuração JSON para ser usado como template
INSERT INTO config_plataforma (chave, valor, tipo, descricao)
VALUES (
    'template_formulario_lead',
    '[
        {"id": "nome", "tipo": "text", "label": "Nome Completo", "obrigatorio": true},
        {"id": "email", "tipo": "email", "label": "Email", "obrigatorio": true},
        {"id": "telefone", "tipo": "tel", "label": "Telefone/WhatsApp", "obrigatorio": true},
        {"id": "consumo_medio", "tipo": "number", "label": "Consumo Médio (kWh/mês)", "obrigatorio": true, "min": 0},
        {"id": "valor_conta", "tipo": "currency", "label": "Valor Médio da Conta (R$)", "obrigatorio": false},
        {"id": "tipo_instalacao", "tipo": "select", "label": "Tipo de Instalação", "obrigatorio": true, "opcoes": ["Residencial", "Comercial", "Industrial", "Rural"]},
        {"id": "cidade", "tipo": "text", "label": "Cidade", "obrigatorio": true},
        {"id": "uf", "tipo": "select", "label": "Estado", "obrigatorio": true, "opcoes": ["MT", "MS", "AC", "AM", "AP", "PA", "RO", "RR", "TO"]},
        {"id": "observacoes", "tipo": "textarea", "label": "Observações", "obrigatorio": false}
    ]',
    'JSON',
    'Template de campos para formulário de captura de lead'
)
ON CONFLICT (chave) DO NOTHING;

-- Template de campos para formulário de visita técnica
INSERT INTO config_plataforma (chave, valor, tipo, descricao)
VALUES (
    'template_formulario_visita',
    '[
        {"id": "data_visita", "tipo": "datetime", "label": "Data/Hora da Visita", "obrigatorio": true},
        {"id": "tecnico_responsavel", "tipo": "text", "label": "Técnico Responsável", "obrigatorio": true},
        {"id": "tipo_telhado", "tipo": "select", "label": "Tipo de Telhado", "obrigatorio": true, "opcoes": ["Cerâmico", "Metálico", "Fibrocimento", "Laje", "Solo"]},
        {"id": "orientacao_telhado", "tipo": "select", "label": "Orientação do Telhado", "obrigatorio": true, "opcoes": ["Norte", "Nordeste", "Noroeste", "Sul", "Sudeste", "Sudoeste", "Leste", "Oeste"]},
        {"id": "inclinacao", "tipo": "number", "label": "Inclinação (graus)", "obrigatorio": false, "min": 0, "max": 90},
        {"id": "area_disponivel", "tipo": "number", "label": "Área Disponível (m²)", "obrigatorio": true, "min": 0},
        {"id": "sombreamento", "tipo": "select", "label": "Sombreamento", "obrigatorio": true, "opcoes": ["Nenhum", "Parcial manhã", "Parcial tarde", "Significativo"]},
        {"id": "distancia_quadro", "tipo": "number", "label": "Distância até Quadro (m)", "obrigatorio": false},
        {"id": "padrao_entrada", "tipo": "select", "label": "Padrão de Entrada", "obrigatorio": true, "opcoes": ["Monofásico", "Bifásico", "Trifásico"]},
        {"id": "disjuntor_geral", "tipo": "text", "label": "Disjuntor Geral (A)", "obrigatorio": false},
        {"id": "fotos", "tipo": "file", "label": "Fotos do Local", "obrigatorio": false, "multiplo": true, "aceita": ["image/*"]},
        {"id": "observacoes_tecnicas", "tipo": "textarea", "label": "Observações Técnicas", "obrigatorio": false}
    ]',
    'JSON',
    'Template de campos para formulário de visita técnica'
)
ON CONFLICT (chave) DO NOTHING;

-- Template de campos para formulário de proposta
INSERT INTO config_plataforma (chave, valor, tipo, descricao)
VALUES (
    'template_formulario_proposta',
    '[
        {"id": "potencia_kwp", "tipo": "number", "label": "Potência do Sistema (kWp)", "obrigatorio": true, "min": 0, "step": 0.01},
        {"id": "qtd_modulos", "tipo": "number", "label": "Quantidade de Módulos", "obrigatorio": true, "min": 1},
        {"id": "marca_modulos", "tipo": "text", "label": "Marca dos Módulos", "obrigatorio": true},
        {"id": "modelo_modulos", "tipo": "text", "label": "Modelo dos Módulos", "obrigatorio": true},
        {"id": "potencia_modulo", "tipo": "number", "label": "Potência por Módulo (W)", "obrigatorio": true},
        {"id": "marca_inversor", "tipo": "text", "label": "Marca do Inversor", "obrigatorio": true},
        {"id": "modelo_inversor", "tipo": "text", "label": "Modelo do Inversor", "obrigatorio": true},
        {"id": "qtd_inversores", "tipo": "number", "label": "Quantidade de Inversores", "obrigatorio": true, "min": 1},
        {"id": "producao_estimada", "tipo": "number", "label": "Produção Estimada (kWh/mês)", "obrigatorio": true},
        {"id": "valor_equipamentos", "tipo": "currency", "label": "Valor dos Equipamentos (R$)", "obrigatorio": true},
        {"id": "valor_instalacao", "tipo": "currency", "label": "Valor da Instalação (R$)", "obrigatorio": true},
        {"id": "valor_total", "tipo": "currency", "label": "Valor Total (R$)", "obrigatorio": true},
        {"id": "desconto", "tipo": "currency", "label": "Desconto (R$)", "obrigatorio": false},
        {"id": "valor_final", "tipo": "currency", "label": "Valor Final (R$)", "obrigatorio": true},
        {"id": "prazo_instalacao", "tipo": "number", "label": "Prazo de Instalação (dias)", "obrigatorio": true},
        {"id": "garantia_sistema", "tipo": "number", "label": "Garantia do Sistema (anos)", "obrigatorio": true},
        {"id": "garantia_modulos", "tipo": "number", "label": "Garantia dos Módulos (anos)", "obrigatorio": true},
        {"id": "garantia_inversor", "tipo": "number", "label": "Garantia do Inversor (anos)", "obrigatorio": true},
        {"id": "arquivo_proposta", "tipo": "file", "label": "Arquivo da Proposta (PDF)", "obrigatorio": false, "aceita": [".pdf"]}
    ]',
    'JSON',
    'Template de campos para formulário de proposta comercial'
)
ON CONFLICT (chave) DO NOTHING;

-- ============================================================================
-- 4. DADOS DE EXEMPLO PARA DESENVOLVIMENTO (OPCIONAL)
-- ============================================================================

-- Descomente o bloco abaixo para criar dados de teste

/*
-- Criar usuário admin de teste (senha: admin123)
-- ATENÇÃO: Em produção, criar via Supabase Auth e depois vincular aqui
INSERT INTO usuarios (
    nome_completo,
    cpf,
    email,
    telefone,
    is_superadmin,
    ativo,
    email_verificado
) VALUES (
    'Administrador do Sistema',
    '000.000.000-00',
    'admin@plataformagd.com',
    '(66) 99999-9999',
    TRUE,
    TRUE,
    TRUE
) ON CONFLICT (cpf) DO NOTHING;

-- Adicionar perfil superadmin
INSERT INTO perfis_usuario (usuario_id, perfil, ativo)
SELECT id, 'superadmin', TRUE
FROM usuarios
WHERE cpf = '000.000.000-00'
ON CONFLICT (usuario_id, perfil) DO NOTHING;
*/

-- ============================================================================
-- 5. ÍNDICES ADICIONAIS PARA PERFORMANCE
-- ============================================================================

-- Índices para buscas frequentes no marketplace
CREATE INDEX IF NOT EXISTS idx_produtos_busca
    ON produtos_marketplace USING gin(to_tsvector('portuguese', titulo || ' ' || COALESCE(descricao, '')));

-- Índice para ordenação de faturas por data
CREATE INDEX IF NOT EXISTS idx_faturas_data_ordem
    ON faturas(uc_id, ano_referencia DESC, mes_referencia DESC);

-- Índice para cobranças pendentes
CREATE INDEX IF NOT EXISTS idx_cobrancas_pendentes
    ON cobrancas(status, vencimento)
    WHERE status = 'PENDENTE';

-- Índice para notificações não lidas
CREATE INDEX IF NOT EXISTS idx_notificacoes_nao_lidas
    ON notificacoes(usuario_id, criado_em DESC)
    WHERE lida = FALSE;

-- Índice para projetos ativos por parceiro
CREATE INDEX IF NOT EXISTS idx_projetos_ativos
    ON projetos(parceiro_id, coluna_id)
    WHERE status NOT IN ('CONCLUIDO', 'PERDIDO', 'CANCELADO');

-- ============================================================================
-- FIM DO SEED DATA
-- ============================================================================

-- Verificação final
DO $$
DECLARE
    config_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO config_count FROM config_plataforma;
    RAISE NOTICE 'Seed concluído! Configurações criadas: %', config_count;
END;
$$;

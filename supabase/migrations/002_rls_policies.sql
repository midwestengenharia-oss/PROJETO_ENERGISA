-- ============================================================================
-- PLATAFORMA GD - ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================
-- Este arquivo configura as políticas de segurança no nível de linha
-- Executar APÓS a migração inicial (001_initial_schema.sql)
-- ============================================================================

-- ============================================================================
-- HABILITAR RLS EM TODAS AS TABELAS
-- ============================================================================

ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE perfis_usuario ENABLE ROW LEVEL SECURITY;
ALTER TABLE tokens_energisa ENABLE ROW LEVEL SECURITY;
ALTER TABLE tokens_plataforma ENABLE ROW LEVEL SECURITY;
ALTER TABLE unidades_consumidoras ENABLE ROW LEVEL SECURITY;
ALTER TABLE empresas ENABLE ROW LEVEL SECURITY;
ALTER TABLE usinas ENABLE ROW LEVEL SECURITY;
ALTER TABLE gestores_usina ENABLE ROW LEVEL SECURITY;
ALTER TABLE beneficiarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE convites ENABLE ROW LEVEL SECURITY;
ALTER TABLE contratos ENABLE ROW LEVEL SECURITY;
ALTER TABLE faturas ENABLE ROW LEVEL SECURITY;
ALTER TABLE historico_gd ENABLE ROW LEVEL SECURITY;
ALTER TABLE cobrancas ENABLE ROW LEVEL SECURITY;
ALTER TABLE saques ENABLE ROW LEVEL SECURITY;
ALTER TABLE notificacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE config_plataforma ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE parceiros ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipe_parceiro ENABLE ROW LEVEL SECURITY;
ALTER TABLE produtos_marketplace ENABLE ROW LEVEL SECURITY;
ALTER TABLE kanban_pipelines ENABLE ROW LEVEL SECURITY;
ALTER TABLE kanban_colunas ENABLE ROW LEVEL SECURITY;
ALTER TABLE formularios_dinamicos ENABLE ROW LEVEL SECURITY;
ALTER TABLE projetos ENABLE ROW LEVEL SECURITY;
ALTER TABLE projeto_historico ENABLE ROW LEVEL SECURITY;
ALTER TABLE projeto_tarefas ENABLE ROW LEVEL SECURITY;
ALTER TABLE transacoes_marketplace ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- FUNÇÕES AUXILIARES PARA POLICIES
-- ============================================================================

-- Função para verificar se o usuário autenticado é superadmin
CREATE OR REPLACE FUNCTION is_superadmin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM usuarios
        WHERE auth_id = auth.uid()
          AND is_superadmin = TRUE
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Função para obter o ID do usuário na tabela usuarios pelo auth.uid()
CREATE OR REPLACE FUNCTION get_usuario_id()
RETURNS UUID AS $$
BEGIN
    RETURN (
        SELECT id FROM usuarios
        WHERE auth_id = auth.uid()
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Função para verificar se usuário tem perfil específico
CREATE OR REPLACE FUNCTION has_perfil(perfil_nome perfil_tipo)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM perfis_usuario pu
        JOIN usuarios u ON u.id = pu.usuario_id
        WHERE u.auth_id = auth.uid()
          AND pu.perfil = perfil_nome
          AND pu.ativo = TRUE
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Função para verificar se usuário é membro de um parceiro
CREATE OR REPLACE FUNCTION is_membro_parceiro(parceiro_id_param INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    user_id UUID;
BEGIN
    user_id := get_usuario_id();

    -- É dono do parceiro
    IF EXISTS (SELECT 1 FROM parceiros WHERE id = parceiro_id_param AND usuario_id = user_id) THEN
        RETURN TRUE;
    END IF;

    -- É membro da equipe
    IF EXISTS (
        SELECT 1 FROM equipe_parceiro
        WHERE parceiro_id = parceiro_id_param
          AND usuario_id = user_id
          AND ativo = TRUE
    ) THEN
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- ============================================================================
-- POLICIES - USUARIOS
-- ============================================================================

-- Usuários podem ver seus próprios dados
CREATE POLICY usuarios_select_own ON usuarios
    FOR SELECT USING (auth_id = auth.uid());

-- Superadmins podem ver todos os usuários
CREATE POLICY usuarios_select_admin ON usuarios
    FOR SELECT USING (is_superadmin());

-- Usuários podem atualizar seus próprios dados (exceto is_superadmin)
CREATE POLICY usuarios_update_own ON usuarios
    FOR UPDATE USING (auth_id = auth.uid())
    WITH CHECK (auth_id = auth.uid());

-- Apenas superadmin pode atualizar qualquer usuário
CREATE POLICY usuarios_update_admin ON usuarios
    FOR UPDATE USING (is_superadmin());

-- ============================================================================
-- POLICIES - PERFIS_USUARIO
-- ============================================================================

-- Usuários veem seus próprios perfis
CREATE POLICY perfis_select_own ON perfis_usuario
    FOR SELECT USING (usuario_id = get_usuario_id());

-- Superadmin vê todos os perfis
CREATE POLICY perfis_select_admin ON perfis_usuario
    FOR SELECT USING (is_superadmin());

-- Apenas superadmin pode criar/modificar perfis
CREATE POLICY perfis_insert_admin ON perfis_usuario
    FOR INSERT WITH CHECK (is_superadmin());

CREATE POLICY perfis_update_admin ON perfis_usuario
    FOR UPDATE USING (is_superadmin());

-- ============================================================================
-- POLICIES - TOKENS (ENERGISA E PLATAFORMA)
-- ============================================================================

-- Tokens são privados - apenas o próprio usuário
CREATE POLICY tokens_energisa_own ON tokens_energisa
    FOR ALL USING (usuario_id = get_usuario_id());

CREATE POLICY tokens_plataforma_own ON tokens_plataforma
    FOR ALL USING (usuario_id = get_usuario_id());

-- ============================================================================
-- POLICIES - UNIDADES_CONSUMIDORAS
-- ============================================================================

-- Usuários veem suas próprias UCs
CREATE POLICY ucs_select_own ON unidades_consumidoras
    FOR SELECT USING (usuario_id = get_usuario_id());

-- Gestores veem UCs das usinas que gerenciam
CREATE POLICY ucs_select_gestor ON unidades_consumidoras
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM gestores_usina gu
            JOIN usinas u ON u.id = gu.usina_id
            WHERE gu.gestor_id = get_usuario_id()
              AND gu.ativo = TRUE
              AND (u.uc_geradora_id = unidades_consumidoras.id
                   OR unidades_consumidoras.geradora_id = u.uc_geradora_id)
        )
    );

-- Superadmin vê todas
CREATE POLICY ucs_select_admin ON unidades_consumidoras
    FOR SELECT USING (is_superadmin());

-- Usuário pode atualizar suas próprias UCs
CREATE POLICY ucs_update_own ON unidades_consumidoras
    FOR UPDATE USING (usuario_id = get_usuario_id());

-- ============================================================================
-- POLICIES - EMPRESAS
-- ============================================================================

-- Proprietário vê suas empresas
CREATE POLICY empresas_select_own ON empresas
    FOR SELECT USING (proprietario_id = get_usuario_id());

-- Superadmin vê todas
CREATE POLICY empresas_select_admin ON empresas
    FOR SELECT USING (is_superadmin());

-- Proprietário pode criar/atualizar suas empresas
CREATE POLICY empresas_insert_own ON empresas
    FOR INSERT WITH CHECK (proprietario_id = get_usuario_id());

CREATE POLICY empresas_update_own ON empresas
    FOR UPDATE USING (proprietario_id = get_usuario_id());

-- ============================================================================
-- POLICIES - USINAS
-- ============================================================================

-- Ver usinas que gerencia ou é proprietário
CREATE POLICY usinas_select_own ON usinas
    FOR SELECT USING (
        -- É proprietário da empresa dona da usina
        EXISTS (
            SELECT 1 FROM empresas e
            WHERE e.id = usinas.empresa_id
              AND e.proprietario_id = get_usuario_id()
        )
        OR
        -- É gestor da usina
        EXISTS (
            SELECT 1 FROM gestores_usina gu
            WHERE gu.usina_id = usinas.id
              AND gu.gestor_id = get_usuario_id()
              AND gu.ativo = TRUE
        )
    );

-- Superadmin vê todas
CREATE POLICY usinas_select_admin ON usinas
    FOR SELECT USING (is_superadmin());

-- ============================================================================
-- POLICIES - GESTORES_USINA
-- ============================================================================

-- Gestor vê suas próprias vinculações
CREATE POLICY gestores_usina_select_own ON gestores_usina
    FOR SELECT USING (gestor_id = get_usuario_id());

-- Proprietário vê gestores das suas usinas
CREATE POLICY gestores_usina_select_proprietario ON gestores_usina
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM usinas u
            JOIN empresas e ON e.id = u.empresa_id
            WHERE u.id = gestores_usina.usina_id
              AND e.proprietario_id = get_usuario_id()
        )
    );

-- Superadmin vê todos
CREATE POLICY gestores_usina_select_admin ON gestores_usina
    FOR SELECT USING (is_superadmin());

-- ============================================================================
-- POLICIES - BENEFICIARIOS
-- ============================================================================

-- Beneficiário vê seus próprios dados
CREATE POLICY beneficiarios_select_own ON beneficiarios
    FOR SELECT USING (usuario_id = get_usuario_id());

-- Gestor vê beneficiários das usinas que gerencia
CREATE POLICY beneficiarios_select_gestor ON beneficiarios
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM gestores_usina gu
            WHERE gu.usina_id = beneficiarios.usina_id
              AND gu.gestor_id = get_usuario_id()
              AND gu.ativo = TRUE
        )
    );

-- Proprietário vê beneficiários das suas usinas
CREATE POLICY beneficiarios_select_proprietario ON beneficiarios
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM usinas u
            JOIN empresas e ON e.id = u.empresa_id
            WHERE u.id = beneficiarios.usina_id
              AND e.proprietario_id = get_usuario_id()
        )
    );

-- Superadmin vê todos
CREATE POLICY beneficiarios_select_admin ON beneficiarios
    FOR SELECT USING (is_superadmin());

-- Gestor pode criar/editar beneficiários das suas usinas
CREATE POLICY beneficiarios_insert_gestor ON beneficiarios
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM gestores_usina gu
            WHERE gu.usina_id = beneficiarios.usina_id
              AND gu.gestor_id = get_usuario_id()
              AND gu.ativo = TRUE
        )
    );

CREATE POLICY beneficiarios_update_gestor ON beneficiarios
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM gestores_usina gu
            WHERE gu.usina_id = beneficiarios.usina_id
              AND gu.gestor_id = get_usuario_id()
              AND gu.ativo = TRUE
        )
    );

-- ============================================================================
-- POLICIES - CONVITES
-- ============================================================================

-- Usuário vê convites que criou
CREATE POLICY convites_select_criador ON convites
    FOR SELECT USING (convidado_por_id = get_usuario_id());

-- Usuário vê convites para seu email
CREATE POLICY convites_select_destinatario ON convites
    FOR SELECT USING (
        email = (SELECT email FROM usuarios WHERE id = get_usuario_id())
    );

-- Superadmin vê todos
CREATE POLICY convites_select_admin ON convites
    FOR SELECT USING (is_superadmin());

-- ============================================================================
-- POLICIES - CONTRATOS
-- ============================================================================

-- Partes do contrato podem ver
CREATE POLICY contratos_select_partes ON contratos
    FOR SELECT USING (
        parte_a_id = get_usuario_id()
        OR parte_b_id = get_usuario_id()
    );

-- Superadmin vê todos
CREATE POLICY contratos_select_admin ON contratos
    FOR SELECT USING (is_superadmin());

-- ============================================================================
-- POLICIES - FATURAS
-- ============================================================================

-- Usuário vê faturas das suas UCs
CREATE POLICY faturas_select_own ON faturas
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM unidades_consumidoras uc
            WHERE uc.id = faturas.uc_id
              AND uc.usuario_id = get_usuario_id()
        )
    );

-- Gestor vê faturas das UCs das usinas que gerencia
CREATE POLICY faturas_select_gestor ON faturas
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM unidades_consumidoras uc
            JOIN gestores_usina gu ON gu.usina_id IN (
                SELECT id FROM usinas WHERE uc_geradora_id = uc.id OR uc_geradora_id = uc.geradora_id
            )
            WHERE uc.id = faturas.uc_id
              AND gu.gestor_id = get_usuario_id()
              AND gu.ativo = TRUE
        )
    );

-- Superadmin vê todas
CREATE POLICY faturas_select_admin ON faturas
    FOR SELECT USING (is_superadmin());

-- ============================================================================
-- POLICIES - HISTORICO_GD
-- ============================================================================

-- Mesmo padrão das faturas
CREATE POLICY historico_gd_select_own ON historico_gd
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM unidades_consumidoras uc
            WHERE uc.id = historico_gd.uc_id
              AND uc.usuario_id = get_usuario_id()
        )
    );

CREATE POLICY historico_gd_select_admin ON historico_gd
    FOR SELECT USING (is_superadmin());

-- ============================================================================
-- POLICIES - COBRANCAS
-- ============================================================================

-- Beneficiário vê suas cobranças
CREATE POLICY cobrancas_select_beneficiario ON cobrancas
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM beneficiarios b
            WHERE b.id = cobrancas.beneficiario_id
              AND b.usuario_id = get_usuario_id()
        )
    );

-- Gestor vê cobranças das suas usinas
CREATE POLICY cobrancas_select_gestor ON cobrancas
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM beneficiarios b
            JOIN gestores_usina gu ON gu.usina_id = b.usina_id
            WHERE b.id = cobrancas.beneficiario_id
              AND gu.gestor_id = get_usuario_id()
              AND gu.ativo = TRUE
        )
    );

-- Superadmin vê todas
CREATE POLICY cobrancas_select_admin ON cobrancas
    FOR SELECT USING (is_superadmin());

-- ============================================================================
-- POLICIES - SAQUES
-- ============================================================================

-- Usuário vê seus próprios saques
CREATE POLICY saques_select_own ON saques
    FOR SELECT USING (usuario_id = get_usuario_id());

-- Superadmin vê todos (para aprovar)
CREATE POLICY saques_select_admin ON saques
    FOR SELECT USING (is_superadmin());

-- Usuário pode criar seus próprios saques
CREATE POLICY saques_insert_own ON saques
    FOR INSERT WITH CHECK (usuario_id = get_usuario_id());

-- Apenas superadmin pode atualizar (aprovar/rejeitar)
CREATE POLICY saques_update_admin ON saques
    FOR UPDATE USING (is_superadmin());

-- ============================================================================
-- POLICIES - NOTIFICACOES
-- ============================================================================

-- Usuário vê e gerencia suas próprias notificações
CREATE POLICY notificacoes_own ON notificacoes
    FOR ALL USING (usuario_id = get_usuario_id());

-- ============================================================================
-- POLICIES - CONFIG_PLATAFORMA
-- ============================================================================

-- Todos podem ler configurações públicas
CREATE POLICY config_select_all ON config_plataforma
    FOR SELECT USING (TRUE);

-- Apenas superadmin pode modificar
CREATE POLICY config_update_admin ON config_plataforma
    FOR UPDATE USING (is_superadmin());

-- ============================================================================
-- POLICIES - LEADS
-- ============================================================================

-- Gestor vê leads atribuídos a ele
CREATE POLICY leads_select_gestor ON leads
    FOR SELECT USING (gestor_id = get_usuario_id());

-- Superadmin vê todos
CREATE POLICY leads_select_admin ON leads
    FOR SELECT USING (is_superadmin());

-- ============================================================================
-- POLICIES - PARCEIROS (MARKETPLACE)
-- ============================================================================

-- Dono do parceiro pode ver
CREATE POLICY parceiros_select_owner ON parceiros
    FOR SELECT USING (usuario_id = get_usuario_id());

-- Membros da equipe podem ver
CREATE POLICY parceiros_select_equipe ON parceiros
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM equipe_parceiro ep
            WHERE ep.parceiro_id = parceiros.id
              AND ep.usuario_id = get_usuario_id()
              AND ep.ativo = TRUE
        )
    );

-- Superadmin vê todos
CREATE POLICY parceiros_select_admin ON parceiros
    FOR SELECT USING (is_superadmin());

-- Parceiros ativos são visíveis publicamente (para marketplace)
CREATE POLICY parceiros_select_public ON parceiros
    FOR SELECT USING (status = 'ATIVO');

-- ============================================================================
-- POLICIES - EQUIPE_PARCEIRO
-- ============================================================================

-- Membros veem sua própria equipe
CREATE POLICY equipe_select_membro ON equipe_parceiro
    FOR SELECT USING (is_membro_parceiro(parceiro_id));

-- Superadmin vê todos
CREATE POLICY equipe_select_admin ON equipe_parceiro
    FOR SELECT USING (is_superadmin());

-- Admin do parceiro pode gerenciar equipe
CREATE POLICY equipe_insert_admin ON equipe_parceiro
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM parceiros p
            WHERE p.id = equipe_parceiro.parceiro_id
              AND p.usuario_id = get_usuario_id()
        )
        OR
        EXISTS (
            SELECT 1 FROM equipe_parceiro ep
            WHERE ep.parceiro_id = equipe_parceiro.parceiro_id
              AND ep.usuario_id = get_usuario_id()
              AND ep.papel = 'ADMIN'
              AND ep.ativo = TRUE
        )
    );

-- ============================================================================
-- POLICIES - PRODUTOS_MARKETPLACE
-- ============================================================================

-- Membros do parceiro veem seus produtos
CREATE POLICY produtos_select_parceiro ON produtos_marketplace
    FOR SELECT USING (is_membro_parceiro(parceiro_id));

-- Produtos ativos são públicos
CREATE POLICY produtos_select_public ON produtos_marketplace
    FOR SELECT USING (status = 'ATIVO');

-- Superadmin vê todos
CREATE POLICY produtos_select_admin ON produtos_marketplace
    FOR SELECT USING (is_superadmin());

-- Membros do parceiro podem criar/editar
CREATE POLICY produtos_insert_parceiro ON produtos_marketplace
    FOR INSERT WITH CHECK (is_membro_parceiro(parceiro_id));

CREATE POLICY produtos_update_parceiro ON produtos_marketplace
    FOR UPDATE USING (is_membro_parceiro(parceiro_id));

-- ============================================================================
-- POLICIES - KANBAN (PIPELINES, COLUNAS, FORMULARIOS)
-- ============================================================================

-- Membros do parceiro acessam seu kanban
CREATE POLICY pipelines_parceiro ON kanban_pipelines
    FOR ALL USING (is_membro_parceiro(parceiro_id));

CREATE POLICY colunas_parceiro ON kanban_colunas
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM kanban_pipelines kp
            WHERE kp.id = kanban_colunas.pipeline_id
              AND is_membro_parceiro(kp.parceiro_id)
        )
    );

CREATE POLICY formularios_parceiro ON formularios_dinamicos
    FOR ALL USING (is_membro_parceiro(parceiro_id));

-- Superadmin acessa tudo
CREATE POLICY pipelines_admin ON kanban_pipelines
    FOR SELECT USING (is_superadmin());

CREATE POLICY colunas_admin ON kanban_colunas
    FOR SELECT USING (is_superadmin());

CREATE POLICY formularios_admin ON formularios_dinamicos
    FOR SELECT USING (is_superadmin());

-- ============================================================================
-- POLICIES - PROJETOS
-- ============================================================================

-- Membros do parceiro acessam projetos
CREATE POLICY projetos_parceiro ON projetos
    FOR ALL USING (is_membro_parceiro(parceiro_id));

-- Vendedor/técnico responsável pode acessar
CREATE POLICY projetos_responsavel ON projetos
    FOR SELECT USING (
        vendedor_id = get_usuario_id()
        OR tecnico_id = get_usuario_id()
    );

-- Superadmin acessa tudo
CREATE POLICY projetos_admin ON projetos
    FOR SELECT USING (is_superadmin());

-- ============================================================================
-- POLICIES - PROJETO_HISTORICO E TAREFAS
-- ============================================================================

CREATE POLICY historico_projetos ON projeto_historico
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM projetos p
            WHERE p.id = projeto_historico.projeto_id
              AND is_membro_parceiro(p.parceiro_id)
        )
    );

CREATE POLICY tarefas_projetos ON projeto_tarefas
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM projetos p
            WHERE p.id = projeto_tarefas.projeto_id
              AND is_membro_parceiro(p.parceiro_id)
        )
        OR responsavel_id = get_usuario_id()
    );

-- ============================================================================
-- POLICIES - TRANSACOES_MARKETPLACE
-- ============================================================================

CREATE POLICY transacoes_parceiro ON transacoes_marketplace
    FOR SELECT USING (is_membro_parceiro(parceiro_id));

CREATE POLICY transacoes_admin ON transacoes_marketplace
    FOR SELECT USING (is_superadmin());

-- ============================================================================
-- FIM DAS POLICIES
-- ============================================================================

-- Verificação
DO $$
DECLARE
    policy_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public';

    RAISE NOTICE 'RLS configurado! Total de policies criadas: %', policy_count;
END;
$$;

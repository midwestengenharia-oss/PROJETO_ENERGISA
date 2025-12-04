-- ============================================================================
-- FIX: Permitir INSERT publico na tabela leads (landing page)
-- Execute no Supabase SQL Editor
-- ============================================================================

-- Permitir INSERT anonimo na tabela leads (para landing page capturar leads)
CREATE POLICY "Permitir INSERT publico em leads"
    ON leads
    FOR INSERT
    TO anon, authenticated
    WITH CHECK (true);

-- Permitir SELECT anonimo para verificar se CPF ja existe
CREATE POLICY "Permitir SELECT publico em leads por CPF"
    ON leads
    FOR SELECT
    TO anon
    USING (true);

-- Permitir UPDATE anonimo (para atualizar lead existente na landing page)
CREATE POLICY "Permitir UPDATE publico em leads"
    ON leads
    FOR UPDATE
    TO anon
    USING (true)
    WITH CHECK (true);

-- Tambem precisamos permitir INSERT na tabela simulacoes (endpoint publico)
ALTER TABLE simulacoes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Permitir INSERT publico em simulacoes"
    ON simulacoes
    FOR INSERT
    TO anon, authenticated
    WITH CHECK (true);

CREATE POLICY "Permitir SELECT publico em simulacoes"
    ON simulacoes
    FOR SELECT
    TO anon, authenticated
    USING (true);

-- Tambem precisamos permitir INSERT na tabela contatos (endpoint autenticado)
ALTER TABLE contatos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Permitir INSERT autenticado em contatos"
    ON contatos
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

CREATE POLICY "Permitir SELECT autenticado em contatos"
    ON contatos
    FOR SELECT
    TO authenticated
    USING (true);

-- ============================================================================
-- IMPORTANTE: Execute este SQL no Supabase SQL Editor
-- ============================================================================

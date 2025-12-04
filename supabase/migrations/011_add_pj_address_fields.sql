-- Migration: Adicionar campos de endereço e dados empresariais para PJ
-- Data: 2024-12-04

-- Campos de Endereço
ALTER TABLE usuarios
ADD COLUMN IF NOT EXISTS logradouro VARCHAR(255),
ADD COLUMN IF NOT EXISTS numero VARCHAR(20),
ADD COLUMN IF NOT EXISTS complemento VARCHAR(100),
ADD COLUMN IF NOT EXISTS bairro VARCHAR(100),
ADD COLUMN IF NOT EXISTS cidade VARCHAR(100),
ADD COLUMN IF NOT EXISTS uf VARCHAR(2),
ADD COLUMN IF NOT EXISTS cep VARCHAR(10);

-- Campos de Dados Empresariais (para PJ)
ALTER TABLE usuarios
ADD COLUMN IF NOT EXISTS porte VARCHAR(50),
ADD COLUMN IF NOT EXISTS natureza_juridica VARCHAR(100),
ADD COLUMN IF NOT EXISTS cnae_codigo INTEGER,
ADD COLUMN IF NOT EXISTS cnae_descricao VARCHAR(255),
ADD COLUMN IF NOT EXISTS situacao_cadastral VARCHAR(50),
ADD COLUMN IF NOT EXISTS data_abertura DATE;

-- Criar índice para buscas por cidade/UF
CREATE INDEX IF NOT EXISTS idx_usuarios_cidade_uf ON usuarios(cidade, uf);

-- Comentários explicativos
COMMENT ON COLUMN usuarios.logradouro IS 'Rua/Avenida do endereço';
COMMENT ON COLUMN usuarios.numero IS 'Número do endereço';
COMMENT ON COLUMN usuarios.complemento IS 'Complemento do endereço';
COMMENT ON COLUMN usuarios.bairro IS 'Bairro';
COMMENT ON COLUMN usuarios.cidade IS 'Cidade/Município';
COMMENT ON COLUMN usuarios.uf IS 'Unidade Federativa (sigla)';
COMMENT ON COLUMN usuarios.cep IS 'CEP formatado';
COMMENT ON COLUMN usuarios.porte IS 'Porte da empresa (MEI, ME, EPP, etc)';
COMMENT ON COLUMN usuarios.natureza_juridica IS 'Natureza jurídica da empresa';
COMMENT ON COLUMN usuarios.cnae_codigo IS 'Código CNAE principal';
COMMENT ON COLUMN usuarios.cnae_descricao IS 'Descrição da atividade econômica';
COMMENT ON COLUMN usuarios.situacao_cadastral IS 'Situação cadastral na Receita (ATIVA, BAIXADA, etc)';
COMMENT ON COLUMN usuarios.data_abertura IS 'Data de abertura/início das atividades';

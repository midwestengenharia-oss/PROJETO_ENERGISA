-- Migration: Adicionar campo apelido na tabela unidades_consumidoras
-- Permite que o usuário dê um nome personalizado para cada UC (ex: "Casa do Pai", "Cunhado")

ALTER TABLE unidades_consumidoras
ADD COLUMN IF NOT EXISTS apelido VARCHAR(100);

COMMENT ON COLUMN unidades_consumidoras.apelido IS 'Apelido/nome personalizado da UC definido pelo usuário';

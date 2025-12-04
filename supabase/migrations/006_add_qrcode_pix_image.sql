-- Migration: Adicionar campo qr_code_pix_image na tabela faturas
-- Este campo armazena a imagem base64 do QR Code PIX para pagamento

ALTER TABLE faturas
ADD COLUMN IF NOT EXISTS qr_code_pix_image TEXT;

COMMENT ON COLUMN faturas.qr_code_pix_image IS 'Imagem Base64 do QR Code PIX para pagamento (qrCodePixImage64 da API Energisa)';

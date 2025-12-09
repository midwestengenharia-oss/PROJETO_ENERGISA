"""
Extrator de Texto de PDFs de Faturas

Extrai texto de PDFs de faturas da Energisa usando pdfplumber.
Suporta PDFs nativos e escaneados (com OCR fallback).
"""

import base64
import io
import re
from typing import Optional
import pdfplumber
from PIL import Image
import pytesseract


class FaturaPDFExtractor:
    """Extrator de texto de PDFs de faturas"""

    def __init__(self):
        self.tesseract_available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Verifica se pytesseract está disponível"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def extrair_texto_pdf(self, pdf_base64: str) -> str:
        """
        Extrai texto de um PDF em base64.

        Args:
            pdf_base64: String base64 do PDF

        Returns:
            Texto extraído do PDF (cru)

        Raises:
            ValueError: Se o PDF estiver vazio ou inválido
        """
        if not pdf_base64:
            raise ValueError("PDF base64 vazio")

        try:
            # Decode base64 para bytes
            pdf_bytes = base64.b64decode(pdf_base64)

            # Tentar extração direta com pdfplumber (PDFs nativos)
            texto = self._extrair_com_pdfplumber(pdf_bytes)

            # Se não conseguiu extrair texto suficiente, tentar OCR
            if len(texto.strip()) < 100 and self.tesseract_available:
                texto_ocr = self._extrair_com_ocr(pdf_bytes)
                if len(texto_ocr) > len(texto):
                    texto = texto_ocr

            if not texto or len(texto.strip()) < 50:
                raise ValueError("Não foi possível extrair texto suficiente do PDF")

            # Pré-processar texto
            texto_limpo = self.preprocessar_texto(texto)

            return texto_limpo

        except Exception as e:
            raise ValueError(f"Erro ao extrair texto do PDF: {str(e)}")

    def _extrair_com_pdfplumber(self, pdf_bytes: bytes) -> str:
        """
        Extrai texto usando pdfplumber (PDFs nativos).

        Args:
            pdf_bytes: Bytes do PDF

        Returns:
            Texto extraído
        """
        texto_completo = []

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for pagina in pdf.pages:
                # Extrair texto preservando layout
                texto_pagina = pagina.extract_text(layout=True)
                if texto_pagina:
                    texto_completo.append(texto_pagina)

                # Também tentar extrair tabelas (faturas têm muitas tabelas)
                tabelas = pagina.extract_tables()
                for tabela in tabelas:
                    # Converter tabela em texto formatado
                    texto_tabela = self._tabela_para_texto(tabela)
                    texto_completo.append(texto_tabela)

        return "\n\n".join(texto_completo)

    def _extrair_com_ocr(self, pdf_bytes: bytes) -> str:
        """
        Extrai texto usando OCR (PDFs escaneados).

        Args:
            pdf_bytes: Bytes do PDF

        Returns:
            Texto extraído via OCR
        """
        if not self.tesseract_available:
            return ""

        texto_completo = []

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for pagina in pdf.pages:
                    # Converter página em imagem
                    img = pagina.to_image(resolution=300)

                    # Aplicar OCR
                    texto_pagina = pytesseract.image_to_string(
                        img.original,
                        lang='por',  # Português
                        config='--psm 6'  # Assume um bloco uniforme de texto
                    )

                    if texto_pagina:
                        texto_completo.append(texto_pagina)

        except Exception as e:
            print(f"Erro no OCR: {e}")
            return ""

        return "\n\n".join(texto_completo)

    def _tabela_para_texto(self, tabela: list) -> str:
        """
        Converte uma tabela extraída em texto formatado.

        Args:
            tabela: Lista de listas representando a tabela

        Returns:
            Texto formatado da tabela
        """
        if not tabela:
            return ""

        linhas_texto = []
        for linha in tabela:
            if linha:
                # Juntar células com pipe
                linha_texto = " | ".join([str(cel or "").strip() for cel in linha])
                if linha_texto.strip():
                    linhas_texto.append(linha_texto)

        return "\n".join(linhas_texto)

    def preprocessar_texto(self, texto_cru: str) -> str:
        """
        Limpa e normaliza o texto extraído.

        Args:
            texto_cru: Texto bruto extraído do PDF

        Returns:
            Texto limpo e normalizado
        """
        if not texto_cru:
            return ""

        # 1. Normalizar quebras de linha múltiplas
        texto = re.sub(r'\n{3,}', '\n\n', texto_cru)

        # 2. Remover espaços em branco excessivos (mas preservar tabs de tabelas)
        linhas = []
        for linha in texto.split('\n'):
            # Remover espaços no início/fim
            linha_limpa = linha.strip()
            if linha_limpa:
                # Normalizar espaços múltiplos (exceto em números formatados)
                linha_limpa = re.sub(r'  +', ' ', linha_limpa)
                linhas.append(linha_limpa)

        texto = '\n'.join(linhas)

        # 3. Normalizar separadores decimais
        # Manter vírgulas e pontos como estão - o parser decidirá

        # 4. Remover caracteres especiais problemáticos
        texto = texto.replace('\x00', '')  # Null bytes
        texto = texto.replace('\ufffd', '')  # Replacement character

        # 5. Normalizar encoding
        texto = texto.encode('utf-8', errors='ignore').decode('utf-8')

        return texto

    def extrair_secao(self, texto: str, inicio_pattern: str, fim_pattern: Optional[str] = None) -> str:
        """
        Extrai uma seção específica do texto.

        Args:
            texto: Texto completo
            inicio_pattern: Regex para identificar início da seção
            fim_pattern: Regex para identificar fim da seção (opcional)

        Returns:
            Texto da seção extraída
        """
        match_inicio = re.search(inicio_pattern, texto, re.IGNORECASE | re.MULTILINE)
        if not match_inicio:
            return ""

        inicio_idx = match_inicio.end()

        if fim_pattern:
            match_fim = re.search(fim_pattern, texto[inicio_idx:], re.IGNORECASE | re.MULTILINE)
            if match_fim:
                fim_idx = inicio_idx + match_fim.start()
                return texto[inicio_idx:fim_idx].strip()

        # Se não tem fim definido, pegar até próximo cabeçalho ou final
        return texto[inicio_idx:].strip()

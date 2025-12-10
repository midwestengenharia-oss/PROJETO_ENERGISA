"""
Parser Python Puro para Faturas da Energisa

Extrai dados estruturados do texto de faturas usando regex e parsing de texto.
NÃO usa IA - apenas Python puro.
"""

import re
from typing import Optional, List, Tuple
from decimal import Decimal
from datetime import datetime, date
from .extraction_schemas import (
    FaturaExtraidaSchema,
    ConsumoKwhExtracted,
    EnergiaInjetadaItemExtracted,
    AjusteLei14300Extracted,
    LancamentoServicoExtracted,
    ItensFaturaExtracted,
    TotaisExtracted,
    QuadroAtencaoExtracted,
    DadosInstalacaoExtracted,
    MediaConsumo13MExtracted,
    ConsumoMesExtracted
)


class FaturaPythonParser:
    """Parser de faturas da Energisa usando Python puro"""

    # Mapeamento de meses em português
    MESES_PT = {
        'janeiro': 1, 'jan': 1,
        'fevereiro': 2, 'fev': 2,
        'março': 3, 'mar': 3, 'marco': 3,
        'abril': 4, 'abr': 4,
        'maio': 5, 'mai': 5,
        'junho': 6, 'jun': 6,
        'julho': 7, 'jul': 7,
        'agosto': 8, 'ago': 8,
        'setembro': 9, 'set': 9,
        'outubro': 10, 'out': 10,
        'novembro': 11, 'nov': 11,
        'dezembro': 12, 'dez': 12
    }

    def parse(self, texto: str) -> FaturaExtraidaSchema:
        """
        Faz o parsing completo do texto da fatura.

        Args:
            texto: Texto extraído do PDF

        Returns:
            Dados estruturados da fatura
        """
        # Normalizar texto (manter original para algumas extrações)
        texto_upper = texto.upper()
        texto_original = texto

        # Extrair cada seção
        codigo_cliente = self._extrair_codigo_cliente(texto_upper)
        ligacao = self._extrair_tipo_ligacao(texto_upper)
        data_apresentacao = self._extrair_data_apresentacao(texto_upper)
        mes_ano_ref = self._extrair_mes_ano_referencia(texto_upper)
        vencimento = self._extrair_vencimento(texto_upper)
        total_pagar = self._extrair_total_pagar(texto_upper)

        # Datas de leitura
        leitura_ant_data = self._extrair_leitura_anterior_data(texto_upper)
        leitura_atual_data = self._extrair_leitura_atual_data(texto_upper)
        dias = self._extrair_dias(texto_upper, leitura_ant_data, leitura_atual_data)
        proxima_leitura = self._extrair_proxima_leitura(texto_upper)

        # Leituras do medidor
        leitura_ant = self._extrair_leitura_anterior(texto_upper)
        leitura_atual = self._extrair_leitura_atual(texto_upper)

        # Itens da fatura
        itens = self._extrair_itens_fatura(texto_upper)

        # Totais
        totais = self._extrair_totais(texto_upper, itens)

        # Quadro de atenção (GD)
        quadro_atencao = self._extrair_quadro_atencao(texto_upper)

        # Bandeira
        bandeira = self._extrair_bandeira(texto_upper)

        # Dados da instalação
        dados_instalacao = self._extrair_dados_instalacao(texto_upper, texto_original)

        # Histórico de consumo (13 meses)
        media_consumo = self._extrair_media_consumo_13m(texto_upper)

        # Calcular consumo total
        consumo_total = self._calcular_consumo_total(leitura_ant, leitura_atual, itens)

        # Calcular energia injetada/compensada total
        energia_injetada_total = self._calcular_energia_injetada_total(itens)
        energia_compensada_total = self._calcular_energia_compensada_total(itens, texto_upper)

        return FaturaExtraidaSchema(
            codigo_cliente=codigo_cliente,
            ligacao=ligacao,
            data_apresentacao=data_apresentacao,
            mes_ano_referencia=mes_ano_ref,
            vencimento=vencimento,
            total_a_pagar=total_pagar,
            leitura_anterior_data=leitura_ant_data,
            leitura_atual_data=leitura_atual_data,
            dias=dias,
            proxima_leitura_data=proxima_leitura,
            leitura_anterior=leitura_ant,
            leitura_atual=leitura_atual,
            itens_fatura=itens,
            totais=totais,
            quadro_atencao=quadro_atencao,
            bandeira_tarifaria=bandeira,
            dados_instalacao=dados_instalacao,
            media_consumo_13m=media_consumo,
            consumo_total_kwh=consumo_total,
            energia_injetada_total_kwh=energia_injetada_total,
            energia_compensada_total_kwh=energia_compensada_total
        )

    def _extrair_codigo_cliente(self, texto: str) -> Optional[str]:
        """Extrai código do cliente (formato 6/XXXXXXXX-X)"""
        patterns = [
            r'(?:C[ÓO]DIGO\s+(?:DO\s+)?CLIENTE|CLIENTE)[:\s]+(\d/\d{7,8}-\d)',
            r'(\d/\d{7,8}-\d)',  # Padrão direto
        ]

        for pattern in patterns:
            match = re.search(pattern, texto)
            if match:
                return match.group(1).replace(' ', '')

        return None

    def _extrair_tipo_ligacao(self, texto: str) -> Optional[str]:
        """Extrai tipo de ligação"""
        patterns = [
            r'(?:LIGA[ÇC][ÃA]O|TIPO\s+DE\s+LIGA[ÇC][ÃA]O)[:\s]+(MONOF[ÁA]SIC[OA]|BIF[ÁA]SIC[OA]|TRIF[ÁA]SIC[OA])',
            r'\b(MONOF[ÁA]SIC[OA]|BIF[ÁA]SIC[OA]|TRIF[ÁA]SIC[OA])\b'
        ]

        for pattern in patterns:
            match = re.search(pattern, texto)
            if match:
                tipo = match.group(1)
                # Normalizar
                if 'MONO' in tipo:
                    return "MONOFASICO"
                elif 'BIF' in tipo:
                    return "BIFASICO"
                elif 'TRIF' in tipo:
                    return "TRIFASICO"

        return None

    def _extrair_data_apresentacao(self, texto: str) -> Optional[date]:
        """Extrai data de apresentação"""
        patterns = [
            r'(?:DATA\s+DE\s+)?APRESENTA[ÇC][ÃA]O[:\s]+(\d{2}[/\-]\d{2}[/\-]\d{4})',
            r'EMISS[ÃA]O[:\s]+(\d{2}[/\-]\d{2}[/\-]\d{4})'
        ]

        for pattern in patterns:
            match = re.search(pattern, texto)
            if match:
                return self._parse_data_br(match.group(1))

        return None

    def _extrair_mes_ano_referencia(self, texto: str) -> Optional[str]:
        """Extrai mês/ano de referência (retorna YYYY-MM)"""
        # Padrões específicos primeiro
        patterns = [
            # REFERÊNCIA: DEZEMBRO/2025
            r'REFER[ÊE]NCIA[:\s]+([A-Z]+)\s*[/\-]\s*(\d{4})',
            # MÊS DE REFERÊNCIA: DEZ/2025
            r'M[ÊE]S\s+(?:DE\s+)?REFER[ÊE]NCIA[:\s]+([A-Z]+)[/\s\-]+(\d{2,4})',
            # CONTA DE ENERGIA - DEZEMBRO 2025
            r'CONTA\s+DE\s+ENERGIA[:\s\-]+([A-Z]+)\s+(\d{4})',
            # FATURA DE DEZEMBRO/2025
            r'FATURA\s+(?:DE\s+)?([A-Z]+)\s*[/\-]\s*(\d{4})',
            # DEZEMBRO/2025 ou DEZ/25 (mais genérico)
            r'\b([A-Z]{3,10})\s*[/\-]\s*(\d{2,4})\b',
            # 12/2025
            r'\b(\d{2})/(\d{4})\b',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, texto):
                mes_str = match.group(1)
                ano_str = match.group(2)

                # Converter mês
                if mes_str.isdigit():
                    mes_num = int(mes_str)
                    if not (1 <= mes_num <= 12):
                        continue
                else:
                    mes_nome = mes_str.lower()
                    mes_num = None
                    for nome, num in self.MESES_PT.items():
                        if nome in mes_nome or mes_nome in nome:
                            mes_num = num
                            break
                    if not mes_num:
                        continue

                # Normalizar ano (se vier 25, converter para 2025)
                ano = int(ano_str)
                if ano < 100:
                    ano = 2000 + ano

                # Validar ano razoável
                if 2020 <= ano <= 2030:
                    return f"{ano:04d}-{mes_num:02d}"

        return None

    def _extrair_vencimento(self, texto: str) -> Optional[date]:
        """Extrai data de vencimento"""
        patterns = [
            r'VENCIMENTO[:\s]+(\d{2}[/\-]\d{2}[/\-]\d{4})',
            r'VENC[:\s]+(\d{2}[/\-]\d{2}[/\-]\d{4})'
        ]

        for pattern in patterns:
            match = re.search(pattern, texto)
            if match:
                return self._parse_data_br(match.group(1))

        return None

    def _extrair_total_pagar(self, texto: str) -> Optional[Decimal]:
        """Extrai total a pagar"""
        patterns = [
            r'TOTAL\s+A\s+PAGAR[:\s]+R?\$?\s*([\d.,]+)',
            r'VALOR\s+(?:COBRADO|DO\s+DOCUMENTO)[:\s]+R?\$?\s*([\d.,]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, texto)
            if match:
                return self._parse_decimal_br(match.group(1))

        return None

    def _extrair_leitura_anterior_data(self, texto: str) -> Optional[date]:
        """Extrai data da leitura anterior"""
        pattern = r'LEITURA\s+ANTERIOR[:\s]+(\d{2}[/\-]\d{2}[/\-]\d{4})'
        match = re.search(pattern, texto)
        if match:
            return self._parse_data_br(match.group(1))
        return None

    def _extrair_leitura_atual_data(self, texto: str) -> Optional[date]:
        """Extrai data da leitura atual"""
        pattern = r'LEITURA\s+ATUAL[:\s]+(\d{2}[/\-]\d{2}[/\-]\d{4})'
        match = re.search(pattern, texto)
        if match:
            return self._parse_data_br(match.group(1))
        return None

    def _extrair_dias(self, texto: str, leitura_ant_data: Optional[date] = None, leitura_atual_data: Optional[date] = None) -> Optional[int]:
        """Extrai quantidade de dias do ciclo de faturamento"""
        # Padrões mais específicos para evitar capturar ano como dias
        patterns = [
            r'(?:QUANTIDADE\s+DE\s+)?DIAS\s*(?:DO\s+CICLO)?[:\s]+(\d{1,3})\b',
            r'\b(\d{1,2})\s+DIAS?\s+(?:DE\s+)?(?:CONSUMO|FATURAMENTO)',
            r'PER[IÍ]ODO\s+DE\s+(\d{1,2})\s+DIAS?',
            r'(?:CICLO|PERIODO)[:\s]+(\d{1,2})\s+DIAS?',
        ]

        for pattern in patterns:
            match = re.search(pattern, texto)
            if match:
                dias = int(match.group(1))
                # Validar: dias deve estar entre 1 e 45
                if 1 <= dias <= 45:
                    return dias

        # Calcular a partir das datas de leitura se disponíveis
        if leitura_ant_data and leitura_atual_data:
            delta = (leitura_atual_data - leitura_ant_data).days
            if 1 <= delta <= 45:
                return delta

        return None

    def _extrair_proxima_leitura(self, texto: str) -> Optional[date]:
        """Extrai data da próxima leitura"""
        pattern = r'PR[ÓO]XIMA\s+LEITURA[:\s]+(\d{2}[/\-]\d{2}[/\-]\d{4})'
        match = re.search(pattern, texto)
        if match:
            return self._parse_data_br(match.group(1))
        return None

    def _extrair_leitura_anterior(self, texto: str) -> Optional[int]:
        """Extrai valor da leitura anterior do medidor"""
        # Padrão Energisa MT: "Energia ativa em kWh Ponta 2283 2492 1 209"
        # Formato: descrição ANTERIOR ATUAL CONST DIFERENÇA
        pattern_energisa = r'ENERGIA\s+ATIVA\s+EM\s+KWH.*?PONTA\s+(\d+)\s+(\d+)\s+\d+\s+\d+'
        match = re.search(pattern_energisa, texto, re.IGNORECASE)
        if match:
            val = int(match.group(1))  # primeiro número é anterior
            if 100 <= val <= 99999999:
                return val

        # Padrões mais específicos
        patterns = [
            # LEITURA ANTERIOR: 12345 (valor com 4+ dígitos)
            r'LEITURA\s+ANTERIOR[:\s]+(\d{4,8})\b',
            # Tabela: | ANTERIOR | 12345 |
            r'\|\s*ANTERIOR\s*\|\s*(\d{4,8})\s*\|',
            # MEDIDOR linha com ANTERIOR: 12345
            r'MEDIDOR.*?ANTERIOR[:\s]+(\d{4,8})',
            # Contexto específico com KWH
            r'(\d{4,8})\s*KWH\s*ANTERIOR',
            # Tabela com KWH Ponta: anterior atual const diferença
            r'KWH.*?PONTA\s+(\d+)\s+\d+\s+\d+\s+\d+',
        ]
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                val = int(match.group(1))
                if 100 <= val <= 99999999:
                    return val
        return None

    def _extrair_leitura_atual(self, texto: str) -> Optional[int]:
        """Extrai valor da leitura atual do medidor"""
        # Padrão Energisa MT: "Energia ativa em kWh Ponta 2283 2492 1 209"
        pattern_energisa = r'ENERGIA\s+ATIVA\s+EM\s+KWH.*?PONTA\s+(\d+)\s+(\d+)\s+\d+\s+\d+'
        match = re.search(pattern_energisa, texto, re.IGNORECASE)
        if match:
            val = int(match.group(2))  # segundo número é atual
            if 100 <= val <= 99999999:
                return val

        # Padrões mais específicos
        patterns = [
            # LEITURA ATUAL: 12345 (valor com 4+ dígitos)
            r'LEITURA\s+ATUAL[:\s]+(\d{4,8})\b',
            # Tabela: | ATUAL | 12345 |
            r'\|\s*ATUAL\s*\|\s*(\d{4,8})\s*\|',
            # MEDIDOR linha com ATUAL: 12345
            r'MEDIDOR.*?ATUAL[:\s]+(\d{4,8})',
            # Contexto específico com KWH
            r'(\d{4,8})\s*KWH\s*ATUAL',
            # Tabela com KWH Ponta: anterior atual const diferença
            r'KWH.*?PONTA\s+\d+\s+(\d+)\s+\d+\s+\d+',
        ]
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                val = int(match.group(1))
                if 100 <= val <= 99999999:
                    return val
        return None

    def _extrair_itens_fatura(self, texto: str) -> ItensFaturaExtracted:
        """Extrai todos os itens da fatura"""

        # 1. Consumo em kWh
        consumo = self._extrair_consumo_kwh(texto)

        # 2. Energia Injetada oUC
        injetada_ouc = self._extrair_energia_injetada_ouc(texto)

        # 3. Energia Injetada mUC
        injetada_muc = self._extrair_energia_injetada_muc(texto)

        # 4. Ajuste Lei 14.300
        ajuste = self._extrair_ajuste_lei_14300(texto)

        # 5. Lançamentos e Serviços
        lancamentos = self._extrair_lancamentos_servicos(texto)

        return ItensFaturaExtracted(
            consumo_kwh=consumo,
            energia_injetada_ouc=injetada_ouc,
            energia_injetada_muc=injetada_muc,
            ajuste_lei_14300=ajuste,
            lancamentos_e_servicos=lancamentos
        )

    def _extrair_consumo_kwh(self, texto: str) -> Optional[ConsumoKwhExtracted]:
        """Extrai linha de consumo em kWh"""

        # Padrão específico Energisa MT: "Consumo em kWh ... KWH 209,00 ... 1,101380 230,18"
        # Formato: descrição ... unidade quantidade ... preço valor
        patterns_energisa = [
            # Consumo em kWh KWH 209,00 1,101380 230,18
            r'CONSUMO\s+EM\s+KWH\s+KWH\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
            # Linha com "Consumo em kWh" seguida de números
            r'CONSUMO\s+EM\s+KWH[^\d]+([\d.,]+)[^\d]+([\d.,]+)[^\d]+([\d.,]+)',
            # Energia ativa em kWh Ponta ANTERIOR ATUAL CONST DIFERENÇA
            r'ENERGIA\s+ATIVA\s+EM\s+KWH.*?(\d+)\s+(\d+)\s+\d+\s+(\d+)',
        ]

        for pattern in patterns_energisa:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                # Tentar interpretar os grupos
                g1, g2, g3 = match.groups()
                qtd = self._parse_float_br(g1)
                preco = self._parse_decimal_br(g2)
                valor = self._parse_decimal_br(g3)

                # Se primeiro grupo parece leitura (4+ dígitos sem vírgula), usar terceiro como quantidade
                if qtd and qtd > 1000 and ',' not in g1:
                    # Formato: anterior atual const diferença → diferença é o consumo
                    qtd = self._parse_float_br(g3)
                    preco = None
                    valor = None

                if qtd and 1 <= qtd <= 50000:
                    return ConsumoKwhExtracted(
                        unidade="KWH",
                        quantidade=qtd,
                        preco_unit_com_tributos=preco,
                        valor=valor
                    )

        # Padrões com quantidade, preço e valor (3 grupos)
        patterns_completos = [
            # CONSUMO EM KWH | KWH | 150 | 0,85 | 127,50
            r'CONSUMO\s+(?:EM\s+)?KWH[|\s]+KWH[|\s]+([\d.,]+)[|\s]+([\d.,]+)[|\s]+([\d.,]+)',
            # ENERGIA ATIVA CONSUMO | KWH | 150 | 0,85 | 127,50
            r'ENERGIA\s+ATIVA.*?CONSUMO[|\s]+KWH[|\s]+([\d.,]+)[|\s]+([\d.,]+)[|\s]+([\d.,]+)',
            # Energia Elétrica - kWh 150 0,85 127,50
            r'ENERGIA\s+EL[ÉE]TRICA.*?KWH\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
        ]

        for pattern in patterns_completos:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                qtd = self._parse_float_br(match.group(1))
                if qtd and 1 <= qtd <= 50000:
                    return ConsumoKwhExtracted(
                        unidade="KWH",
                        quantidade=qtd,
                        preco_unit_com_tributos=self._parse_decimal_br(match.group(2)),
                        valor=self._parse_decimal_br(match.group(3))
                    )

        # Padrões simples (apenas quantidade)
        patterns_simples = [
            # CONSUMO: 150 KWH
            r'CONSUMO[:\s]+([\d.,]+)\s*KWH',
            # CONSUMO FATURADO seguido por número em outra linha
            r'CONSUMO\s+FATURADO.*?KWH\s+([\d.,]+)',
            # KWH CONSUMIDOS: 150
            r'KWH\s+(?:CONSUMIDOS?|FATURADOS?)[:\s]+([\d.,]+)',
            # MEDIDO: 150 KWH
            r'MEDIDO[:\s]+([\d.,]+)\s*KWH',
            # ENERGIA CONSUMIDA: 150
            r'ENERGIA\s+CONSUMIDA[:\s]+([\d.,]+)',
            # Tabela com leitura: Ponta ANTERIOR ATUAL x DIFERENÇA
            r'PONTA\s+(\d+)\s+(\d+)\s+\d+\s+(\d+)',
        ]

        for pattern in patterns_simples:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                # Se tem 3 grupos (leituras), usar o último (diferença)
                if len(match.groups()) >= 3:
                    qtd = self._parse_float_br(match.group(3))
                else:
                    qtd = self._parse_float_br(match.group(1))

                if qtd and 1 <= qtd <= 50000:
                    return ConsumoKwhExtracted(
                        unidade="KWH",
                        quantidade=qtd
                    )

        return None

    def _extrair_energia_injetada_ouc(self, texto: str) -> List[EnergiaInjetadaItemExtracted]:
        """Extrai itens de energia injetada oUC"""
        return self._extrair_energia_injetada(texto, tipo="OUC")

    def _extrair_energia_injetada_muc(self, texto: str) -> List[EnergiaInjetadaItemExtracted]:
        """Extrai itens de energia injetada mUC"""
        return self._extrair_energia_injetada(texto, tipo="MUC")

    def _extrair_energia_injetada(self, texto: str, tipo: str) -> List[EnergiaInjetadaItemExtracted]:
        """
        Extrai itens de energia injetada (oUC ou mUC).

        Formatos suportados:
        1. ENERGIA ATIVA INJETADA GDII oUC | KWH | quantidade | preço | valor
        2. Energia Atv Injetada GDII ... 189,00 ... 1,101380 -208,16 (Energisa MT)
        3. D6118578678 Energia injetada Ponta ANTERIOR ATUAL CONST DIFERENÇA
        """
        itens = []

        # Padrão Energisa MT: "Energia Atv Injetada GDII ... KWH 189,00 ... -208,16"
        patterns_energisa = [
            # Energia Atv Injetada GDII ... quantidade ... preço valor
            r'ENERGIA\s+AT[IV]*\s+INJETADA\s+(GD\s*I{1,2})[^\d]*([\d.,]+)[^\d]+([\d.,]+)[^\d]+([\-\d.,]+)',
            # Energia injetada Ponta ANTERIOR ATUAL CONST DIFERENÇA
            r'ENERGIA\s+INJETADA.*?PONTA\s+(\d+)\s+(\d+)\s+\d+\s+(\d+)',
        ]

        for pattern in patterns_energisa:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                grupos = match.groups()

                if 'GD' in pattern:
                    # Formato com tipo GD explícito
                    tipo_gd_str = grupos[0].upper().replace(' ', '')
                    tipo_gd = "GDII" if "II" in tipo_gd_str or "2" in tipo_gd_str else "GDI"
                    qtd = self._parse_float_br(grupos[1])
                    preco = self._parse_decimal_br(grupos[2])
                    valor = self._parse_decimal_br(grupos[3])
                else:
                    # Formato com leituras (anterior, atual, diferença)
                    tipo_gd = None
                    qtd = self._parse_float_br(grupos[2])  # diferença
                    preco = None
                    valor = None

                if qtd and qtd > 0:
                    itens.append(EnergiaInjetadaItemExtracted(
                        descricao=match.group(0).strip()[:100],
                        tipo_gd=tipo_gd,
                        unidade="KWH",
                        quantidade=qtd,
                        preco_unit_com_tributos=preco,
                        valor=valor,
                        mes_ano_referencia_item=None
                    ))

        # Se já encontrou, retorna
        if itens:
            return itens

        # Regex padrão para outros formatos
        tipo_pattern = r'[OM]\s*UC' if tipo == "OUC" else r'M\s*UC'

        pattern = (
            r'ENERGIA\s+AT(?:IVA|V)?\s+INJETADA.*?' +
            tipo_pattern +
            r'.*?\|?\s*KWH\s*\|?\s*([\d.,]+)\s*\|?\s*([\d.,]+)\s*\|?\s*([\-\d.,]+)'
        )

        for match in re.finditer(pattern, texto, re.IGNORECASE):
            linha_completa = match.group(0)

            # Detectar tipo GD
            tipo_gd = None
            if 'GD' in linha_completa.upper():
                if 'GDII' in linha_completa.upper() or 'GD II' in linha_completa.upper():
                    tipo_gd = "GDII"
                elif 'GDI' in linha_completa.upper():
                    tipo_gd = "GDI"

            mes_ano_item = self._extrair_mes_ano_item(linha_completa)

            itens.append(EnergiaInjetadaItemExtracted(
                descricao=linha_completa.strip()[:100],
                tipo_gd=tipo_gd,
                unidade="KWH",
                quantidade=self._parse_float_br(match.group(1)),
                preco_unit_com_tributos=self._parse_decimal_br(match.group(2)),
                valor=self._parse_decimal_br(match.group(3)),
                mes_ano_referencia_item=mes_ano_item
            ))

        return itens

    def _extrair_mes_ano_item(self, linha: str) -> Optional[str]:
        """Extrai mês/ano de referência de um item específico"""
        # Padrão: 09/2025 ou SET/25
        patterns = [
            r'(\d{2})/(\d{4})',  # 09/2025
            r'(\d{2})/(\d{2})',  # 09/25
            r'([A-Z]{3})/(\d{2,4})'  # SET/25
        ]

        for pattern in patterns:
            match = re.search(pattern, linha)
            if match:
                mes_str = match.group(1)
                ano_str = match.group(2)

                # Se mês é texto, converter
                if mes_str.isalpha():
                    mes = self.MESES_PT.get(mes_str.lower())
                    if not mes:
                        continue
                else:
                    mes = int(mes_str)

                ano = int(ano_str)
                if ano < 100:
                    ano = 2000 + ano

                return f"{ano:04d}-{mes:02d}"

        return None

    def _extrair_ajuste_lei_14300(self, texto: str) -> Optional[AjusteLei14300Extracted]:
        """Extrai ajuste GD II - Lei 14.300/22"""
        # Padrões para diferentes formatos
        patterns = [
            # Padrão com | separador
            r'AJUSTE.*?LEI\s+14\.?300.*?\|?\s*KWH\s*\|?\s*([\d.,]+)\s*\|?\s*([\d.,]+)\s*\|?\s*([\d.,]+)',
            # Padrão Energisa MT: "Ajuste GDII - TRF Reduzida(Lei 14.300/22) ... KWH quantidade preço valor"
            r'AJUSTE\s+GD\s*II.*?LEI\s+14\.?300.*?KWH\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
            # Padrão mais genérico: "Ajuste GDII ... quantidade ... preço valor"
            r'AJUSTE\s+GD\s*II[^\d]+([\d.,]+)[^\d]+([\d.,]+)[^\d]+([\d.,]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                qtd = self._parse_float_br(match.group(1))
                # Validar quantidade razoável
                if qtd and 0 < qtd <= 50000:
                    return AjusteLei14300Extracted(
                        descricao=match.group(0)[:100],
                        unidade="KWH",
                        quantidade=qtd,
                        preco_unit_com_tributos=self._parse_decimal_br(match.group(2)),
                        valor=self._parse_decimal_br(match.group(3))
                    )

        return None

    def _extrair_lancamentos_servicos(self, texto: str) -> List[LancamentoServicoExtracted]:
        """Extrai lançamentos e serviços"""
        lancamentos = []

        # Procurar seção de lançamentos
        secao_pattern = r'LAN[ÇC]AMENTOS\s+E\s+SERVI[ÇC]OS(.*?)(?:TOTAL|RESUMO|$)'
        secao_match = re.search(secao_pattern, texto, re.DOTALL)

        if not secao_match:
            # Tentar padrões comuns de lançamentos mesmo fora da seção
            secao_texto = texto
        else:
            secao_texto = secao_match.group(1)

        # Padrões comuns de lançamentos
        # Formato: CONTRIB DE ILUM PUB | 35,00
        patterns = [
            r'(CONTRIB.*?ILUM.*?PUB.*?)[|\s]+([\d.,]+)',
            r'((?:MULTA|JUROS).*?)[|\s]+([\d.,]+)',
            r'(BANDEIRA.*?)[|\s]+([\d.,]+)',
            r'([A-Z\s]{10,50}?)[|\s]+(\-?[\d.,]+)'  # Genérico
        ]

        encontrados = set()  # Evitar duplicatas
        for pattern in patterns:
            for match in re.finditer(pattern, secao_texto):
                descricao = match.group(1).strip()
                valor_str = match.group(2)

                # Evitar duplicatas
                key = (descricao, valor_str)
                if key in encontrados:
                    continue
                encontrados.add(key)

                lancamentos.append(LancamentoServicoExtracted(
                    descricao=descricao,
                    valor=self._parse_decimal_br(valor_str)
                ))

        return lancamentos

    def _extrair_totais(self, texto: str, itens: ItensFaturaExtracted) -> TotaisExtracted:
        """Extrai totais calculados"""

        # Adicionais de bandeira
        adicionais_bandeira = Decimal("0")
        for lanc in itens.lancamentos_e_servicos:
            if lanc.descricao and 'BANDEIRA' in lanc.descricao:
                adicionais_bandeira += (lanc.valor or Decimal("0"))

        # Soma de lançamentos
        total_lancamentos = sum(
            (lanc.valor or Decimal("0"))
            for lanc in itens.lancamentos_e_servicos
        )

        # Total geral (já foi extraído em _extrair_total_pagar)
        total_geral = self._extrair_total_pagar(texto)

        return TotaisExtracted(
            adicionais_bandeira=adicionais_bandeira if adicionais_bandeira != 0 else None,
            lancamentos_e_servicos=total_lancamentos if total_lancamentos != 0 else None,
            total_geral_fatura=total_geral
        )

    def _extrair_quadro_atencao(self, texto: str) -> Optional[QuadroAtencaoExtracted]:
        """Extrai informações do quadro de atenção (GD)"""
        saldo_acum = None
        a_expirar = None
        expirados = None

        # Padrão Energisa MT: "Saldo Acumulado: 391 A expirar no próximo ciclo: 0"
        pattern_energisa = r'SALDO\s+ACUMULADO[:\s]+([\d.,]+)\s*A\s+EXPIRAR.*?CICLO[:\s]+([\d.,]+)'
        match = re.search(pattern_energisa, texto, re.IGNORECASE)
        if match:
            saldo_acum = self._parse_decimal_br(match.group(1))
            a_expirar = self._parse_decimal_br(match.group(2))
        else:
            # Saldo acumulado - múltiplos padrões
            patterns_saldo = [
                r'SALDO\s+ACUMULADO[:\s]+([\d.,]+)',
                r'SALDO\s+(?:DE\s+)?CR[ÉE]DITOS?[:\s]+([\d.,]+)',
                r'CR[ÉE]DITOS?\s+ACUMULADOS?[:\s]+([\d.,]+)',
                r'SALDO\s+KWH[:\s]+([\d.,]+)',
            ]
            for pattern in patterns_saldo:
                match = re.search(pattern, texto, re.IGNORECASE)
                if match:
                    saldo_acum = self._parse_decimal_br(match.group(1))
                    break

            # A expirar próximo ciclo - múltiplos padrões
            patterns_expirar = [
                r'A\s+EXPIRAR.*?(?:PR[ÓO]XIMO\s+)?CICLO[:\s]+([\d.,]+)',
                r'EXPIRAM?\s+(?:NO\s+)?PR[ÓO]XIMO[:\s]+([\d.,]+)',
                r'VENCER[:\s]+([\d.,]+)\s*KWH',
                r'CR[ÉE]DITOS?\s+A\s+VENCER[:\s]+([\d.,]+)',
            ]
            for pattern in patterns_expirar:
                match = re.search(pattern, texto, re.IGNORECASE)
                if match:
                    a_expirar = self._parse_decimal_br(match.group(1))
                    break

        # Créditos já expirados
        patterns_expirados = [
            r'CR[ÉE]DITOS?\s+EXPIRADOS?[:\s]+([\d.,]+)',
            r'EXPIRADOS?\s+(?:NESTE\s+)?CICLO[:\s]+([\d.,]+)',
            r'PERDIDOS?[:\s]+([\d.,]+)\s*KWH',
        ]
        for pattern in patterns_expirados:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                expirados = self._parse_decimal_br(match.group(1))
                break

        if saldo_acum is not None or a_expirar is not None or expirados is not None:
            return QuadroAtencaoExtracted(
                saldo_acumulado=saldo_acum,
                a_expirar_proximo_ciclo=a_expirar,
                creditos_expirados=expirados
            )

        return None

    def _extrair_bandeira(self, texto: str) -> Optional[str]:
        """Extrai bandeira tarifária"""
        patterns = [
            r'BANDEIRA[:\s]+(VERDE|AMARELA|VERMELHA\s*(?:I{1,2})?)',
            # Padrão Energisa MT: "Adic. B. Vermelha"
            r'ADIC\.?\s*B\.?\s*(VERDE|AMARELA|VERMELHA)',
            # "Bandeira Vermelha"
            r'(VERDE|AMARELA|VERMELHA)\s*(?:PATAMAR\s*)?(I{1,2})?',
        ]
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                bandeira = match.group(1).upper().strip()
                # Se tem segundo grupo (patamar), adicionar
                if len(match.groups()) > 1 and match.group(2):
                    bandeira += " " + match.group(2).upper()
                return bandeira
        return None

    # ===== Utilitários =====

    def _parse_data_br(self, data_str: str) -> Optional[date]:
        """Converte data BR (DD/MM/YYYY) para date"""
        try:
            # Limpar e normalizar
            data_str = data_str.strip().replace('-', '/')
            dia, mes, ano = data_str.split('/')
            return date(int(ano), int(mes), int(dia))
        except:
            return None

    def _parse_decimal_br(self, valor_str: str) -> Optional[Decimal]:
        """Converte número BR (1.234,56) para Decimal"""
        try:
            # Limpar
            valor_str = valor_str.strip().replace('R$', '').replace(' ', '')

            # Se tem vírgula, é BR
            if ',' in valor_str:
                # Remover pontos (milhares) e trocar vírgula por ponto
                valor_str = valor_str.replace('.', '').replace(',', '.')
            # Senão, já está no formato correto

            return Decimal(valor_str)
        except:
            return None

    def _parse_float_br(self, valor_str: str) -> Optional[float]:
        """Converte número BR para float"""
        decimal_val = self._parse_decimal_br(valor_str)
        return float(decimal_val) if decimal_val is not None else None

    # ===== Novos Métodos de Extração =====

    def _extrair_dados_instalacao(self, texto: str, texto_original: str) -> Optional[DadosInstalacaoExtracted]:
        """Extrai dados da instalação/medidor"""
        numero_medidor = None
        numero_instalacao = None
        classe_consumo = None
        subclasse = None
        modalidade = None
        tensao = None
        carga = None
        endereco = None

        # Número do medidor
        patterns_medidor = [
            r'(?:N[ÚU]MERO\s+DO\s+)?MEDIDOR[:\s]+(\d{6,15})',
            r'MED(?:IDOR)?[:\s]+(\d{6,15})',
            r'MEDIDOR\s*[:\s]*(\d+)',
        ]
        for pattern in patterns_medidor:
            match = re.search(pattern, texto)
            if match:
                numero_medidor = match.group(1)
                break

        # Número da instalação
        patterns_instalacao = [
            r'(?:N[ÚU]MERO\s+DA\s+)?INSTALA[ÇC][ÃA]O[:\s]+(\d{6,15})',
            r'INSTALA[ÇC][ÃA]O\s*[:\s]*(\d+)',
        ]
        for pattern in patterns_instalacao:
            match = re.search(pattern, texto)
            if match:
                numero_instalacao = match.group(1)
                break

        # Classe de consumo
        patterns_classe = [
            r'CLASSE[:\s]+(RESIDENCIAL|COMERCIAL|INDUSTRIAL|RURAL|PODER\s+P[ÚU]BLICO|ILUMINA[ÇC][ÃA]O)',
            r'(RESIDENCIAL|COMERCIAL|INDUSTRIAL|RURAL)\s+(?:NORMAL|BAIXA\s+RENDA)',
        ]
        for pattern in patterns_classe:
            match = re.search(pattern, texto)
            if match:
                classe_consumo = match.group(1).strip()
                break

        # Subclasse (Baixa Renda, Normal, etc)
        if 'BAIXA\s*RENDA' in texto or 'BX\s*RENDA' in texto:
            subclasse = "BAIXA RENDA"
        elif 'NORMAL' in texto:
            subclasse = "NORMAL"

        # Modalidade tarifária
        patterns_modalidade = [
            r'MODALIDADE[:\s]+(CONVENCIONAL|BRANCA|AZUL|VERDE)',
            r'TARIF[ÁA]RIA[:\s]+(CONVENCIONAL|BRANCA|AZUL|VERDE)',
            r'\b(CONVENCIONAL|TARIFA\s+BRANCA)\b',
        ]
        for pattern in patterns_modalidade:
            match = re.search(pattern, texto)
            if match:
                modalidade = match.group(1).strip()
                break

        # Tensão nominal - valores típicos: 127V, 220V, 380V, 440V
        patterns_tensao = [
            r'TENS[ÃA]O[:\s]+(127|220|380|440|110|230)\s*V',
            r'\b(127|220|380|440|110|230)\s*V(?:OLTS)?\b',
            r'TENS[ÃA]O\s+NOMINAL[:\s]+([\d]+)\s*V',
        ]
        for pattern in patterns_tensao:
            match = re.search(pattern, texto)
            if match:
                val = match.group(1)
                # Validar que é um valor de tensão válido
                if val.isdigit() and int(val) in [110, 127, 220, 230, 380, 440]:
                    tensao = f"{val}V"
                    break

        # Carga instalada
        patterns_carga = [
            r'CARGA\s+(?:INSTALADA)?[:\s]+([\d.,]+)\s*(?:KW|KVA)',
        ]
        for pattern in patterns_carga:
            match = re.search(pattern, texto)
            if match:
                carga = self._parse_float_br(match.group(1))
                break

        # Endereço (usar texto original para preservar case)
        # Palavras que indicam que NÃO é endereço (propaganda, instruções)
        palavras_invalidas = [
            'NOSSO NÚMERO', 'FÁCIL', 'RÁPIDO', 'SEGURO', 'ACESSE', 'BAIXE',
            'APLICATIVO', 'WWW', 'HTTP', 'CLIQUE', 'LIGUE', 'CENTRAL',
            'ATENDIMENTO', 'SAC', 'OUVIDORIA', 'PAGUE', 'BOLETO'
        ]

        patterns_endereco = [
            # Endereço seguido de nome de rua/avenida
            r'ENDERE[ÇC]O[:\s]+((?:RUA|R\.|AV|AVENIDA|TRAVESSA|TV\.|ALAMEDA|AL\.|ESTRADA|ROD)[^\n]+)',
            # Rua/Avenida diretas
            r'\b((?:RUA|R\.)\s+[A-ZÁÉÍÓÚÃÕÂÊÎÔÛ][A-ZÁÉÍÓÚÃÕÂÊÎÔÛ\s]+[,\s]+\d+[^\n]*)',
            r'\b((?:AV|AVENIDA)\.?\s+[A-ZÁÉÍÓÚÃÕÂÊÎÔÛ][A-ZÁÉÍÓÚÃÕÂÊÎÔÛ\s]+[,\s]+\d+[^\n]*)',
        ]
        for pattern in patterns_endereco:
            match = re.search(pattern, texto_original, re.IGNORECASE)
            if match:
                endereco_candidato = match.group(1).strip()[:200]
                # Verificar se não contém palavras inválidas
                upper_candidato = endereco_candidato.upper()
                if not any(palavra in upper_candidato for palavra in palavras_invalidas):
                    endereco = endereco_candidato
                    break

        # Só retorna se encontrou algo
        if any([numero_medidor, numero_instalacao, classe_consumo, modalidade, tensao, endereco]):
            return DadosInstalacaoExtracted(
                numero_medidor=numero_medidor,
                numero_instalacao=numero_instalacao,
                classe_consumo=classe_consumo,
                subclasse=subclasse,
                modalidade_tarifaria=modalidade,
                tensao_nominal=tensao,
                carga_instalada=carga,
                endereco=endereco
            )

        return None

    def _extrair_media_consumo_13m(self, texto: str) -> Optional[MediaConsumo13MExtracted]:
        """Extrai histórico de consumo dos últimos 13 meses"""
        meses = []

        # Limite máximo razoável de consumo mensal (kWh)
        # - Residencial: até 2000 kWh/mês (casas grandes)
        # - Comercial pequeno: até 10000 kWh/mês
        # - Industrial: até 50000 kWh/mês
        MAX_KWH_MENSAL = 50000

        # Padrão: tabela com meses e valores kWh
        # Formato típico: JAN/24 | 150 | FEV/24 | 160 | ...
        patterns = [
            r'([A-Z]{3})/(\d{2})\s*[:\|]?\s*(\d{1,5})\b',  # JAN/24: 150 (max 5 dígitos)
            r'(\d{2})/(\d{4})\s*[:\|]?\s*(\d{1,5})\s*KWH',  # 01/2024: 150 KWH
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, texto):
                mes_str = match.group(1)
                ano_str = match.group(2)
                kwh_str = match.group(3)

                # Converter mês
                if mes_str.isalpha():
                    mes_num = self.MESES_PT.get(mes_str.lower())
                    if not mes_num:
                        continue
                else:
                    mes_num = int(mes_str)
                    if not (1 <= mes_num <= 12):
                        continue

                # Converter ano
                ano = int(ano_str)
                if ano < 100:
                    ano = 2000 + ano

                # Validar ano razoável
                if not (2020 <= ano <= 2030):
                    continue

                kwh = int(kwh_str)

                # Validar kWh - descartar valores absurdos
                if kwh > MAX_KWH_MENSAL:
                    continue

                # Evitar duplicatas
                mes_ano = f"{ano:04d}-{mes_num:02d}"
                if not any(m.mes == mes_ano for m in meses):
                    meses.append(ConsumoMesExtracted(
                        mes=mes_ano,
                        kwh=float(kwh)
                    ))

        if meses:
            # Calcular média (apenas valores válidos)
            valores_validos = [m.kwh for m in meses if m.kwh and m.kwh <= MAX_KWH_MENSAL]
            media = sum(valores_validos) / len(valores_validos) if valores_validos else None
            return MediaConsumo13MExtracted(
                media_kwh=media,
                meses=meses[:13]  # Limitar a 13 meses
            )

        return None

    def _calcular_consumo_total(self, leitura_ant: Optional[int], leitura_atual: Optional[int], itens: ItensFaturaExtracted) -> Optional[float]:
        """Calcula consumo total em kWh"""
        # Prioridade 1: diferença de leituras
        if leitura_ant is not None and leitura_atual is not None:
            consumo = leitura_atual - leitura_ant
            if consumo >= 0:
                return float(consumo)

        # Prioridade 2: item de consumo
        if itens.consumo_kwh and itens.consumo_kwh.quantidade:
            return float(itens.consumo_kwh.quantidade)

        return None

    def _calcular_energia_injetada_total(self, itens: ItensFaturaExtracted) -> Optional[float]:
        """Calcula total de energia injetada (oUC + mUC)"""
        total = 0.0

        for item in itens.energia_injetada_ouc:
            if item.quantidade:
                total += abs(item.quantidade)

        for item in itens.energia_injetada_muc:
            if item.quantidade:
                total += abs(item.quantidade)

        return total if total > 0 else None

    def _calcular_energia_compensada_total(self, itens: ItensFaturaExtracted, texto: str) -> Optional[float]:
        """Calcula total de energia compensada da rede"""
        # Tentar extrair diretamente do texto
        patterns = [
            r'ENERGIA\s+COMPENSADA[:\s]+([\d.,]+)\s*KWH',
            r'COMPENSA[ÇC][ÃA]O[:\s]+([\d.,]+)\s*KWH',
            r'CR[ÉE]DITOS?\s+UTILIZADOS?[:\s]+([\d.,]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, texto)
            if match:
                val = self._parse_float_br(match.group(1))
                if val:
                    return val

        # Se não encontrar direto, usar energia injetada como proxy
        return self._calcular_energia_injetada_total(itens)

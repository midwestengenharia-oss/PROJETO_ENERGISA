/**
 * API - Faturas
 */

import { api } from './client';
import type { Fatura } from './types';

export interface FaturaFilters {
    uc_id?: number;
    status?: 'pendente' | 'paga' | 'vencida' | 'cancelada';
    mes?: number;
    ano?: number;
    page?: number;
    limit?: number;
}

export interface FaturaManualRequest {
    uc_id: number;
    mes_referencia: number;
    ano_referencia: number;
    valor_fatura: number;
    consumo?: number;
    data_vencimento: string;
    observacoes?: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
    pages: number;
}

export const faturasApi = {
    // Listar faturas
    listar: (filters?: FaturaFilters) =>
        api.get<PaginatedResponse<Fatura>>('/faturas', { params: filters }),

    // Buscar fatura por ID
    buscar: (id: number) =>
        api.get<Fatura>(`/faturas/${id}`),

    // Faturas por UC
    porUC: (ucId: number) =>
        api.get<Fatura[]>(`/faturas/uc/${ucId}`),

    // Estatísticas da UC
    estatisticas: (ucId: number) =>
        api.get<{
            total_faturas: number;
            valor_total: number;
            consumo_total: number;
            media_mensal: number;
        }>(`/faturas/uc/${ucId}/estatisticas`),

    // Comparativo mensal
    comparativo: (ucId: number) =>
        api.get<any>(`/faturas/uc/${ucId}/comparativo`),

    // Histórico de GD (Geração Distribuída)
    historicoGD: (ucId: number) =>
        api.get<any[]>(`/faturas/uc/${ucId}/gd`),

    // Buscar fatura por referência (mês/ano)
    porReferencia: (ucId: number, ano: number, mes: number) =>
        api.get<Fatura>(`/faturas/uc/${ucId}/${ano}/${mes}`),

    // Criar fatura manual
    criarManual: (data: FaturaManualRequest) =>
        api.post<Fatura>('/faturas/manual', data),
};

/**
 * Helper para download do PDF da fatura a partir do base64
 */
export const downloadFaturaPdf = (fatura: Fatura): boolean => {
    if (!fatura.pdf_base64) {
        return false;
    }

    try {
        const link = document.createElement('a');
        link.href = `data:application/pdf;base64,${fatura.pdf_base64}`;
        link.download = `fatura_${fatura.mes_referencia.toString().padStart(2, '0')}_${fatura.ano_referencia}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        return true;
    } catch (error) {
        console.error('Erro ao baixar PDF:', error);
        return false;
    }
};

export default faturasApi;

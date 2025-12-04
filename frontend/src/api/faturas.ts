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

export default faturasApi;

/**
 * API - Contratos
 */

import { api } from './client';
import type { Contrato } from './types';

export interface ContratoFilters {
    tipo?: 'beneficiario' | 'gestor' | 'proprietario';
    status?: 'ativo' | 'pendente' | 'cancelado' | 'expirado';
    usina_id?: number;
    page?: number;
    limit?: number;
}

export interface ContratoCreateRequest {
    tipo: 'GESTOR_PROPRIETARIO' | 'GESTOR_BENEFICIARIO' | 'PROPRIETARIO_BENEFICIARIO';
    parte_a_id: string;
    parte_b_id: string;
    usina_id?: number;
    beneficiario_id?: number;
    vigencia_inicio?: string;
    vigencia_fim?: string;
    percentual_rateio?: number;
    desconto?: number;
    comissao?: number;
}

export interface ContratoUpdateRequest {
    status?: 'RASCUNHO' | 'AGUARDANDO_ASSINATURA' | 'ATIVO' | 'EXPIRADO' | 'CANCELADO';
    vigencia_fim?: string;
    percentual_rateio?: number;
    desconto?: number;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
    pages: number;
}

export const contratosApi = {
    // Listar contratos
    listar: (filters?: ContratoFilters) =>
        api.get<PaginatedResponse<Contrato>>('/contratos', { params: filters }),

    // Meus contratos
    meus: () =>
        api.get<Contrato[]>('/contratos/meus'),

    // Buscar contrato por ID
    buscar: (id: number) =>
        api.get<Contrato>(`/contratos/${id}`),

    // Criar novo contrato
    criar: (data: ContratoCreateRequest) =>
        api.post<Contrato>('/contratos', data),

    // Atualizar contrato
    atualizar: (id: number, data: ContratoUpdateRequest) =>
        api.put<Contrato>(`/contratos/${id}`, data),

    // Rescindir contrato
    rescindir: (id: number, motivo?: string) =>
        api.post(`/contratos/${id}/rescindir`, { motivo }),

    // Suspender contrato
    suspender: (id: number, motivo?: string) =>
        api.post(`/contratos/${id}/suspender`, { motivo }),

    // Reativar contrato
    reativar: (id: number) =>
        api.post(`/contratos/${id}/reativar`),

    // Enviar para assinatura
    enviarAssinatura: (id: number, email?: string) =>
        api.post(`/contratos/${id}/enviar-assinatura`, { email }),

    // Registrar assinatura
    registrarAssinatura: (id: number, assinatura: string, ip?: string) =>
        api.post(`/contratos/${id}/assinar`, { assinatura, ip }),

    // Estatísticas de contratos
    estatisticas: () =>
        api.get<any>('/contratos/estatisticas'),

    // Contratos por usina
    porUsina: (usinaId: number) =>
        api.get<Contrato[]>(`/contratos/usina/${usinaId}`),
};

export default contratosApi;

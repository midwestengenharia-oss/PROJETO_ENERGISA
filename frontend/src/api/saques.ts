/**
 * API - Saques
 */

import { api } from './client';
import type { Saque } from './types';

export interface SaqueFilters {
    status?: 'pendente' | 'aprovado' | 'rejeitado' | 'pago';
    usuario_id?: number;
    page?: number;
    limit?: number;
}

export interface SaqueCreateRequest {
    valor: number;
    tipo_chave_pix: 'cpf' | 'cnpj' | 'email' | 'telefone' | 'aleatoria';
    chave_pix: string;
    observacoes?: string;
}

export interface SaqueAprovarRequest {
    observacoes?: string;
}

export interface SaqueRejeitarRequest {
    motivo: string;
}

export interface SaquePagarRequest {
    comprovante?: string;
    data_pagamento?: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
    pages: number;
}

export const saquesApi = {
    // Listar saques (admin vê todos, usuário vê só os seus)
    listar: (filters?: SaqueFilters) =>
        api.get<PaginatedResponse<Saque>>('/saques', { params: filters }),

    // Meus saques
    meus: () =>
        api.get<Saque[]>('/saques/meus'),

    // Buscar saque por ID
    buscar: (id: number) =>
        api.get<Saque>(`/saques/${id}`),

    // Solicitar novo saque
    solicitar: (data: SaqueCreateRequest) =>
        api.post<Saque>('/saques', data),

    // Cancelar saque (apenas se pendente)
    cancelar: (id: number) =>
        api.post(`/saques/${id}/cancelar`),

    // [ADMIN] Aprovar saque
    aprovar: (id: number, data?: SaqueAprovarRequest) =>
        api.post<Saque>(`/saques/${id}/aprovar`, data),

    // [ADMIN] Rejeitar saque
    rejeitar: (id: number, data: SaqueRejeitarRequest) =>
        api.post<Saque>(`/saques/${id}/rejeitar`, data),

    // [ADMIN] Marcar como pago
    marcarPago: (id: number, data?: SaquePagarRequest) =>
        api.post<Saque>(`/saques/${id}/pagar`, data),

    // Saldo disponível para saque
    saldoDisponivel: () =>
        api.get<{ saldo: number; bloqueado: number; disponivel: number }>('/saques/saldo'),

    // Listar comissões
    comissoes: () =>
        api.get<any[]>('/saques/comissoes'),

    // Estatísticas de saques
    estatisticas: () =>
        api.get<{
            total_pendente: number;
            total_aprovado: number;
            total_pago: number;
            quantidade: { pendente: number; aprovado: number; pago: number };
        }>('/saques/estatisticas'),

    // [ADMIN] Listar saques pendentes
    pendentes: () =>
        api.get<Saque[]>('/saques/pendentes'),
};

export default saquesApi;

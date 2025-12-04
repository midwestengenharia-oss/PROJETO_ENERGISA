/**
 * API - Usinas (Geradoras)
 */

import { api } from './client';
import type { Usina, Beneficiario } from './types';

export interface UsinaFilters {
    status?: 'ativa' | 'inativa' | 'manutencao';
    proprietario_id?: number;
    page?: number;
    limit?: number;
}

export interface UsinaCreateRequest {
    nome: string;
    cod_empresa: number;
    cdc: number;
    digito_verificador: number;
    capacidade_kwp?: number;
    tipo_geracao?: string;
    endereco?: string;
    cidade?: string;
    uf?: string;
    data_conexao?: string;
}

export interface UsinaUpdateRequest {
    nome?: string;
    capacidade_kwp?: number;
    status?: 'ativa' | 'inativa' | 'manutencao';
    endereco?: string;
    cidade?: string;
    uf?: string;
}

export interface AdicionarGestorRequest {
    usuario_id: string;
    permissoes?: string[];
}

export interface VincularBeneficiarioRequest {
    beneficiario_id: number;
    percentual_rateio: number;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
    pages: number;
}

export const usinasApi = {
    // Listar usinas
    listar: (filters?: UsinaFilters) =>
        api.get<PaginatedResponse<Usina>>('/usinas', { params: filters }),

    // Minhas usinas (proprietário/gestor)
    minhas: () =>
        api.get<Usina[]>('/usinas/minhas'),

    // Buscar usina por ID
    buscar: (id: number) =>
        api.get<Usina>(`/usinas/${id}`),

    // Criar nova usina
    criar: (data: UsinaCreateRequest) =>
        api.post<Usina>('/usinas', data),

    // Atualizar usina
    atualizar: (id: number, data: UsinaUpdateRequest) =>
        api.put<Usina>(`/usinas/${id}`, data),

    // Excluir usina
    excluir: (id: number) =>
        api.delete(`/usinas/${id}`),

    // Listar gestores da usina
    listarGestores: (usinaId: number) =>
        api.get<any[]>(`/usinas/${usinaId}/gestores`),

    // Adicionar gestor à usina
    adicionarGestor: (usinaId: number, data: AdicionarGestorRequest) =>
        api.post(`/usinas/${usinaId}/gestores`, data),

    // Remover gestor da usina
    removerGestor: (usinaId: number, gestorId: string) =>
        api.delete(`/usinas/${usinaId}/gestores/${gestorId}`),

    // Listar beneficiários da usina
    listarBeneficiarios: (usinaId: number) =>
        api.get<Beneficiario[]>(`/usinas/${usinaId}/beneficiarios`),

    // Vincular beneficiário à usina
    vincularBeneficiario: (usinaId: number, data: VincularBeneficiarioRequest) =>
        api.post(`/usinas/${usinaId}/beneficiarios`, data),

    // Desvincular beneficiário
    desvincularBeneficiario: (usinaId: number, beneficiarioId: number) =>
        api.delete(`/usinas/${usinaId}/beneficiarios/${beneficiarioId}`),
};

export default usinasApi;

/**
 * API - Admin
 */

import { api } from './client';

export interface ConfiguracaoSistema {
    chave: string;
    valor: string;
    descricao?: string;
    tipo: 'string' | 'number' | 'boolean' | 'json';
}

export interface LogAuditoria {
    id: number;
    usuario_id: string;
    usuario_nome: string;
    acao: string;
    entidade: string;
    entidade_id?: number;
    dados_antes?: any;
    dados_depois?: any;
    ip?: string;
    criado_em: string;
}

export interface LogFilters {
    usuario_id?: string;
    acao?: string;
    entidade?: string;
    page?: number;
    limit?: number;
}

export interface GraficoRequest {
    tipo: string;
    periodo?: string;
    data_inicio?: string;
    data_fim?: string;
}

export interface RelatorioRequest {
    tipo: string;
    formato?: 'pdf' | 'xlsx' | 'csv';
    filtros?: Record<string, any>;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
    pages: number;
}

export const adminApi = {
    // ==================== DASHBOARD ====================

    // Estatísticas gerais do dashboard
    estatisticas: () =>
        api.get<{
            usuarios: { total: number; ativos: number; novos_mes: number };
            usinas: { total: number; ativas: number };
            leads: { total: number; novos_mes: number; convertidos_mes: number };
            financeiro: { receita_mes: number; saques_pendentes: number };
        }>('/admin/dashboard/stats'),

    // Gerar dados para gráficos
    grafico: (data: GraficoRequest) =>
        api.post<any>('/admin/dashboard/grafico', data),

    // ==================== CONFIGURAÇÕES ====================

    // Listar configurações
    listarConfiguracoes: () =>
        api.get<ConfiguracaoSistema[]>('/admin/configuracoes'),

    // Atualizar configuração
    atualizarConfiguracao: (chave: string, valor: string) =>
        api.put(`/admin/configuracoes/${chave}`, { valor }),

    // ==================== LOGS ====================

    // Listar logs de auditoria
    listarLogs: (filters?: LogFilters) =>
        api.get<PaginatedResponse<LogAuditoria>>('/admin/logs', { params: filters }),

    // ==================== RELATÓRIOS ====================

    // Gerar relatório
    gerarRelatorio: (data: RelatorioRequest) =>
        api.post<{ url: string; nome: string }>('/admin/relatorios', data),

    // ==================== INTEGRAÇÕES ====================

    // Verificar status das integrações
    verificarIntegracoes: () =>
        api.get<{
            supabase: { status: string; latency?: number };
            energisa: { status: string; latency?: number };
            email: { status: string };
        }>('/admin/integracoes'),

    // Health check detalhado
    healthDetailed: () =>
        api.get<{
            status: string;
            version: string;
            uptime: number;
            services: Record<string, { status: string; message?: string }>;
        }>('/admin/health-detailed'),
};

export default adminApi;

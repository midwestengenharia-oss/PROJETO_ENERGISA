/**
 * API de Autenticação
 */

import api from './client';
import type {
    SignUpRequest,
    SignUpResponse,
    SignInRequest,
    SignInResponse,
    Usuario,
    PerfilResponse,
} from './types';

export const authApi = {
    /**
     * Cadastro de novo usuário
     */
    signup: async (data: SignUpRequest): Promise<SignUpResponse> => {
        const response = await api.post<SignUpResponse>('/auth/signup', data);
        return response.data;
    },

    /**
     * Login
     */
    signin: async (data: SignInRequest): Promise<SignInResponse> => {
        const response = await api.post<SignInResponse>('/auth/signin', data);
        return response.data;
    },

    /**
     * Logout
     */
    logout: async (): Promise<void> => {
        await api.post('/auth/logout');
    },

    /**
     * Refresh token
     */
    refresh: async (refreshToken: string): Promise<{ access_token: string; refresh_token: string; expires_in: number }> => {
        const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
        return response.data;
    },

    /**
     * Busca dados do usuário logado
     */
    me: async (): Promise<Usuario> => {
        const response = await api.get<Usuario>('/auth/me');
        return response.data;
    },

    /**
     * Busca perfis do usuário
     */
    perfis: async (): Promise<PerfilResponse[]> => {
        const response = await api.get<PerfilResponse[]>('/auth/perfis');
        return response.data;
    },

    /**
     * Atualiza perfil do usuário
     */
    updateProfile: async (data: { nome_completo?: string; telefone?: string }): Promise<Usuario> => {
        const response = await api.put<Usuario>('/auth/me', data);
        return response.data;
    },

    /**
     * Troca senha
     */
    changePassword: async (data: { current_password: string; new_password: string }): Promise<void> => {
        await api.post('/auth/me/senha', data);
    },
};

export default authApi;

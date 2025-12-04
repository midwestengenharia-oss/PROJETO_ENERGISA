/**
 * API Client - Axios configurado para o backend
 */

import axios from 'axios';
import type { AxiosError, AxiosRequestConfig } from 'axios';

// Tipo para config interno do axios
type InternalConfig = AxiosRequestConfig & { headers: Record<string, string> };

// URL da API
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Cria instância do axios
export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Chaves do localStorage
const TOKEN_KEY = 'plataforma_gd_access_token';
const REFRESH_KEY = 'plataforma_gd_refresh_token';
const EXPIRY_KEY = 'plataforma_gd_token_expiry';

// Funções de token
export const tokenUtils = {
    getAccessToken: () => localStorage.getItem(TOKEN_KEY),
    getRefreshToken: () => localStorage.getItem(REFRESH_KEY),
    getExpiry: () => localStorage.getItem(EXPIRY_KEY),

    saveTokens: (accessToken: string, refreshToken: string, expiresIn: number) => {
        localStorage.setItem(TOKEN_KEY, accessToken);
        localStorage.setItem(REFRESH_KEY, refreshToken);
        // Calcula expiração com margem de 5 minutos
        const expiryTime = Date.now() + (expiresIn * 1000) - (5 * 60 * 1000);
        localStorage.setItem(EXPIRY_KEY, expiryTime.toString());
    },

    clearTokens: () => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_KEY);
        localStorage.removeItem(EXPIRY_KEY);
    },

    isTokenExpiringSoon: (): boolean => {
        const expiry = localStorage.getItem(EXPIRY_KEY);
        if (!expiry) return true;
        return Date.now() >= parseInt(expiry);
    },
};

// Flag para evitar múltiplos refreshes simultâneos
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

const subscribeTokenRefresh = (callback: (token: string) => void) => {
    refreshSubscribers.push(callback);
};

const onTokenRefreshed = (token: string) => {
    refreshSubscribers.forEach((callback) => callback(token));
    refreshSubscribers = [];
};

// Interceptor de REQUEST - adiciona token
api.interceptors.request.use(
    async (config) => {
        // Ignora endpoints de auth (exceto /me)
        const isAuthEndpoint = config.url?.includes('/auth/') && !config.url?.includes('/auth/me');

        if (!isAuthEndpoint) {
            const token = tokenUtils.getAccessToken();
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }

        return config;
    },
    (error) => Promise.reject(error)
);

// Interceptor de RESPONSE - trata 401 e faz refresh
api.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config as InternalConfig & { _retry?: boolean };

        // Se for 401 e não for retry
        if (error.response?.status === 401 && !originalRequest._retry) {
            // Ignora se for endpoint de auth
            if (originalRequest.url?.includes('/auth/signin') ||
                originalRequest.url?.includes('/auth/signup')) {
                return Promise.reject(error);
            }

            if (isRefreshing) {
                // Aguarda o refresh em andamento
                return new Promise((resolve) => {
                    subscribeTokenRefresh((token: string) => {
                        originalRequest.headers.Authorization = `Bearer ${token}`;
                        resolve(api(originalRequest));
                    });
                });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            const refreshToken = tokenUtils.getRefreshToken();

            if (!refreshToken) {
                tokenUtils.clearTokens();
                window.location.href = '/app';
                return Promise.reject(error);
            }

            try {
                const response = await axios.post(`${API_URL}/auth/refresh`, {
                    refresh_token: refreshToken,
                });

                const { access_token, refresh_token, expires_in } = response.data;
                tokenUtils.saveTokens(access_token, refresh_token, expires_in);

                isRefreshing = false;
                onTokenRefreshed(access_token);

                originalRequest.headers.Authorization = `Bearer ${access_token}`;
                return api(originalRequest);
            } catch (refreshError) {
                isRefreshing = false;
                tokenUtils.clearTokens();
                window.location.href = '/app';
                return Promise.reject(refreshError);
            }
        }

        // Extrai mensagem de erro do backend
        const message = (error.response?.data as any)?.detail || error.message || 'Erro desconhecido';
        const enhancedError = new Error(message) as Error & { status?: number };
        enhancedError.status = error.response?.status;

        return Promise.reject(enhancedError);
    }
);

export default api;

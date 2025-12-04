/**
 * AuthContext - Gerencia autenticação da aplicação
 */

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { authApi } from '../api/auth';
import { tokenUtils } from '../api/client';
import type { Usuario, PerfilTipo, SignUpRequest } from '../api/types';

interface AuthContextType {
    usuario: Usuario | null;
    perfisDisponiveis: PerfilTipo[];
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    signup: (data: SignUpRequest) => Promise<void>;
    logout: () => void;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [usuario, setUsuario] = useState<Usuario | null>(null);
    const [perfisDisponiveis, setPerfisDisponiveis] = useState<PerfilTipo[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    // Busca dados do usuário logado
    const fetchUser = useCallback(async (): Promise<Usuario | null> => {
        try {
            const user = await authApi.me();
            return user;
        } catch {
            return null;
        }
    }, []);

    // Refresh dos dados do usuário
    const refreshUser = useCallback(async () => {
        const user = await fetchUser();
        if (user) {
            setUsuario(user);
            // Combina perfis do usuário + detectados
            const allPerfis = [...new Set([...user.perfis])];
            setPerfisDisponiveis(allPerfis);
        }
    }, [fetchUser]);

    // Limpa completamente o estado de autenticação
    const clearAuthState = useCallback(() => {
        tokenUtils.clearTokens();
        localStorage.removeItem('plataforma_gd_perfil_ativo');
        setUsuario(null);
        setPerfisDisponiveis([]);
    }, []);

    // Login
    const login = useCallback(async (email: string, password: string) => {
        try {
            // Limpa estado anterior antes de tentar login
            clearAuthState();

            const response = await authApi.signin({ email, password });

            // Salva tokens
            tokenUtils.saveTokens(
                response.tokens.access_token,
                response.tokens.refresh_token,
                response.tokens.expires_in
            );

            // Atualiza estado
            setUsuario(response.user);
            setPerfisDisponiveis(response.perfis_disponiveis);
        } catch (error) {
            // Garante limpeza em caso de erro
            clearAuthState();
            throw error;
        }
    }, [clearAuthState]);

    // Signup
    const signup = useCallback(async (data: SignUpRequest) => {
        try {
            // Limpa estado anterior antes de tentar signup
            clearAuthState();

            const response = await authApi.signup(data);

            // Salva tokens
            tokenUtils.saveTokens(
                response.tokens.access_token,
                response.tokens.refresh_token,
                response.tokens.expires_in
            );

            // Atualiza estado
            setUsuario(response.user);
            setPerfisDisponiveis(response.user.perfis);
        } catch (error) {
            // Garante limpeza em caso de erro
            clearAuthState();
            throw error;
        }
    }, [clearAuthState]);

    // Logout
    const logout = useCallback(() => {
        // Tenta logout no servidor (não crítico)
        authApi.logout().catch(() => {});

        // Limpa completamente o estado
        clearAuthState();
    }, [clearAuthState]);

    // Inicialização - verifica token salvo
    useEffect(() => {
        const initAuth = async () => {
            try {
                const token = tokenUtils.getAccessToken();

                if (token) {
                    const user = await fetchUser();

                    if (user) {
                        setUsuario(user);
                        setPerfisDisponiveis(user.perfis);
                    } else {
                        // Token inválido - limpa tudo
                        clearAuthState();
                    }
                }
            } catch (error) {
                // Erro na inicialização - limpa estado para evitar loops
                console.error('Erro ao inicializar autenticação:', error);
                clearAuthState();
            } finally {
                setIsLoading(false);
            }
        };

        initAuth();
    }, [fetchUser, clearAuthState]);

    const value: AuthContextType = {
        usuario,
        perfisDisponiveis,
        isAuthenticated: !!usuario,
        isLoading,
        login,
        signup,
        logout,
        refreshUser,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth deve ser usado dentro de AuthProvider');
    }
    return context;
}

export default AuthContext;

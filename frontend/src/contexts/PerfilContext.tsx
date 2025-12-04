/**
 * PerfilContext - Gerencia o perfil ativo do usuário
 * Permite que o usuário alterne entre seus diferentes papéis (gestor, beneficiário, etc.)
 */

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import type { PerfilTipo } from '../api/types';

interface PerfilContextType {
    perfilAtivo: PerfilTipo | null;
    perfisDisponiveis: PerfilTipo[];
    trocarPerfil: (perfil: PerfilTipo) => void;
    getPrioridade: (perfil: PerfilTipo) => number;
}

const PerfilContext = createContext<PerfilContextType | null>(null);

// Prioridade dos perfis (maior = mais importante)
const PERFIL_PRIORIDADE: Record<PerfilTipo, number> = {
    superadmin: 100,
    proprietario: 80,
    gestor: 60,
    beneficiario: 40,
    parceiro: 30,
    usuario: 20,
};

// Labels dos perfis para exibição
export const PERFIL_LABELS: Record<PerfilTipo, string> = {
    superadmin: 'Administrador',
    proprietario: 'Proprietário',
    gestor: 'Gestor',
    beneficiario: 'Beneficiário',
    parceiro: 'Parceiro',
    usuario: 'Usuário',
};

// Ícones dos perfis (lucide-react)
export const PERFIL_ICONS: Record<PerfilTipo, string> = {
    superadmin: 'Shield',
    proprietario: 'Building2',
    gestor: 'Users',
    beneficiario: 'Zap',
    parceiro: 'Handshake',
    usuario: 'User',
};

// Cores dos perfis
export const PERFIL_CORES: Record<PerfilTipo, string> = {
    superadmin: 'red',
    proprietario: 'purple',
    gestor: 'blue',
    beneficiario: 'green',
    parceiro: 'orange',
    usuario: 'gray',
};

const PERFIL_ATIVO_KEY = 'plataforma_gd_perfil_ativo';

export function PerfilProvider({ children }: { children: ReactNode }) {
    const { usuario, perfisDisponiveis: perfisAuth, isAuthenticated } = useAuth();
    const [perfilAtivo, setPerfilAtivo] = useState<PerfilTipo | null>(null);

    // Obtém prioridade do perfil
    const getPrioridade = useCallback((perfil: PerfilTipo): number => {
        return PERFIL_PRIORIDADE[perfil] || 0;
    }, []);

    // Determina perfil padrão (maior prioridade)
    const getPerfilPadrao = useCallback((perfis: PerfilTipo[]): PerfilTipo | null => {
        if (!perfis.length) return null;

        return perfis.reduce((maior, atual) => {
            return getPrioridade(atual) > getPrioridade(maior) ? atual : maior;
        }, perfis[0]);
    }, [getPrioridade]);

    // Troca o perfil ativo
    const trocarPerfil = useCallback((perfil: PerfilTipo) => {
        if (perfisAuth.includes(perfil)) {
            setPerfilAtivo(perfil);
            localStorage.setItem(PERFIL_ATIVO_KEY, perfil);
        }
    }, [perfisAuth]);

    // Inicializa perfil ativo
    useEffect(() => {
        if (!isAuthenticated || !perfisAuth.length) {
            setPerfilAtivo(null);
            return;
        }

        // Tenta recuperar perfil salvo
        const perfilSalvo = localStorage.getItem(PERFIL_ATIVO_KEY) as PerfilTipo | null;

        if (perfilSalvo && perfisAuth.includes(perfilSalvo)) {
            setPerfilAtivo(perfilSalvo);
        } else {
            // Usa perfil de maior prioridade
            const perfilPadrao = getPerfilPadrao(perfisAuth);
            if (perfilPadrao) {
                setPerfilAtivo(perfilPadrao);
                localStorage.setItem(PERFIL_ATIVO_KEY, perfilPadrao);
            }
        }
    }, [isAuthenticated, perfisAuth, getPerfilPadrao]);

    // Limpa perfil ao deslogar
    useEffect(() => {
        if (!isAuthenticated) {
            localStorage.removeItem(PERFIL_ATIVO_KEY);
        }
    }, [isAuthenticated]);

    const value: PerfilContextType = {
        perfilAtivo,
        perfisDisponiveis: perfisAuth,
        trocarPerfil,
        getPrioridade,
    };

    return (
        <PerfilContext.Provider value={value}>
            {children}
        </PerfilContext.Provider>
    );
}

export function usePerfil() {
    const context = useContext(PerfilContext);
    if (!context) {
        throw new Error('usePerfil deve ser usado dentro de PerfilProvider');
    }
    return context;
}

export default PerfilContext;

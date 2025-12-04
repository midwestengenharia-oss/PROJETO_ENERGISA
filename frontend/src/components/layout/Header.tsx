/**
 * Header - Cabeçalho da aplicação
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Bell,
    Sun,
    Moon,
    LogOut,
    User,
    Settings,
    ChevronDown,
    Check,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { usePerfil, PERFIL_LABELS, PERFIL_CORES } from '../../contexts/PerfilContext';
import { useTheme } from '../../contexts/ThemeContext';
import type { PerfilTipo } from '../../api/types';

interface HeaderProps {
    sidebarCollapsed: boolean;
}

export function Header({ sidebarCollapsed }: HeaderProps) {
    const navigate = useNavigate();
    const { usuario, logout } = useAuth();
    const { perfilAtivo, perfisDisponiveis, trocarPerfil } = usePerfil();
    const { isDark, toggleTheme } = useTheme();

    const [showUserMenu, setShowUserMenu] = useState(false);
    const [showPerfilMenu, setShowPerfilMenu] = useState(false);
    const [showNotifications, setShowNotifications] = useState(false);

    const handleLogout = () => {
        logout();
        navigate('/app');
    };

    return (
        <header
            className={`
                fixed top-0 right-0 z-30 h-16
                bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700
                transition-all duration-300 ease-in-out
                ${sidebarCollapsed ? 'left-16' : 'left-64'}
            `}
        >
            <div className="h-full px-4 flex items-center justify-between">
                {/* Título da página / Breadcrumb */}
                <div>
                    {/* Pode ser preenchido com breadcrumb ou título */}
                </div>

                {/* Ações */}
                <div className="flex items-center gap-2">
                    {/* Seletor de Perfil (se tiver múltiplos) */}
                    {perfisDisponiveis.length > 1 && (
                        <div className="relative">
                            <button
                                onClick={() => setShowPerfilMenu(!showPerfilMenu)}
                                className={`
                                    flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium
                                    bg-${perfilAtivo ? PERFIL_CORES[perfilAtivo] : 'slate'}-100
                                    text-${perfilAtivo ? PERFIL_CORES[perfilAtivo] : 'slate'}-700
                                    dark:bg-${perfilAtivo ? PERFIL_CORES[perfilAtivo] : 'slate'}-900/30
                                    dark:text-${perfilAtivo ? PERFIL_CORES[perfilAtivo] : 'slate'}-400
                                    hover:opacity-80 transition-opacity
                                `}
                            >
                                <span>{perfilAtivo ? PERFIL_LABELS[perfilAtivo] : 'Selecionar'}</span>
                                <ChevronDown size={16} />
                            </button>

                            {showPerfilMenu && (
                                <>
                                    <div
                                        className="fixed inset-0 z-40"
                                        onClick={() => setShowPerfilMenu(false)}
                                    />
                                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 z-50">
                                        <div className="p-2">
                                            <p className="px-2 py-1 text-xs text-slate-500 dark:text-slate-400">
                                                Trocar perfil
                                            </p>
                                            {perfisDisponiveis.map((perfil) => (
                                                <button
                                                    key={perfil}
                                                    onClick={() => {
                                                        trocarPerfil(perfil);
                                                        setShowPerfilMenu(false);
                                                        navigate(`/app/${perfil}`);
                                                    }}
                                                    className={`
                                                        w-full flex items-center justify-between px-2 py-2 rounded-lg text-sm
                                                        ${perfilAtivo === perfil
                                                            ? 'bg-[#00A3E0] text-white'
                                                            : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                                                        }
                                                    `}
                                                >
                                                    <span>{PERFIL_LABELS[perfil]}</span>
                                                    {perfilAtivo === perfil && <Check size={16} />}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    )}

                    {/* Toggle Tema */}
                    <button
                        onClick={toggleTheme}
                        className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                        title={isDark ? 'Modo claro' : 'Modo escuro'}
                    >
                        {isDark ? <Sun size={20} /> : <Moon size={20} />}
                    </button>

                    {/* Notificações */}
                    <div className="relative">
                        <button
                            onClick={() => setShowNotifications(!showNotifications)}
                            className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 relative"
                        >
                            <Bell size={20} />
                            {/* Badge de notificações */}
                            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
                        </button>

                        {showNotifications && (
                            <>
                                <div
                                    className="fixed inset-0 z-40"
                                    onClick={() => setShowNotifications(false)}
                                />
                                <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 z-50">
                                    <div className="p-4">
                                        <h3 className="font-semibold text-slate-900 dark:text-white mb-4">
                                            Notificações
                                        </h3>
                                        <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-8">
                                            Nenhuma notificação
                                        </p>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>

                    {/* Menu do Usuário */}
                    <div className="relative">
                        <button
                            onClick={() => setShowUserMenu(!showUserMenu)}
                            className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
                        >
                            <div className="w-8 h-8 bg-[#00A3E0] rounded-full flex items-center justify-center text-white font-medium">
                                {usuario?.nome_completo?.charAt(0).toUpperCase() || 'U'}
                            </div>
                            <ChevronDown size={16} className="text-slate-500" />
                        </button>

                        {showUserMenu && (
                            <>
                                <div
                                    className="fixed inset-0 z-40"
                                    onClick={() => setShowUserMenu(false)}
                                />
                                <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 z-50">
                                    <div className="p-3 border-b border-slate-200 dark:border-slate-700">
                                        <p className="font-medium text-slate-900 dark:text-white truncate">
                                            {usuario?.nome_completo}
                                        </p>
                                        <p className="text-sm text-slate-500 dark:text-slate-400 truncate">
                                            {usuario?.email}
                                        </p>
                                    </div>
                                    <div className="p-2">
                                        <button
                                            onClick={() => {
                                                setShowUserMenu(false);
                                                navigate('/app/perfil');
                                            }}
                                            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700"
                                        >
                                            <User size={16} />
                                            <span>Meu Perfil</span>
                                        </button>
                                        <button
                                            onClick={() => {
                                                setShowUserMenu(false);
                                                navigate('/app/configuracoes');
                                            }}
                                            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700"
                                        >
                                            <Settings size={16} />
                                            <span>Configurações</span>
                                        </button>
                                        <hr className="my-2 border-slate-200 dark:border-slate-700" />
                                        <button
                                            onClick={handleLogout}
                                            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                                        >
                                            <LogOut size={16} />
                                            <span>Sair</span>
                                        </button>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}

export default Header;

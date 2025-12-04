/**
 * MainLayout - Layout principal da aplicação autenticada
 */

import { useState } from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { usePerfil } from '../contexts/PerfilContext';
import { Sidebar } from '../components/layout/Sidebar';
import { Header } from '../components/layout/Header';
import { Loader2, Zap } from 'lucide-react';

export function MainLayout() {
    const { isAuthenticated, isLoading } = useAuth();
    const { perfilAtivo } = usePerfil();
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

    // Loading
    if (isLoading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-900">
                <div className="w-16 h-16 bg-[#00A3E0] rounded-2xl flex items-center justify-center mb-4">
                    <Zap className="text-white" size={32} />
                </div>
                <Loader2 className="animate-spin text-[#00A3E0]" size={32} />
            </div>
        );
    }

    // Não autenticado
    if (!isAuthenticated) {
        return <Navigate to="/app" replace />;
    }

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
            {/* Sidebar */}
            <Sidebar
                isCollapsed={sidebarCollapsed}
                onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
            />

            {/* Header */}
            <Header sidebarCollapsed={sidebarCollapsed} />

            {/* Main Content */}
            <main
                className={`
                    pt-16 min-h-screen
                    transition-all duration-300 ease-in-out
                    ${sidebarCollapsed ? 'pl-16' : 'pl-64'}
                `}
            >
                <div className="p-6">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}

export default MainLayout;

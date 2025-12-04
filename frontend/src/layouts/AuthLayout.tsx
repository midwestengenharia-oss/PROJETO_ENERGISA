/**
 * AuthLayout - Layout para páginas de autenticação (SignIn/SignUp)
 */

import { Outlet } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { Zap, Loader2 } from 'lucide-react';

interface AuthLayoutProps {
    showLoading?: boolean;
}

export function AuthLayout({ showLoading = false }: AuthLayoutProps) {
    const { isDark } = useTheme();

    // Loading
    if (showLoading) {
        return (
            <div className={`min-h-screen flex flex-col items-center justify-center ${isDark ? 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900' : 'bg-gradient-to-br from-slate-100 via-white to-slate-100'}`}>
                <div className="w-16 h-16 bg-[#00A3E0] rounded-2xl flex items-center justify-center mb-4">
                    <Zap className="text-white" size={32} />
                </div>
                <Loader2 className="animate-spin text-[#00A3E0]" size={32} />
            </div>
        );
    }

    // Renderiza as páginas de auth (login/cadastro)
    return <Outlet />;
}

export default AuthLayout;

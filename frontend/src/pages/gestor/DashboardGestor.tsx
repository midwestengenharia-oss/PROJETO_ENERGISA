/**
 * DashboardGestor - Dashboard do Gestor de Usinas
 */

import { useAuth } from '../../contexts/AuthContext';
import {
    Building2,
    Users,
    FileText,
    PieChart,
    Zap,
    TrendingUp,
    AlertCircle
} from 'lucide-react';

export function DashboardGestor() {
    const { usuario } = useAuth();

    const stats = [
        { label: 'Usinas Gerenciadas', value: 2, icon: Building2, color: 'blue' },
        { label: 'Beneficiários', value: 45, icon: Users, color: 'green' },
        { label: 'Cobranças Pendentes', value: 12, icon: FileText, color: 'orange' },
        { label: 'Energia Distribuída', value: '89 MWh', icon: Zap, color: 'yellow' },
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Dashboard do Gestor
                </h1>
                <p className="text-slate-500 dark:text-slate-400">
                    Bem-vindo, {usuario?.nome_completo?.split(' ')[0]}!
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((stat) => (
                    <div
                        key={stat.label}
                        className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700"
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500 dark:text-slate-400">{stat.label}</p>
                                <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                                    {stat.value}
                                </p>
                            </div>
                            <div className={`w-12 h-12 bg-${stat.color}-100 dark:bg-${stat.color}-900/30 rounded-xl flex items-center justify-center`}>
                                <stat.icon className={`text-${stat.color}-600 dark:text-${stat.color}-400`} size={24} />
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Grid de conteúdo */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Rateio de Energia */}
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                    <div className="p-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
                        <h2 className="font-semibold text-slate-900 dark:text-white">Rateio Mensal</h2>
                        <PieChart className="text-slate-400" size={20} />
                    </div>
                    <div className="p-4">
                        <div className="space-y-3">
                            {[
                                { uc: 'UC 001', nome: 'Residência João', percent: 15, kwh: 450 },
                                { uc: 'UC 002', nome: 'Comércio Maria', percent: 25, kwh: 750 },
                                { uc: 'UC 003', nome: 'Indústria XYZ', percent: 40, kwh: 1200 },
                                { uc: 'UC 004', nome: 'Outros', percent: 20, kwh: 600 },
                            ].map((item, idx) => (
                                <div key={idx} className="space-y-1">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-600 dark:text-slate-300">{item.nome}</span>
                                        <span className="font-medium text-slate-900 dark:text-white">{item.kwh} kWh</span>
                                    </div>
                                    <div className="h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-[#00A3E0] rounded-full"
                                            style={{ width: `${item.percent}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Cobranças Pendentes */}
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                    <div className="p-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
                        <h2 className="font-semibold text-slate-900 dark:text-white">Cobranças Pendentes</h2>
                        <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded-full text-xs font-medium">
                            12 pendentes
                        </span>
                    </div>
                    <div className="p-4 space-y-3">
                        {[
                            { nome: 'Carlos Silva', valor: 'R$ 245,00', vencimento: '10/12', status: 'vencida' },
                            { nome: 'Ana Santos', valor: 'R$ 180,00', vencimento: '15/12', status: 'pendente' },
                            { nome: 'Pedro Oliveira', valor: 'R$ 320,00', vencimento: '20/12', status: 'pendente' },
                        ].map((cobranca, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
                                <div>
                                    <p className="font-medium text-slate-900 dark:text-white">{cobranca.nome}</p>
                                    <p className="text-xs text-slate-500">Vence: {cobranca.vencimento}</p>
                                </div>
                                <div className="text-right">
                                    <p className="font-medium text-slate-900 dark:text-white">{cobranca.valor}</p>
                                    <span className={`text-xs ${
                                        cobranca.status === 'vencida' ? 'text-red-500' : 'text-yellow-500'
                                    }`}>
                                        {cobranca.status}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default DashboardGestor;

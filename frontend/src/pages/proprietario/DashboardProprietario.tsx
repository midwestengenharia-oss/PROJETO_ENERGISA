/**
 * DashboardProprietario - Dashboard do Proprietário de Usinas
 */

import { useAuth } from '../../contexts/AuthContext';
import {
    Building2,
    Users,
    Wallet,
    Zap,
    TrendingUp,
    FileSignature
} from 'lucide-react';

export function DashboardProprietario() {
    const { usuario } = useAuth();

    const stats = [
        { label: 'Minhas Usinas', value: 3, icon: Building2, color: 'purple' },
        { label: 'Gestores Vinculados', value: 5, icon: Users, color: 'blue' },
        { label: 'Receita Mensal', value: 'R$ 45.230', icon: Wallet, color: 'green' },
        { label: 'Energia Gerada', value: '125 MWh', icon: Zap, color: 'yellow' },
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Dashboard do Proprietário
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

            {/* Usinas Overview */}
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                    <h2 className="font-semibold text-slate-900 dark:text-white">Minhas Usinas</h2>
                </div>
                <div className="p-4">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="text-left text-sm text-slate-500 dark:text-slate-400">
                                    <th className="pb-3 font-medium">Usina</th>
                                    <th className="pb-3 font-medium">Capacidade</th>
                                    <th className="pb-3 font-medium">Geração Mensal</th>
                                    <th className="pb-3 font-medium">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                                {[
                                    { nome: 'Solar Norte', capacidade: '500 kWp', geracao: '45 MWh', status: 'ativa' },
                                    { nome: 'Solar Sul', capacidade: '350 kWp', geracao: '32 MWh', status: 'ativa' },
                                    { nome: 'Solar Leste', capacidade: '400 kWp', geracao: '48 MWh', status: 'manutencao' },
                                ].map((usina, idx) => (
                                    <tr key={idx} className="text-sm">
                                        <td className="py-3">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                                                    <Building2 className="text-purple-600 dark:text-purple-400" size={16} />
                                                </div>
                                                <span className="font-medium text-slate-900 dark:text-white">{usina.nome}</span>
                                            </div>
                                        </td>
                                        <td className="py-3 text-slate-600 dark:text-slate-300">{usina.capacidade}</td>
                                        <td className="py-3 text-slate-600 dark:text-slate-300">{usina.geracao}</td>
                                        <td className="py-3">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                                usina.status === 'ativa'
                                                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                                    : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                                            }`}>
                                                {usina.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default DashboardProprietario;

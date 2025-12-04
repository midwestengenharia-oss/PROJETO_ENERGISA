/**
 * DashboardAdmin - Dashboard do Super Administrador
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import {
    Users,
    Building2,
    Target,
    Wallet,
    TrendingUp,
    AlertCircle,
    CheckCircle,
    Clock
} from 'lucide-react';

interface StatsCard {
    label: string;
    value: string | number;
    icon: React.ElementType;
    color: string;
    change?: string;
}

export function DashboardAdmin() {
    const { usuario } = useAuth();

    const stats: StatsCard[] = [
        { label: 'Usuários Ativos', value: 1248, icon: Users, color: 'blue', change: '+12%' },
        { label: 'Usinas Cadastradas', value: 87, icon: Building2, color: 'green', change: '+5%' },
        { label: 'Leads Este Mês', value: 324, icon: Target, color: 'purple', change: '+28%' },
        { label: 'Saques Pendentes', value: 15, icon: Wallet, color: 'orange' },
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Dashboard Administrativo
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
                                {stat.change && (
                                    <p className="text-sm text-green-500 mt-1 flex items-center gap-1">
                                        <TrendingUp size={14} />
                                        {stat.change}
                                    </p>
                                )}
                            </div>
                            <div className={`w-12 h-12 bg-${stat.color}-100 dark:bg-${stat.color}-900/30 rounded-xl flex items-center justify-center`}>
                                <stat.icon className={`text-${stat.color}-600 dark:text-${stat.color}-400`} size={24} />
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Últimos Leads */}
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                    <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                        <h2 className="font-semibold text-slate-900 dark:text-white">Últimos Leads</h2>
                    </div>
                    <div className="p-4 space-y-3">
                        {[
                            { nome: 'João Silva', status: 'novo', tempo: '5 min' },
                            { nome: 'Maria Santos', status: 'contato', tempo: '1h' },
                            { nome: 'Carlos Oliveira', status: 'convertido', tempo: '2h' },
                        ].map((lead, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-[#00A3E0] rounded-full flex items-center justify-center text-white font-medium">
                                        {lead.nome.charAt(0)}
                                    </div>
                                    <div>
                                        <p className="font-medium text-slate-900 dark:text-white">{lead.nome}</p>
                                        <p className="text-xs text-slate-500">{lead.tempo} atrás</p>
                                    </div>
                                </div>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                    lead.status === 'novo' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                                    lead.status === 'contato' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                                    'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                }`}>
                                    {lead.status}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Alertas do Sistema */}
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                    <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                        <h2 className="font-semibold text-slate-900 dark:text-white">Alertas do Sistema</h2>
                    </div>
                    <div className="p-4 space-y-3">
                        {[
                            { msg: '15 saques aguardando aprovação', tipo: 'warning', icon: Clock },
                            { msg: '3 usinas com documentação pendente', tipo: 'error', icon: AlertCircle },
                            { msg: 'Backup realizado com sucesso', tipo: 'success', icon: CheckCircle },
                        ].map((alerta, idx) => (
                            <div key={idx} className={`flex items-center gap-3 p-3 rounded-lg ${
                                alerta.tipo === 'warning' ? 'bg-yellow-50 dark:bg-yellow-900/20' :
                                alerta.tipo === 'error' ? 'bg-red-50 dark:bg-red-900/20' :
                                'bg-green-50 dark:bg-green-900/20'
                            }`}>
                                <alerta.icon className={`${
                                    alerta.tipo === 'warning' ? 'text-yellow-600' :
                                    alerta.tipo === 'error' ? 'text-red-600' :
                                    'text-green-600'
                                }`} size={20} />
                                <span className={`text-sm ${
                                    alerta.tipo === 'warning' ? 'text-yellow-800 dark:text-yellow-300' :
                                    alerta.tipo === 'error' ? 'text-red-800 dark:text-red-300' :
                                    'text-green-800 dark:text-green-300'
                                }`}>
                                    {alerta.msg}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default DashboardAdmin;

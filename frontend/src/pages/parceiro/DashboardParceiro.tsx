/**
 * DashboardParceiro - Dashboard do Parceiro Comercial
 */

import { useAuth } from '../../contexts/AuthContext';
import {
    Target,
    Package,
    Wallet,
    TrendingUp,
    Users,
    CheckCircle
} from 'lucide-react';

export function DashboardParceiro() {
    const { usuario } = useAuth();

    const stats = [
        { label: 'Leads Este Mês', value: 24, icon: Target, color: 'purple' },
        { label: 'Projetos Ativos', value: 8, icon: Package, color: 'blue' },
        { label: 'Comissões Pendentes', value: 'R$ 3.450', icon: Wallet, color: 'green' },
        { label: 'Taxa de Conversão', value: '32%', icon: TrendingUp, color: 'yellow' },
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Portal do Parceiro
                </h1>
                <p className="text-slate-500 dark:text-slate-400">
                    Olá, {usuario?.nome_completo?.split(' ')[0]}! Acompanhe suas vendas e comissões.
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
                {/* Últimos Leads */}
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                    <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                        <h2 className="font-semibold text-slate-900 dark:text-white">Últimos Leads</h2>
                    </div>
                    <div className="p-4 space-y-3">
                        {[
                            { nome: 'Empresa ABC', valor: 'R$ 850/mês', status: 'novo', tempo: '2h' },
                            { nome: 'João Silva', valor: 'R$ 280/mês', status: 'contato', tempo: '1d' },
                            { nome: 'Condomínio XYZ', valor: 'R$ 2.500/mês', status: 'proposta', tempo: '3d' },
                        ].map((lead, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
                                        <Target className="text-purple-600 dark:text-purple-400" size={18} />
                                    </div>
                                    <div>
                                        <p className="font-medium text-slate-900 dark:text-white">{lead.nome}</p>
                                        <p className="text-xs text-slate-500">{lead.valor} • {lead.tempo} atrás</p>
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

                {/* Comissões */}
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                    <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                        <h2 className="font-semibold text-slate-900 dark:text-white">Comissões Recentes</h2>
                    </div>
                    <div className="p-4 space-y-3">
                        {[
                            { projeto: 'Projeto Solar Residencial', valor: 'R$ 1.200', status: 'pago' },
                            { projeto: 'Projeto Comercial ABC', valor: 'R$ 2.250', status: 'pendente' },
                        ].map((comissao, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                                        comissao.status === 'pago'
                                            ? 'bg-green-100 dark:bg-green-900/30'
                                            : 'bg-yellow-100 dark:bg-yellow-900/30'
                                    }`}>
                                        {comissao.status === 'pago'
                                            ? <CheckCircle className="text-green-600 dark:text-green-400" size={18} />
                                            : <Wallet className="text-yellow-600 dark:text-yellow-400" size={18} />
                                        }
                                    </div>
                                    <div>
                                        <p className="font-medium text-slate-900 dark:text-white">{comissao.projeto}</p>
                                        <p className="text-xs text-slate-500">{comissao.status}</p>
                                    </div>
                                </div>
                                <span className="font-bold text-slate-900 dark:text-white">{comissao.valor}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Meta do Mês */}
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="font-semibold text-slate-900 dark:text-white">Meta do Mês</h2>
                    <span className="text-sm text-slate-500">24 de 30 leads</span>
                </div>
                <div className="h-4 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-[#00A3E0] to-[#00D4FF] rounded-full"
                        style={{ width: '80%' }}
                    />
                </div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                    Faltam apenas <span className="font-bold text-[#00A3E0]">6 leads</span> para atingir sua meta!
                </p>
            </div>
        </div>
    );
}

export default DashboardParceiro;

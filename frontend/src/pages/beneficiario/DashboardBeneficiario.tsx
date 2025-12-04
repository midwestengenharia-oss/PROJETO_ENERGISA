/**
 * DashboardBeneficiario - Dashboard do Beneficiário
 */

import { useAuth } from '../../contexts/AuthContext';
import {
    Zap,
    TrendingDown,
    Wallet,
    FileSignature,
    Leaf,
    Calendar
} from 'lucide-react';

export function DashboardBeneficiario() {
    const { usuario } = useAuth();

    const stats = [
        { label: 'Créditos Disponíveis', value: '450 kWh', icon: Zap, color: 'green' },
        { label: 'Economia Este Mês', value: 'R$ 285', icon: TrendingDown, color: 'blue' },
        { label: 'Próximo Pagamento', value: 'R$ 180', icon: Wallet, color: 'orange' },
        { label: 'CO² Evitado', value: '125 kg', icon: Leaf, color: 'emerald' },
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Meus Créditos de Energia
                </h1>
                <p className="text-slate-500 dark:text-slate-400">
                    Olá, {usuario?.nome_completo?.split(' ')[0]}! Veja sua economia com energia solar.
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

            {/* Gráfico de Economia */}
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                    <h2 className="font-semibold text-slate-900 dark:text-white">Economia nos Últimos 6 Meses</h2>
                </div>
                <div className="p-4">
                    <div className="flex items-end justify-between h-48 gap-2">
                        {[
                            { mes: 'Jul', valor: 180 },
                            { mes: 'Ago', valor: 220 },
                            { mes: 'Set', valor: 195 },
                            { mes: 'Out', valor: 240 },
                            { mes: 'Nov', valor: 260 },
                            { mes: 'Dez', valor: 285 },
                        ].map((item) => (
                            <div key={item.mes} className="flex-1 flex flex-col items-center gap-2">
                                <div
                                    className="w-full bg-gradient-to-t from-[#00A3E0] to-[#00D4FF] rounded-t-lg"
                                    style={{ height: `${(item.valor / 300) * 100}%` }}
                                />
                                <span className="text-xs text-slate-500 dark:text-slate-400">{item.mes}</span>
                            </div>
                        ))}
                    </div>
                    <div className="mt-4 text-center">
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                            Total economizado: <span className="font-bold text-green-500">R$ 1.380,00</span>
                        </p>
                    </div>
                </div>
            </div>

            {/* Info Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Próximo Vencimento */}
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-xl flex items-center justify-center">
                            <Calendar className="text-orange-600 dark:text-orange-400" size={24} />
                        </div>
                        <div>
                            <p className="text-sm text-slate-500 dark:text-slate-400">Próximo Vencimento</p>
                            <p className="text-xl font-bold text-slate-900 dark:text-white">15/12/2024</p>
                            <p className="text-sm text-slate-600 dark:text-slate-300">Valor: R$ 180,00</p>
                        </div>
                    </div>
                </div>

                {/* Contrato */}
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
                            <FileSignature className="text-blue-600 dark:text-blue-400" size={24} />
                        </div>
                        <div>
                            <p className="text-sm text-slate-500 dark:text-slate-400">Meu Contrato</p>
                            <p className="text-xl font-bold text-slate-900 dark:text-white">Ativo</p>
                            <p className="text-sm text-slate-600 dark:text-slate-300">Válido até: 12/2025</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default DashboardBeneficiario;

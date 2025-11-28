import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../components/Toast';
import { Loader2, Mail, Lock, Zap, Moon, SunMedium, Shield, Phone, CheckCircle2 } from 'lucide-react';
import { api } from '../lib/api';
import axios from 'axios';

// Gateway API
const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:3000';
const gatewayApi = axios.create({
    baseURL: GATEWAY_URL,
});

interface PhoneOption {
    codigoEmpresaWeb: number;
    cdc: number;
    digitoVerificador: number;
    posicao: number;
    celular: string;
}

interface SignInProps {
    onSwitchToSignUp: () => void;
}

type LoginMethod = 'email' | 'energisa';
type EnergisaStep = 'cpf' | 'phone' | 'sms';

export function SignIn({ onSwitchToSignUp }: SignInProps) {
    const { login } = useAuth();
    const { isDark, toggleTheme } = useTheme();
    const toast = useToast();

    // Login method selection
    const [loginMethod, setLoginMethod] = useState<LoginMethod>('email');

    // Email/Password login
    const [email, setEmail] = useState('');
    const [senha, setSenha] = useState('');
    const [loading, setLoading] = useState(false);

    // Energisa login
    const [energisaStep, setEnergisaStep] = useState<EnergisaStep>('cpf');
    const [cpf, setCpf] = useState('');
    const [transactionId, setTransactionId] = useState('');
    const [listaTelefone, setListaTelefone] = useState<PhoneOption[]>([]);
    const [selectedPhone, setSelectedPhone] = useState<PhoneOption | null>(null);
    const [smsCode, setSmsCode] = useState('');
    const [energisaLoading, setEnergisaLoading] = useState(false);

    // Format CPF
    const formatCPF = (value: string) => {
        const numbers = value.replace(/\D/g, '');
        if (numbers.length <= 11) {
            return numbers
                .replace(/(\d{3})(\d)/, '$1.$2')
                .replace(/(\d{3})(\d)/, '$1.$2')
                .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
        }
        return numbers.slice(0, 11);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!email || !senha) {
            toast.warning('Preencha todos os campos');
            return;
        }

        setLoading(true);
        try {
            await login(email, senha);
            toast.success('Login realizado com sucesso!');
        } catch (err: any) {
            toast.error(err.message || 'Email ou senha incorretos');
        } finally {
            setLoading(false);
        }
    };

    // Energisa Flow - Step 1: Submit CPF
    const handleEnergisaCpf = async () => {
        const cpfNumbers = cpf.replace(/\D/g, '');

        if (cpfNumbers.length !== 11) {
            toast.error('CPF inválido. Digite um CPF válido.');
            return;
        }

        setEnergisaLoading(true);
        try {
            const response = await gatewayApi.post('/auth/login/start', {
                cpf: cpfNumbers
            });

            if (response.data.transaction_id && response.data.listaTelefone) {
                setTransactionId(response.data.transaction_id);
                setListaTelefone(response.data.listaTelefone);
                setEnergisaStep('phone');
                toast.success('CPF encontrado! Selecione um telefone.');
            }
        } catch (error: any) {
            toast.error(error.response?.data?.message || 'CPF não encontrado');
        } finally {
            setEnergisaLoading(false);
        }
    };

    // Energisa Flow - Step 2: Send SMS to selected phone
    const handleEnergisaPhone = async () => {
        if (!selectedPhone) {
            toast.error('Selecione um telefone.');
            return;
        }

        setEnergisaLoading(true);
        try {
            const response = await gatewayApi.post('/auth/login/send-sms', {
                transactionId,
                cdc: selectedPhone.cdc,
                digitoVerificador: selectedPhone.digitoVerificador,
                posicao: selectedPhone.posicao
            });

            if (response.data.success) {
                setEnergisaStep('sms');
                toast.success(`SMS enviado para ${selectedPhone.celular}!`);
            }
        } catch (error: any) {
            toast.error(error.message || 'Erro ao enviar SMS');
        } finally {
            setEnergisaLoading(false);
        }
    };

    // Energisa Flow - Step 3: Validate SMS and login
    const handleEnergisaSms = async () => {
        if (smsCode.length < 4) {
            toast.error('Código inválido. Digite o código recebido por SMS.');
            return;
        }

        setEnergisaLoading(true);
        try {
            const response = await gatewayApi.post('/auth/login/validate-sms', {
                transactionId,
                codigo: smsCode
            });

            if (response.data.success) {
                // Login successful - you might need to handle storing auth token
                // For now, we'll use the existing login method
                const cpfNumbers = cpf.replace(/\D/g, '');
                await login(cpfNumbers, smsCode); // Or however you handle auth
                toast.success('Login realizado com sucesso!');
            }
        } catch (error: any) {
            toast.error(error.message || 'Código SMS inválido');
        } finally {
            setEnergisaLoading(false);
        }
    };

    return (
        <div className={`min-h-screen flex items-center justify-center p-4 transition-colors duration-300 ${isDark ? 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900' : 'bg-gradient-to-br from-slate-100 via-white to-slate-200'}`}>
            {/* Toggle Theme Button */}
            <button
                onClick={toggleTheme}
                className={`absolute top-4 right-4 p-3 rounded-full transition ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-400' : 'bg-white hover:bg-slate-100 text-slate-600 shadow-md'}`}
            >
                {isDark ? <SunMedium size={20} /> : <Moon size={20} />}
            </button>

            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-[#00A3E0] rounded-2xl mb-4 shadow-lg shadow-blue-500/30">
                        <Zap className="text-white" size={32} />
                    </div>
                    <h1 className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-slate-800'}`}>GestorEnergy</h1>
                    <p className={isDark ? 'text-slate-400' : 'text-slate-600'}>Gerencie suas faturas de energia</p>
                </div>

                {/* Card de Login */}
                <div className={`rounded-2xl shadow-2xl p-8 ${isDark ? 'bg-slate-800' : 'bg-white'}`}>
                    <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-slate-800'}`}>Entrar</h2>

                    {/* Tabs */}
                    <div className="flex gap-2 mb-6">
                        <button
                            onClick={() => setLoginMethod('email')}
                            className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${loginMethod === 'email'
                                    ? 'bg-[#00A3E0] text-white'
                                    : isDark
                                        ? 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                }`}
                        >
                            <Mail size={16} className="inline mr-2" />
                            Email
                        </button>
                        <button
                            onClick={() => setLoginMethod('energisa')}
                            className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${loginMethod === 'energisa'
                                    ? 'bg-[#00A3E0] text-white'
                                    : isDark
                                        ? 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                }`}
                        >
                            <Shield size={16} className="inline mr-2" />
                            Energisa
                        </button>
                    </div>

                    {/* Email/Password Login */}
                    {loginMethod === 'email' && (
                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div>
                                <label className={`block text-sm font-medium mb-1.5 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                                    Email
                                </label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-[#00A3E0] focus:border-transparent outline-none transition ${isDark ? 'bg-slate-700 border-slate-600 text-white placeholder-slate-400' : 'bg-white border-slate-200 text-slate-900'}`}
                                        placeholder="seu@email.com"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className={`block text-sm font-medium mb-1.5 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                                    Senha
                                </label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                                    <input
                                        type="password"
                                        value={senha}
                                        onChange={(e) => setSenha(e.target.value)}
                                        className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-[#00A3E0] focus:border-transparent outline-none transition ${isDark ? 'bg-slate-700 border-slate-600 text-white placeholder-slate-400' : 'bg-white border-slate-200 text-slate-900'}`}
                                        placeholder="Digite sua senha"
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-[#00A3E0] text-white py-3 rounded-lg font-bold hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 size={20} className="animate-spin" />
                                        Entrando...
                                    </>
                                ) : (
                                    'Entrar'
                                )}
                            </button>
                        </form>
                    )}

                    {/* Energisa Login */}
                    {loginMethod === 'energisa' && (
                        <div className="space-y-5">
                            {/* Step 1: CPF */}
                            {energisaStep === 'cpf' && (
                                <>
                                    <div>
                                        <label className={`block text-sm font-medium mb-1.5 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                                            CPF do Titular
                                        </label>
                                        <input
                                            type="text"
                                            value={cpf}
                                            onChange={(e) => setCpf(formatCPF(e.target.value))}
                                            placeholder="000.000.000-00"
                                            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-[#00A3E0] focus:border-transparent outline-none transition ${isDark ? 'bg-slate-700 border-slate-600 text-white placeholder-slate-400' : 'bg-white border-slate-200 text-slate-900'}`}
                                        />
                                    </div>
                                    <button
                                        onClick={handleEnergisaCpf}
                                        disabled={energisaLoading}
                                        className="w-full bg-[#00A3E0] text-white py-3 rounded-lg font-bold hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                    >
                                        {energisaLoading ? (
                                            <>
                                                <Loader2 size={20} className="animate-spin" />
                                                Buscando...
                                            </>
                                        ) : (
                                            'Buscar Telefones'
                                        )}
                                    </button>
                                </>
                            )}

                            {/* Step 2: Phone Selection */}
                            {energisaStep === 'phone' && (
                                <>
                                    <div>
                                        <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                                            Selecione um telefone
                                        </label>
                                        <div className="space-y-2">
                                            {listaTelefone.map((phone) => (
                                                <button
                                                    key={`${phone.cdc}-${phone.posicao}`}
                                                    onClick={() => setSelectedPhone(phone)}
                                                    className={`w-full p-3 rounded-lg border-2 text-left transition ${selectedPhone?.cdc === phone.cdc && selectedPhone?.posicao === phone.posicao
                                                            ? 'border-[#00A3E0] bg-[#00A3E0]/10'
                                                            : isDark
                                                                ? 'border-slate-600 hover:border-slate-500 bg-slate-700'
                                                                : 'border-slate-200 hover:border-slate-300 bg-white'
                                                        }`}
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <div className={`font-medium ${isDark ? 'text-white' : 'text-slate-900'}`}>
                                                                {phone.celular}
                                                            </div>
                                                            <div className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                                                                UC: {phone.cdc}-{phone.digitoVerificador}
                                                            </div>
                                                        </div>
                                                        {selectedPhone?.cdc === phone.cdc && selectedPhone?.posicao === phone.posicao && (
                                                            <CheckCircle2 className="text-[#00A3E0]" size={20} />
                                                        )}
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <button
                                        onClick={handleEnergisaPhone}
                                        disabled={!selectedPhone || energisaLoading}
                                        className="w-full bg-[#00A3E0] text-white py-3 rounded-lg font-bold hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                    >
                                        {energisaLoading ? (
                                            <>
                                                <Loader2 size={20} className="animate-spin" />
                                                Enviando SMS...
                                            </>
                                        ) : (
                                            'Enviar SMS'
                                        )}
                                    </button>
                                </>
                            )}

                            {/* Step 3: SMS Code */}
                            {energisaStep === 'sms' && (
                                <>
                                    <div>
                                        <label className={`block text-sm font-medium mb-1.5 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                                            Código SMS
                                        </label>
                                        <input
                                            type="text"
                                            value={smsCode}
                                            onChange={(e) => setSmsCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                            placeholder="000000"
                                            className={`w-full px-4 py-3 border rounded-lg text-center text-lg tracking-widest font-mono focus:ring-2 focus:ring-[#00A3E0] focus:border-transparent outline-none transition ${isDark ? 'bg-slate-700 border-slate-600 text-white placeholder-slate-400' : 'bg-white border-slate-200 text-slate-900'}`}
                                            maxLength={6}
                                            autoFocus
                                        />
                                        <p className={`text-xs mt-2 text-center ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                                            SMS enviado para {selectedPhone?.celular}
                                        </p>
                                    </div>
                                    <button
                                        onClick={handleEnergisaSms}
                                        disabled={energisaLoading}
                                        className="w-full bg-[#00A3E0] text-white py-3 rounded-lg font-bold hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                    >
                                        {energisaLoading ? (
                                            <>
                                                <Loader2 size={20} className="animate-spin" />
                                                Validando...
                                            </>
                                        ) : (
                                            'Entrar'
                                        )}
                                    </button>
                                </>
                            )}
                        </div>
                    )}

                    <div className="mt-6 text-center">
                        <p className={isDark ? 'text-slate-400' : 'text-slate-600'}>
                            Nao tem uma conta?{' '}
                            <button
                                onClick={onSwitchToSignUp}
                                className="text-[#00A3E0] font-bold hover:underline"
                            >
                                Criar conta
                            </button>
                        </p>
                    </div>
                </div>

                <p className={`text-center text-sm mt-6 ${isDark ? 'text-slate-500' : 'text-slate-600'}`}>
                    Plataforma segura para gestao de faturas de energia
                </p>
            </div>
        </div>
    );
}

/**
 * SignUpPage - Página de cadastro com suporte a PF e PJ
 */

import { useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useToast } from '../../components/Toast';
import { Loader2, Mail, Lock, User, Phone, CreditCard, Zap, ArrowLeft, Moon, SunMedium, Building2, Search, CheckCircle } from 'lucide-react';

// Formatar CPF
const formatCPF = (value: string) => {
    const numbers = value.replace(/\D/g, '').slice(0, 11);
    return numbers
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
};

// Formatar CNPJ
const formatCNPJ = (value: string) => {
    const numbers = value.replace(/\D/g, '').slice(0, 14);
    return numbers
        .replace(/(\d{2})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1/$2')
        .replace(/(\d{4})(\d{1,2})$/, '$1-$2');
};

// Formatar telefone
const formatPhone = (value: string) => {
    const numbers = value.replace(/\D/g, '').slice(0, 11);
    if (numbers.length <= 10) {
        return numbers
            .replace(/(\d{2})(\d)/, '($1) $2')
            .replace(/(\d{4})(\d)/, '$1-$2');
    }
    return numbers
        .replace(/(\d{2})(\d)/, '($1) $2')
        .replace(/(\d{5})(\d)/, '$1-$2');
};

type TipoPessoa = 'PF' | 'PJ';

export function SignUpPage() {
    const navigate = useNavigate();
    const { signup } = useAuth();
    const { isDark, toggleTheme } = useTheme();
    const toast = useToast();

    const [tipoPessoa, setTipoPessoa] = useState<TipoPessoa>('PF');
    const [formData, setFormData] = useState({
        nome_completo: '',
        email: '',
        cpf: '',
        cnpj: '',
        razao_social: '',
        nome_fantasia: '',
        telefone: '',
        senha: '',
        confirmarSenha: '',
        // Dados extras da BrasilAPI (preenchidos automaticamente)
        logradouro: '',
        numero: '',
        complemento: '',
        bairro: '',
        cidade: '',
        uf: '',
        cep: '',
        porte: '',
        natureza_juridica: '',
        cnae_codigo: null as number | null,
        cnae_descricao: '',
        situacao_cadastral: '',
        data_abertura: ''
    });
    const [loading, setLoading] = useState(false);
    const [loadingCNPJ, setLoadingCNPJ] = useState(false);
    const [cnpjFound, setCnpjFound] = useState(false);

    // Buscar dados do CNPJ na BrasilAPI
    const buscarDadosCNPJ = useCallback(async (cnpj: string) => {
        const cnpjNumeros = cnpj.replace(/\D/g, '');
        if (cnpjNumeros.length !== 14) return;

        setLoadingCNPJ(true);
        setCnpjFound(false);

        try {
            const response = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpjNumeros}`);

            if (response.ok) {
                const data = await response.json();

                // Formata o CEP
                const cepFormatado = data.cep ? data.cep.replace(/(\d{5})(\d{3})/, '$1-$2') : '';

                // Monta o logradouro completo
                const logradouroCompleto = data.descricao_tipo_de_logradouro && data.logradouro
                    ? `${data.descricao_tipo_de_logradouro} ${data.logradouro}`
                    : data.logradouro || '';

                setFormData(prev => ({
                    ...prev,
                    razao_social: data.razao_social || '',
                    nome_fantasia: data.nome_fantasia || '',
                    // Endereço
                    logradouro: logradouroCompleto,
                    numero: data.numero || '',
                    complemento: data.complemento || '',
                    bairro: data.bairro || '',
                    cidade: data.municipio || '',
                    uf: data.uf || '',
                    cep: cepFormatado,
                    // Dados empresariais
                    porte: data.porte || '',
                    natureza_juridica: data.natureza_juridica || '',
                    cnae_codigo: data.cnae_fiscal || null,
                    cnae_descricao: data.cnae_fiscal_descricao || '',
                    situacao_cadastral: data.descricao_situacao_cadastral || '',
                    data_abertura: data.data_inicio_atividade || ''
                }));
                setCnpjFound(true);
                toast.success('Dados da empresa carregados!');
            } else if (response.status === 404) {
                toast.warning('CNPJ não encontrado na base de dados');
            } else {
                toast.warning('Não foi possível buscar dados do CNPJ');
            }
        } catch (error) {
            console.error('Erro ao buscar CNPJ:', error);
            // Silenciosamente falha - usuário pode preencher manualmente
        } finally {
            setLoadingCNPJ(false);
        }
    }, [toast]);

    const handleChange = (field: string, value: string) => {
        let formattedValue = value;

        if (field === 'cpf') {
            formattedValue = formatCPF(value);
        } else if (field === 'cnpj') {
            formattedValue = formatCNPJ(value);
            // Buscar dados quando CNPJ estiver completo
            const cnpjNumeros = value.replace(/\D/g, '');
            if (cnpjNumeros.length === 14) {
                buscarDadosCNPJ(value);
            } else {
                setCnpjFound(false);
            }
        } else if (field === 'telefone') {
            formattedValue = formatPhone(value);
        }

        setFormData(prev => ({ ...prev, [field]: formattedValue }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Validações comuns
        if (!formData.nome_completo || !formData.email || !formData.telefone || !formData.senha) {
            toast.warning('Preencha todos os campos obrigatórios');
            return;
        }

        if (formData.nome_completo.split(' ').length < 2) {
            toast.warning('Informe nome e sobrenome');
            return;
        }

        // Validações específicas PF
        if (tipoPessoa === 'PF') {
            if (!formData.cpf) {
                toast.warning('Informe o CPF');
                return;
            }
            if (formData.cpf.replace(/\D/g, '').length !== 11) {
                toast.warning('CPF deve ter 11 dígitos');
                return;
            }
        }

        // Validações específicas PJ
        if (tipoPessoa === 'PJ') {
            if (!formData.cnpj) {
                toast.warning('Informe o CNPJ');
                return;
            }
            if (formData.cnpj.replace(/\D/g, '').length !== 14) {
                toast.warning('CNPJ deve ter 14 dígitos');
                return;
            }
        }

        if (formData.senha.length < 6) {
            toast.warning('Senha deve ter pelo menos 6 caracteres');
            return;
        }

        if (formData.senha !== formData.confirmarSenha) {
            toast.warning('As senhas não conferem');
            return;
        }

        setLoading(true);
        try {
            const signupData: any = {
                tipo_pessoa: tipoPessoa,
                nome_completo: formData.nome_completo,
                email: formData.email,
                telefone: formData.telefone.replace(/\D/g, ''),
                password: formData.senha
            };

            if (tipoPessoa === 'PF') {
                signupData.cpf = formData.cpf.replace(/\D/g, '');
            } else {
                signupData.cnpj = formData.cnpj.replace(/\D/g, '');
                signupData.razao_social = formData.razao_social || null;
                signupData.nome_fantasia = formData.nome_fantasia || null;
                // Dados extras da BrasilAPI
                signupData.logradouro = formData.logradouro || null;
                signupData.numero = formData.numero || null;
                signupData.complemento = formData.complemento || null;
                signupData.bairro = formData.bairro || null;
                signupData.cidade = formData.cidade || null;
                signupData.uf = formData.uf || null;
                signupData.cep = formData.cep?.replace(/\D/g, '') || null;
                signupData.porte = formData.porte || null;
                signupData.natureza_juridica = formData.natureza_juridica || null;
                signupData.cnae_codigo = formData.cnae_codigo || null;
                signupData.cnae_descricao = formData.cnae_descricao || null;
                signupData.situacao_cadastral = formData.situacao_cadastral || null;
                signupData.data_abertura = formData.data_abertura || null;
            }

            await signup(signupData);
            toast.success('Conta criada com sucesso!');
        } catch (err: any) {
            toast.error(err.message || 'Erro ao criar conta');
        } finally {
            setLoading(false);
        }
    };

    const inputClass = `w-full pl-10 pr-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-[#00A3E0] focus:border-transparent outline-none transition text-sm ${isDark ? 'bg-slate-700 border-slate-600 text-white placeholder-slate-400' : 'bg-white border-slate-200 text-slate-900'}`;
    const labelClass = `block text-sm font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`;

    return (
        <div className={`min-h-screen flex items-center justify-center p-4 py-8 transition-colors duration-300 ${isDark ? 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900' : 'bg-gradient-to-br from-slate-100 via-white to-slate-200'}`}>
            {/* Toggle Theme */}
            <button
                onClick={toggleTheme}
                className={`absolute top-4 right-4 p-3 rounded-full transition ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-400' : 'bg-white hover:bg-slate-100 text-slate-600 shadow-md'}`}
            >
                {isDark ? <SunMedium size={20} /> : <Moon size={20} />}
            </button>

            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-6">
                    <Link to="/" className="inline-block">
                        <div className="inline-flex items-center justify-center w-14 h-14 bg-[#00A3E0] rounded-2xl mb-3 shadow-lg shadow-blue-500/30">
                            <Zap className="text-white" size={28} />
                        </div>
                    </Link>
                    <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-800'}`}>Plataforma GD</h1>
                </div>

                {/* Card de Cadastro */}
                <div className={`rounded-2xl shadow-2xl p-6 sm:p-8 ${isDark ? 'bg-slate-800' : 'bg-white'}`}>
                    <div className="flex items-center gap-3 mb-6">
                        <Link
                            to="/app"
                            className={`p-2 rounded-lg transition ${isDark ? 'hover:bg-slate-700' : 'hover:bg-slate-100'}`}
                        >
                            <ArrowLeft size={20} className={isDark ? 'text-slate-400' : 'text-slate-600'} />
                        </Link>
                        <h2 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-slate-800'}`}>Criar conta</h2>
                    </div>

                    {/* Toggle PF/PJ */}
                    <div className="flex gap-2 mb-6">
                        <button
                            type="button"
                            onClick={() => setTipoPessoa('PF')}
                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg font-medium transition ${
                                tipoPessoa === 'PF'
                                    ? 'bg-[#00A3E0] text-white'
                                    : isDark
                                        ? 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                            }`}
                        >
                            <User size={18} />
                            Pessoa Física
                        </button>
                        <button
                            type="button"
                            onClick={() => setTipoPessoa('PJ')}
                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg font-medium transition ${
                                tipoPessoa === 'PJ'
                                    ? 'bg-[#00A3E0] text-white'
                                    : isDark
                                        ? 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                            }`}
                        >
                            <Building2 size={18} />
                            Pessoa Jurídica
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className={labelClass}>
                                {tipoPessoa === 'PF' ? 'Nome completo' : 'Nome do responsável'}
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="text"
                                    value={formData.nome_completo}
                                    onChange={(e) => handleChange('nome_completo', e.target.value)}
                                    className={inputClass}
                                    placeholder={tipoPessoa === 'PF' ? 'Seu nome completo' : 'Nome do responsável'}
                                />
                            </div>
                        </div>

                        <div>
                            <label className={labelClass}>Email</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="email"
                                    value={formData.email}
                                    onChange={(e) => handleChange('email', e.target.value)}
                                    className={inputClass}
                                    placeholder="seu@email.com"
                                />
                            </div>
                        </div>

                        {/* Campos PF */}
                        {tipoPessoa === 'PF' && (
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className={labelClass}>CPF</label>
                                    <div className="relative">
                                        <CreditCard className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                        <input
                                            type="text"
                                            value={formData.cpf}
                                            onChange={(e) => handleChange('cpf', e.target.value)}
                                            className={inputClass}
                                            placeholder="000.000.000-00"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className={labelClass}>Telefone</label>
                                    <div className="relative">
                                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                        <input
                                            type="text"
                                            value={formData.telefone}
                                            onChange={(e) => handleChange('telefone', e.target.value)}
                                            className={inputClass}
                                            placeholder="(00) 00000-0000"
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Campos PJ */}
                        {tipoPessoa === 'PJ' && (
                            <>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className={labelClass}>CNPJ</label>
                                        <div className="relative">
                                            {loadingCNPJ ? (
                                                <Loader2 className="absolute left-3 top-1/2 -translate-y-1/2 text-blue-500 animate-spin" size={18} />
                                            ) : cnpjFound ? (
                                                <CheckCircle className="absolute left-3 top-1/2 -translate-y-1/2 text-green-500" size={18} />
                                            ) : (
                                                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                            )}
                                            <input
                                                type="text"
                                                value={formData.cnpj}
                                                onChange={(e) => handleChange('cnpj', e.target.value)}
                                                className={`${inputClass} ${cnpjFound ? 'border-green-500 focus:ring-green-500' : ''}`}
                                                placeholder="00.000.000/0000-00"
                                            />
                                            {loadingCNPJ && (
                                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-blue-500">
                                                    Buscando...
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    <div>
                                        <label className={labelClass}>Telefone</label>
                                        <div className="relative">
                                            <Phone className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                            <input
                                                type="text"
                                                value={formData.telefone}
                                                onChange={(e) => handleChange('telefone', e.target.value)}
                                                className={inputClass}
                                                placeholder="(00) 00000-0000"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <label className={labelClass}>
                                        Razão Social
                                        {cnpjFound && <span className="text-green-500 font-normal ml-2 text-xs">(preenchido automaticamente)</span>}
                                    </label>
                                    <div className="relative">
                                        <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                        <input
                                            type="text"
                                            value={formData.razao_social}
                                            onChange={(e) => handleChange('razao_social', e.target.value)}
                                            className={`${inputClass} ${cnpjFound && formData.razao_social ? 'border-green-500' : ''}`}
                                            placeholder="Razão social da empresa"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className={labelClass}>
                                        Nome Fantasia
                                        {cnpjFound && <span className="text-green-500 font-normal ml-2 text-xs">(preenchido automaticamente)</span>}
                                    </label>
                                    <div className="relative">
                                        <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                        <input
                                            type="text"
                                            value={formData.nome_fantasia}
                                            onChange={(e) => handleChange('nome_fantasia', e.target.value)}
                                            className={`${inputClass} ${cnpjFound && formData.nome_fantasia ? 'border-green-500' : ''}`}
                                            placeholder="Nome fantasia"
                                        />
                                    </div>
                                </div>
                            </>
                        )}

                        <div>
                            <label className={labelClass}>Senha</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="password"
                                    value={formData.senha}
                                    onChange={(e) => handleChange('senha', e.target.value)}
                                    className={inputClass}
                                    placeholder="Mínimo 6 caracteres"
                                />
                            </div>
                        </div>

                        <div>
                            <label className={labelClass}>Confirmar senha</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="password"
                                    value={formData.confirmarSenha}
                                    onChange={(e) => handleChange('confirmarSenha', e.target.value)}
                                    className={inputClass}
                                    placeholder="Repita a senha"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-[#00A3E0] text-white py-3 rounded-lg font-bold hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-6"
                        >
                            {loading ? (
                                <>
                                    <Loader2 size={20} className="animate-spin" />
                                    Criando conta...
                                </>
                            ) : (
                                'Criar conta'
                            )}
                        </button>
                    </form>

                    <div className="mt-4 text-center">
                        <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                            Já tem uma conta?{' '}
                            <Link to="/app" className="text-[#00A3E0] font-bold hover:underline">
                                Entrar
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default SignUpPage;

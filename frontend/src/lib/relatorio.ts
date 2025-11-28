import axios from 'axios';
import html2pdf from 'html2pdf.js';

type Tarifas = {
    tarifaB1_kWh_comImpostos: number;
    fioBBase_kWh: number;
};

type FormInputs = {
    nome: string;
    tipoClassificacao: 'Monofásico' | 'Bifásico' | 'Trifásico';
    consumo: number;              // kWh/mês
    iluminacaoPublica: number;    // R$/mês
    bandeiras: number;            // R$/mês
    vendedor: string;
};

const PIS = 0.012102;
const COFINS = 0.055743;
const ICMS = 0.17;
const TRIB_DIVISOR = (1 - (PIS + COFINS)) * (1 - ICMS);

const applyTaxes = (valor: number) => valor / TRIB_DIVISOR;
const parseBR = (value: any) => {
    if (value === null || value === undefined) return 0;
    const s = String(value).trim();
    if (!s) return 0;
    return Number(s.replace(/\./g, '').replace(',', '.')) || 0;
};

async function buscarTarifas(): Promise<Tarifas> {
    // TUSD+TE
    const tarifaResp = await axios.get('https://dadosabertos.aneel.gov.br/api/3/action/datastore_search', {
        params: {
            resource_id: 'fcf2906c-7c32-4b9b-a637-054e7a5234f4',
            filters: JSON.stringify({
                SigAgente: 'EMT',
                DscBaseTarifaria: 'Tarifa de Aplicação',
                DscSubGrupo: 'B1',
                DscModalidadeTarifaria: 'Convencional',
                DscDetalhe: 'Não se aplica',
                NomPostoTarifario: 'Não se aplica',
                DscClasse: 'Residencial',
                DscSubClasse: 'Residencial',
                DscREH: 'RESOLUÇÃO HOMOLOGATÓRIA N° 3.440, DE 1 DE ABRIL DE 2025'
            }),
            sort: 'DatInicioVigencia desc',
            limit: 30
        }
    });

    // Fio B
    const fioResp = await axios.get('https://dadosabertos.aneel.gov.br/api/3/action/datastore_search', {
        params: {
            resource_id: 'a4060165-3a0c-404f-926c-83901088b67c',
            filters: JSON.stringify({
                SigNomeAgente: 'EMT',
                DscComponenteTarifario: 'TUSD_FioB',
                DscBaseTarifaria: 'Tarifa de Aplicação',
                DscSubGrupoTarifario: 'B1',
                DscModalidadeTarifaria: 'Convencional',
                DscClasseConsumidor: 'Residencial',
                DscSubClasseConsumidor: 'Residencial',
                DscDetalheConsumidor: 'Não se aplica',
                DscPostoTarifario: 'Não se aplica',
                DscResolucaoHomologatoria: 'RESOLUÇÃO HOMOLOGATÓRIA N° 3.440, DE 1 DE ABRIL DE 2025'
            }),
            sort: 'DatInicioVigencia desc',
            limit: 30
        }
    });

    // Tarifas
    let tarifaB1_kWh_comImpostos = 0;
    (tarifaResp.data.result?.records || []).forEach((r: any) => {
        if (r.DscSubGrupo === 'B1' && r.DscModalidadeTarifaria === 'Convencional' && r.NomPostoTarifario === 'Não se aplica') {
            let total = parseBR(r.VlrTUSD) + parseBR(r.VlrTE); // R$/MWh sem tributos
            if (r.DscUnidadeTerciaria === 'MWh') total = total / 1000; // R$/kWh sem tributos
            tarifaB1_kWh_comImpostos = applyTaxes(total); // R$/kWh com tributos
        }
    });

    let fioBBase_kWh = 0;
    const fio = (fioResp.data.result?.records || [])[0];
    if (fio) fioBBase_kWh = parseBR(fio.VlrComponenteTarifario) / 1000; // R$/kWh sem tributos

    return { tarifaB1_kWh_comImpostos, fioBBase_kWh };
}

function montarHtml(form: FormInputs, tarifas: Tarifas) {
    const { tarifaB1_kWh_comImpostos, fioBBase_kWh } = tarifas;
    const consumo_kWh = form.consumo;
    const iluminacaoPublica_R = form.iluminacaoPublica;
    const bandeiras_R = form.bandeiras;

    // taxa mínima kWh
    let taxaMin_kWh = 50;
    const tipo = form.tipoClassificacao.toLowerCase();
    if (tipo.includes('mono')) taxaMin_kWh = 30;
    else if (tipo.includes('tri')) taxaMin_kWh = 100;
    const taxaMinAplicada_kWh = Math.min(consumo_kWh, taxaMin_kWh);

    // Fio B escalonado
    const FIOB_RAMP: Record<number, number> = { 2023: 0.15, 2024: 0.30, 2025: 0.45, 2026: 0.60, 2027: 0.75, 2028: 0.90 };
    const anoAtual = new Date().getFullYear();
    const fatorFioB = FIOB_RAMP[anoAtual] ?? FIOB_RAMP[2028];
    const fioB_escalonado_kWh = fioBBase_kWh * fatorFioB;
    const valorFioB_R = consumo_kWh * fioB_escalonado_kWh;

    const valorTaxaMin_R = taxaMinAplicada_kWh * tarifaB1_kWh_comImpostos;
    const valorPisoRegulatorio_R = Math.max(valorTaxaMin_R, valorFioB_R);

    // Tarifas com desconto
    const descontoPercentTarifa = 0.30;
    const tarifaMidwest_kWh = tarifaB1_kWh_comImpostos * (1 - descontoPercentTarifa);

    const valorConsumoEnergisa_R = consumo_kWh * tarifaB1_kWh_comImpostos;
    const valorConsumoMidwest_R = consumo_kWh * tarifaMidwest_kWh;
    const economiaConsumo_R = Math.max(valorConsumoEnergisa_R - valorConsumoMidwest_R, 0);

    const contaAtual_R = valorConsumoEnergisa_R + iluminacaoPublica_R + bandeiras_R;
    const contaMidwest_R = valorConsumoMidwest_R + valorPisoRegulatorio_R + iluminacaoPublica_R;

    let economiaMensal_R = contaAtual_R - contaMidwest_R;
    if (economiaMensal_R < 0) economiaMensal_R = 0;
    const economiaAnual_R = economiaMensal_R * 12;

    let faturasNumber = 0;
    if (contaMidwest_R > 0 && economiaAnual_R > 0) {
        faturasNumber = economiaAnual_R / contaMidwest_R;
    }

    // Tabela 10 anos
    const reajusteAnual = 0.08;
    let linhas10Anos = '';
    let economiaAcumulada_R = 0;
    for (let i = 0; i < 10; i++) {
        const fator = Math.pow(1 + reajusteAnual, i);
        const custoEnergisaAno_R = contaAtual_R * 12 * fator;
        const valorMidwestAno_R = contaMidwest_R * 12 * fator;
        let economiaAno_R = custoEnergisaAno_R - valorMidwestAno_R;
        if (economiaAno_R < 0) economiaAno_R = 0;
        economiaAcumulada_R += economiaAno_R;
        linhas10Anos += `
      <tr>
        <td>${i + 1}</td>
        <td>R$ ${custoEnergisaAno_R.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
        <td>R$ ${valorMidwestAno_R.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
        <td class="text-green">R$ ${economiaAno_R.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
        <td class="text-primary">R$ ${economiaAcumulada_R.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
      </tr>`;
    }

    const logoUrl = 'https://baserow.simplexsolucoes.com.br/media/user_files/WE8kutKMAmL1PMICsfR9k56kUHaNYz8p_4566a63159be5bf535dc3a25811394b215dcd9a04a1a44d9f14321e296b6a9c3.png';

    // (Use aqui o HTML do fluxo que já está no relatorio.md; resumido para caber)
    const html = `
  <html><head><style>
    /* copie o CSS do fluxo aqui */
    .text-green { color: #28a745; font-weight: 600; }
    .text-primary { color: #F18A26; font-weight: 700; }
  </style></head>
  <body>
    <!-- Header -->
    <div>
      <img src="${logoUrl}" alt="Midwest" style="max-width:220px;" />
      <div>Proposta para: <strong>${form.nome}</strong></div>
    </div>

    <!-- Cards -->
    <div>
      <div>Valor Atual: R$ ${contaAtual_R.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
      <div>Com Midwest: R$ ${contaMidwest_R.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
      <div>Economia Mensal: R$ ${economiaMensal_R.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
      <div>Faturas economizadas/ano: ${faturasNumber.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 2 })}</div>
    </div>

    <!-- Tabela 10 anos -->
    <table border="1" cellspacing="0" cellpadding="4">
      <thead>
        <tr><th>Ano</th><th>Gasto sem Midwest</th><th>Gasto com Midwest</th><th>Economia Anual</th><th>Economia Total</th></tr>
      </thead>
      <tbody>${linhas10Anos}</tbody>
    </table>
  </body></html>`;

    return html;
}

export async function gerarRelatorioInterno(form: FormInputs, fileName = 'relatorio-midwest.pdf') {
    const tarifas = await buscarTarifas();
    const html = montarHtml(form, tarifas);
    const opt = {
        margin: 0,
        filename: fileName,
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };
    await html2pdf().from(html).set(opt).save();
}

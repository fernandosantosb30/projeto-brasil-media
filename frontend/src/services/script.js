'use strict';

const el = (id) => document.getElementById(id);
const moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

async function verificarResposta(response) {
    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(typeof body.detail === 'string' ? body.detail : 'Não foi possível concluir. Verifique os campos e tente novamente.');
    }
    return response;
}

async function carregarFiltros() {
    try {
        const response = await verificarResposta(await fetch('/filtros/opcoes'));
        const opcoes = await response.json();
        for (const [id, key] of [['tipo_servico', 'servicos'], ['interface', 'interfaces'], ['ip_fixo', 'ips']]) {
            // Option usa texto, sem interpretar conteúdo da base como HTML.
            el(id).replaceChildren(new Option('Todos', ''), ...opcoes[key].map((item) => new Option(item, item)));
        }
        el('calcular').disabled = false;
        el('processar').disabled = false;
        el('status').textContent = 'Selecione os filtros para iniciar a consulta.';
    } catch {
        el('status').textContent = 'Não foi possível carregar as opções. Recarregue a página para tentar novamente.';
    }
}

async function buscarMedia(event) {
    event.preventDefault();
    el('calcular').disabled = true;
    el('display-media').textContent = '—';
    el('display-qtd').textContent = '—';
    el('status').textContent = 'Consultando…';
    try {
        const params = new URLSearchParams();
        for (const id of ['cidade', 'uf', 'tipo_servico', 'interface', 'ip_fixo', 'prazo']) {
            const value = el(id).value.trim();
            if (value) params.set(id, value);
        }
        if (el('velocidade').value) {
            const mbps = Number(el('velocidade').value) * (el('unidade').value === 'Gbps' ? 1000 : 1);
            if (!Number.isSafeInteger(mbps) || mbps <= 0 || mbps > 1000000000) {
                throw new Error('Informe uma velocidade equivalente a um número inteiro positivo de Mbps.');
            }
            params.set('velocidade', mbps);
        }
        const response = await verificarResposta(await fetch(`/contratos/custo-medio?${params}`));
        const dados = await response.json();
        el('display-media').textContent = dados.custo_medio === null ? 'Sem dados' : moeda.format(dados.custo_medio);
        el('display-qtd').textContent = dados.quantidade_contratos;
        el('status').textContent = dados.mensagem;
    } catch (error) {
        el('status').textContent = error instanceof TypeError ? 'Conexão indisponível. Tente novamente.' : error.message;
    } finally {
        el('calcular').disabled = false;
    }
}

async function processarLote(event) {
    event.preventDefault();
    const file = el('arquivo').files[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
        el('status-lote').textContent = 'O arquivo deve ter no máximo 2 MiB.';
        return;
    }
    el('processar').disabled = true;
    el('status-lote').textContent = 'Processando…';
    try {
        const data = new FormData();
        data.append('file', file);
        const response = await verificarResposta(await fetch('/contratos/processar-planilha', { method: 'POST', body: data }));
        const url = URL.createObjectURL(await response.blob());
        const link = document.createElement('a');
        link.href = url;
        link.download = 'resultado_custos.csv';
        document.body.append(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        el('status-lote').textContent = 'Consulta concluída. O download do resultado foi iniciado.';
    } catch (error) {
        el('status-lote').textContent = error instanceof TypeError ? 'Conexão indisponível. Tente novamente.' : error.message;
    } finally {
        el('processar').disabled = false;
    }
}

el('consulta').addEventListener('submit', buscarMedia);
el('lote').addEventListener('submit', processarLote);
carregarFiltros();

// 1. Função para carregar os filtros dinâmicos da planilha ao abrir o site
async function carregarFiltros() {
    try {
        const response = await fetch('http://127.0.0.1:8000/filtros/opcoes');
        if (!response.ok) throw new Error('Falha ao carregar opções');
        
        const opcoes = await response.json();

        // Preenche os selects com os dados reais da planilha
        preencherSelect('tipo_servico', opcoes.servicos);
        preencherSelect('interface', opcoes.interfaces);
        preencherSelect('ip_fixo', opcoes.ips);
        
    } catch (e) {
        console.error("Erro ao carregar filtros:", e);
    }
}

// Função auxiliar para montar as opções dentro dos <select>
function preencherSelect(id, lista) {
    const select = document.getElementById(id);
    if (!select) return;
    
    select.innerHTML = '<option value="">Todos</option>';
    lista.forEach(item => {
        if (item && item !== 'NAN') {
            select.innerHTML += `<option value="${item}">${item}</option>`;
        }
    });
}

// 2. Sua função de busca corrigida com os novos campos
async function buscarMedia() {
    // Captura os valores (incluindo os novos campos Interface e IP Fixo)
    const cidade = document.getElementById('cidade').value;
    const uf = document.getElementById('uf').value;
    const tipo_servico = document.getElementById('tipo_servico').value;
    const interfaceTec = document.getElementById('interface').value; // Novo
    const ip_fixo = document.getElementById('ip_fixo').value;         // Novo
    const velocidade = document.getElementById('velocidade').value;
    const prazo = document.getElementById('prazo').value;

    // Monta a URL com TODOS os parâmetros
    const url = new URL('http://127.0.0.1:8000/contratos/custo-medio');
    
    if (cidade) url.searchParams.append('cidade', cidade);
    if (uf) url.searchParams.append('uf', uf);
    if (tipo_servico) url.searchParams.append('tipo_servico', tipo_servico);
    if (interfaceTec) url.searchParams.append('interface', interfaceTec);
    if (ip_fixo) url.searchParams.append('ip_fixo', ip_fixo);
    if (velocidade) url.searchParams.append('velocidade', velocidade);
    if (prazo) url.searchParams.append('prazo', prazo);

    try {
        const response = await fetch(url);
        
        if (!response.ok) throw new Error('Erro na resposta do servidor');
        
        const dados = await response.json();

        // Atualiza a tela
        document.getElementById('display-media').innerText = 
            `R$ ${dados.custo_medio.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        
        document.getElementById('display-qtd').innerText = dados.quantidade_contratos;

    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao conectar com o Backend. Verifique se o Uvicorn está rodando!');
    }
}

// Substitua o final do seu script.js por isso:
document.addEventListener('DOMContentLoaded', (event) => {
    console.log('DOM carregado, buscando filtros...');
    carregarFiltros();
});
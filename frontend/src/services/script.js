async function buscarMedia() {
    const cidade = document.getElementById('cidade').value;
    const uf = document.getElementById('uf').value;
    const velocidade = document.getElementById('velocidade').value;
    const prazo = document.getElementById('prazo').value;
    
    const resultadoDiv = document.getElementById('resultado');

    // Montando a URL com os novos parâmetros
    let url = `http://127.0.0.1:8000/contratos/custo-medio?`;
    
    if (cidade) url += `cidade=${cidade}&`;
    if (uf) url += `uf=${uf}&`;
    if (velocidade) url += `velocidade=${velocidade}&`;
    if (prazo) url += `prazo=${prazo}`;

    try {
        const response = await fetch(url);
        const data = await response.json();

        if (data.quantidade_contratos > 0) {
            document.getElementById('res-media').innerText = `R$ ${data.custo_medio.toFixed(2)}`;
            document.getElementById('res-qtd').innerText = data.quantidade_contratos;
            resultadoDiv.style.display = 'block';
        } else {
            alert("Nenhum contrato encontrado para esses critérios.");
            resultadoDiv.style.display = 'none';
        }
    } catch (error) {
        alert("Erro ao conectar com o Backend. Verifique se o Uvicorn está rodando!");
    }
}
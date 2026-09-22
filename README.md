# Painel de Custos de Conectividade

Aplicação web para consultar o custo médio mensal de contratos de conectividade por cidade, estado e características do serviço. Combina uma API em Python com uma interface em HTML, CSS e JavaScript, incluindo consultas individuais e processamento de CSV em lote.

**Esta versão é uma demonstração de portfólio. Os 12 contratos e todos os valores incluídos são fictícios, criados exclusivamente para estudo. Não representam preços de mercado, clientes ou operações de uma empresa.**

## O que o projeto resolve

O painel centraliza consultas que normalmente exigiriam filtrar uma planilha manualmente. Permite explorar como localização, velocidade, interface, IP fixo e prazo alteram a amostra usada no cálculo. É destinado a pessoas que estudam análise de dados, desenvolvimento de APIs e sistemas de apoio à consulta de custos.

## Funcionalidades

- Consulta por cidade, UF, serviço, velocidade, prazo, interface e IP fixo.
- Opções de serviço, interface e IP fixo carregadas da própria base.
- Conversão de Gbps para Mbps na interface: 1 Gbps = 1.000 Mbps.
- Média mensal e quantidade de contratos encontrados.
- Alternativa regional identificada na tela quando não há correspondência na cidade.
- Importação de até 1.000 consultas por CSV, com download dos resultados.
- Validação de dados, mensagens de erro e documentação interativa da API.
- Interface adaptável a telas pequenas, com rótulos e mensagens acessíveis.

## Demonstração local

Depois de iniciar a aplicação, abra [o painel local](http://127.0.0.1:8000) e experimente:

| Cidade | UF | Serviço | Velocidade | Resultado esperado |
| --- | --- | --- | --- | --- |
| Curitiba | PR | Link dedicado | 500 Mbps | R$ 1.200,00 em 2 contratos |
| Maringá | PR | Link dedicado | 500 Mbps | R$ 1.400,00 em 3 contratos, pela alternativa regional |
| Curitiba | PR | Link dedicado | 1 Gbps | R$ 2.200,00 em 1 contrato |

Deixe os outros filtros vazios para reproduzir os exemplos. A tela também oferece um [modelo de consulta em lote](frontend/exemplo_consultas.csv).

## Tecnologias e arquitetura

- **Python e FastAPI:** API HTTP, validação com Pydantic e documentação OpenAPI.
- **Biblioteca padrão do Python:** leitura de CSV e cálculo monetário com `Decimal`.
- **HTML, CSS e JavaScript:** interface sem framework e sem etapa de build.
- **Uvicorn:** servidor da aplicação.
- **pytest e Ruff:** testes de regressão, análise estática e formatação.

```text
Navegador → FastAPI → validação dos filtros → cálculo em memória
                 ↳ CSV fictício carregado na inicialização
                 ↳ arquivos estáticos da interface
```

A interface e a API compartilham a mesma origem. As requisições usam caminhos relativos, sem endereço de servidor fixado no JavaScript e sem CORS aberto. A aplicação não utiliza banco de dados, autenticação, cadastro de contratos ou serviços externos para calcular médias.

```text
backend/
  app/
    main.py                # Inicialização, opções de filtros e frontend
    data_handler.py        # Leitura, normalização e validação do CSV
    schemas.py             # Filtros e respostas tipadas
    middleware.py          # Limite de tamanho da requisição
    routes/contratos.py    # Consulta individual e lote
    services/calculos.py   # Regra de média e alternativa regional
  tests/test_app.py        # Testes automatizados
  contratos.csv            # Base inteiramente fictícia
  requirements.txt         # Dependências de execução fixadas
  requirements-dev.txt     # Ferramentas de desenvolvimento
frontend/
  index.html
  exemplo_consultas.csv
  src/services/script.js
  src/styles/styles.css
```

## Instalação e execução

Pré-requisitos: **Python 3.14**, `pip` e suporte a `venv`. Essa é a versão usada na validação desta edição. Não é necessário instalar Node.js, MySQL ou ferramentas de frontend.

Na raiz do projeto, em Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --no-access-log
```

No PowerShell do Windows:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --no-access-log
```

Acesse:

- [Interface](http://127.0.0.1:8000)
- [Documentação da API](http://127.0.0.1:8000/docs)
- [Estado da aplicação](http://127.0.0.1:8000/health)

Se a porta estiver ocupada, acrescente `--port 8765` e use essa porta no navegador. Execute os comandos a partir da raiz; não abra `index.html` diretamente como arquivo.

### Configuração

A configuração padrão funciona sem `.env`. Para alterá-la, copie `.env.example` para `.env` e ajuste:

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `CONTRATOS_CSV` | `backend/contratos.csv` | Caminho absoluto ou relativo à raiz para a base de consulta |

Variáveis definidas no ambiente têm prioridade sobre `.env`. Reinicie o servidor depois de alterar a base ou a configuração. Uma base ausente ou inválida impede a inicialização, em vez de produzir médias enganosas.

Para uso pessoal, mantenha a planilha original intacta em `private/contratos.csv`. Essa pasta não é versionada nem enviada ao Docker. O padrão `backend/contratos.csv` é sempre artificial. Para selecionar outra base local, use `CONTRATOS_CSV=private/contratos.csv` no `.env`, após validar o formato e os registros conforme as regras abaixo. Uma base com campos obrigatórios ausentes ou valores inválidos será rejeitada; preserve o original e faça eventuais correções somente em uma cópia privada.

A interface desta edição identifica os dados como fictícios: mantenha apenas bases sintéticas em qualquer demonstração pública. Não faça upload do original nem de suas cópias privadas ao GitHub.

### Docker (opcional)

Com Docker e Compose instalados:

```bash
docker compose up --build
```

Acesse a porta 8000. O contêiner executa sem privilégios de administrador, tem sistema de arquivos somente para leitura e expõe a porta apenas no endereço local. O contexto de build inclui somente o código e os dados demonstrativos necessários. A execução por Docker não foi validada no ambiente desta revisão, onde Docker não estava disponível.

## Dados e regras de cálculo

A base usa estas colunas obrigatórias:

| Coluna | Conteúdo |
| --- | --- |
| `cidade`, `uf` | Localidade e sigla de duas letras |
| `tipo_servico`, `interface`, `ip_fixo` | Categorias de serviço |
| `velocidade` | Inteiro positivo em Mbps |
| `prazo` | Inteiro positivo em meses |
| `valor` | Valor mensal positivo em reais |

A leitura aceita UTF-8, UTF-8 com BOM e Windows-1252, com vírgula ou ponto e vírgula como delimitador. Números aceitam ponto decimal (`1234.56`) ou vírgula decimal com milhar brasileiro (`1.234,56`). Um ponto isolado é decimal: use `1000` para mil. Valores que contenham o delimitador devem estar entre aspas. Velocidade e prazo devem corresponder a inteiros; valores numéricos devem ser positivos e não exceder 1 bilhão.

Textos são comparados sem distinção de acentos, caixa ou espaços repetidos. A média é aritmética simples, calculada com `Decimal` e arredondada para dois decimais usando `ROUND_HALF_UP`.

1. Todos os filtros informados são aplicados em conjunto.
2. Se não houver resultado e cidade e UF tiverem sido informadas, somente a cidade é desconsiderada. Serviço, velocidade, interface, IP fixo e prazo continuam valendo.
3. Sem correspondências, a API retorna `custo_medio: null`, amostragem zero e `tipo_resultado: "sem_dados"`. Isso não significa custo zero.

### Consulta em lote

Use as colunas obrigatórias `cidade`, `uf`, `tipo_servico` e `velocidade`. As colunas `interface`, `ip_fixo` e `prazo` são opcionais. Os cabeçalhos `servico` e `serviço` também são aceitos. Colunas desconhecidas, duplicadas, campos obrigatórios vazios e linhas inválidas rejeitam o arquivo inteiro com HTTP 422.

O arquivo deve ter extensão `.csv`, até **2 MiB** e **1.000 registros**. Há também um limite de 2 MiB + 64 KiB para a requisição completa, antes do parser multipart. O upload não altera a base; arquivos temporários usados pelo parser são fechados após a requisição.

A saída usa UTF-8 com BOM, ponto e vírgula e vírgula decimal, incluindo:

- `custo_medio_estimado`: vazio quando não há correspondência.
- `amostragem_contratos`: quantidade usada no cálculo.
- `tipo_resultado`: `especifico`, `media_regional` ou `sem_dados`.

Textos que podem ser interpretados como fórmulas recebem um apóstrofo na exportação. A regra de cálculo é compartilhada entre consultas individuais e em lote.

## API

| Método | Rota | Uso |
| --- | --- | --- |
| GET | `/health` | Confirma que a aplicação iniciou |
| GET | `/filtros/opcoes` | Lista categorias presentes na base |
| GET | `/contratos/custo-medio` | Consulta com filtros opcionais |
| POST | `/contratos/processar-planilha` | Recebe arquivo multipart no campo `file` |

```bash
curl "http://127.0.0.1:8000/contratos/custo-medio?cidade=Curitiba&uf=PR&velocidade=1000"
curl -F "file=@frontend/exemplo_consultas.csv" \
  http://127.0.0.1:8000/contratos/processar-planilha -o resultado_custos.csv
```

## Testes e qualidade

Com o ambiente virtual ativo:

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pytest -q
python -m ruff check backend
python -m ruff format --check backend
python -m pip check
python -m pip_audit -r backend/requirements.txt --no-deps --disable-pip
```

Os testes cobrem médias conhecidas, normalização, preservação dos filtros na alternativa regional, números inválidos, codificações e delimitadores, equivalência entre lote e consulta, exportação de Unicode, neutralização de fórmulas, limites de upload, arquivos privados fora da interface e falha de inicialização com base inválida.

O frontend não exige build. Uma verificação opcional de sintaxe, caso Node.js esteja instalado, é `node --check frontend/src/services/script.js`.

## Limitações e próximos passos

- A amostra demonstrativa é pequena e não estima preços reais ou tendências de mercado.
- A base fica em memória e as consultas percorrem seus registros. Não há persistência de uploads, edição de contratos ou atualização automática.
- Não há autenticação, autorização ou limitação de requisições por usuário. A execução documentada é local; uma implantação pública com dados reais exige controles adicionais.
- Testes de interface completos em vários navegadores, autenticação e armazenamento persistente são possibilidades futuras, não funcionalidades implementadas.

## Publicação e direitos

A edição atual contém dados sintéticos e referências genéricas. O arquivo `backend/contratos.csv` contém exclusivamente dados artificiais. A planilha original deve permanecer em `private/contratos.csv`, fora do Git e do contexto Docker; nunca substitua a versão demonstrativa pela original no caminho público. Somente `backend/contratos.csv` e `frontend/exemplo_consultas.csv`, ambos sintéticos, são permitidos entre as planilhas versionadas. `.env`, bases locais, logs, chaves e resultados exportados estão excluídos por regras do `.gitignore`, que não removem arquivos já versionados.

Na preparação do envio ao GitHub, o histórico remoto foi inspecionado por padrões de credenciais e chaves privadas, sem ocorrências nessas regras de busca. Essa verificação não constitui uma auditoria completa. O histórico publicado foi reescrito para remover as versões confidenciais de `contratos.csv` e o banco legado dos commits antigos. Clones anteriores devem ser substituídos por novos clones para evitar reintroduzir esses dados. A remoção de referências não garante a exclusão de caches do GitHub ou cópias de terceiros; a purga de dados residuais do servidor deve ser solicitada ao suporte do GitHub. Caso credenciais já tenham sido expostas, removê-las dos arquivos atuais não substitui sua revogação ou rotação.

Não foi encontrada licença no material original. Nenhuma licença ou cessão de direitos foi atribuída nesta revisão. Confirme a autorização para divulgar o código e o contexto de origem antes de publicar: substituir dados e nomes não estabelece direitos de distribuição.

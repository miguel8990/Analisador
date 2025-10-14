Analisador de Imagens de Satélite com Python/Flask
Resumo
API RESTful desenvolvida em Python com o framework Flask, projetada para a análise de imagens de satélite no formato GeoTIFF, com foco em aplicações para agricultura de precisão.

Este projeto demonstra um fluxo de trabalho completo, desde a obtenção de dados de satélite na nuvem (Google Earth Engine) até a análise, interpretação e visualização de dados através de uma API local.

Funcionalidades
Cálculo de Índices Espectrais:

NDVI (Índice de Vegetação por Diferença Normalizada)

GNDVI (Índice de Vegetação por Diferença Normalizada com a banda Verde)

NDWI (Índice de Água por Diferença Normalizada)

Análise Estatística: Extração de métricas como média, mínimo, máximo e desvio padrão para cada índice calculado.

Zoneamento Agrícola: Classificação da área analisada em zonas de "Vigor Baixo", "Médio" e "Alto" com base nos valores de NDVI.

Interpretações Dinâmicas: Geração de diagnósticos textuais baseados em limiares pré-definidos sobre os resultados numéricos.

Geração de Imagem RGB: Endpoint para conversão de dados brutos de um GeoTIFF multibanda em uma imagem visual (PNG).

Tecnologias
Backend: Python 3, Flask

Análise Geoespacial: Rasterio, NumPy

Processamento de Imagem: Pillow

Fonte de Dados: Google Earth Engine (para exportação de imagens Sentinel-2)

Cliente de API: Postman

Arquitetura do Fluxo de Trabalho
O projeto opera em um fluxo de duas etapas principais:

Obtenção de Dados (Google Earth Engine):

Scripts são utilizados no Google Earth Engine para filtrar e selecionar imagens do satélite Sentinel-2 sobre uma área de interesse.

As bandas espectrais de interesse (ex: Azul, Verde, Vermelho, Infravermelho Próximo) são selecionadas.

A imagem resultante é exportada como um arquivo GeoTIFF para o Google Drive e transferida para o ambiente local.

Análise via API (Python/Flask):

O servidor Flask é executado no ambiente local.

O arquivo GeoTIFF é submetido a um dos endpoints da API através de uma requisição POST.

A API processa o arquivo em memória, executa os cálculos e retorna uma resposta em formato JSON com a análise completa ou um arquivo de imagem PNG.

Instruções de Uso
Pré-requisitos
Python 3.9 ou superior

Git

Instalação
Clone o repositório:

Bash

git clone [URL_DO_SEU_REPOSITORIO_AQUI]
cd [NOME_DA_PASTA_DO_PROJETO]
Crie e ative um ambiente virtual:

Bash

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
Instale as dependências a partir do arquivo requirements.txt:

Bash

pip install -r requirements.txt
Execução
Inicie o servidor Flask:

Bash

flask run
O servidor estará disponível em http://127.0.0.1:5000. Utilize um cliente de API para realizar as requisições.

Endpoints da API
1. Análise Agrícola Completa
URL: /analisar_lavoura

Método: POST

Entrada: Requisição multipart/form-data com uma chave imagem contendo o arquivo GeoTIFF de 4 bandas (Azul, Verde, Vermelho, NIR).

Resposta de Sucesso (200 OK): Um objeto JSON contendo as estatísticas, zoneamento e interpretações dos índices.

JSON

{
    "analise_ndvi": { ... },
    "analise_umidade_ndwi": { ... },
    "mensagem": "Análise da lavoura concluída!"
}
2. Geração de Imagem RGB
URL: /gerar_imagem_rgb

Método: POST

Entrada: Requisição multipart/form-data com uma chave imagem contendo um arquivo GeoTIFF com pelo menos 3 bandas (Azul, Verde, Vermelho).

Resposta de Sucesso (200 OK): Retorna um arquivo de imagem no formato image/png.

Licença
Este projeto está distribuído sob a licença MIT. Consulte o arquivo LICENSE para mais detalhes.


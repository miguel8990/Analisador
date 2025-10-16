# Analisador de Lavouras com Google Earth Engine e Flask

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![Framework](https://img.shields.io/badge/Framework-Flask-black.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Resumo

Este projeto demonstra um fluxo de trabalho automatizado para agricultura de precisão, combinando o poder do Google Earth Engine (GEE) para obtenção de dados de satélite com uma API RESTful local desenvolvida em Python/Flask para análise geoespacial.

O sistema é composto por dois componentes principais:
1.  **A API (`app.py`):** Um servidor Flask que recebe imagens GeoTIFF e realiza análises complexas, calculando índices espectrais, estatísticas e zoneamento.
2.  **O Cliente (`requisidor.py`):** Um script Python que automatiza todo o processo: define uma área de interesse, busca a imagem mais recente no GEE, descarrega-a diretamente para a memória e envia-a para a API local para análise.

## Visão Geral do Fluxo de Trabalho

O fluxo de trabalho é totalmente automatizado e não requer downloads manuais:

1.  O **Cliente (`requisidor.py`)** é executado.
2.  O utilizador define parâmetros-chave no script (latitude, longitude, raio).
3.  O cliente contacta o **Google Earth Engine (GEE)**, encontra a melhor imagem Sentinel-2 para a área e data definidas, e gera uma URL de download direto.
4.  O cliente descarrega a imagem em memória (como um buffer de bytes).
5.  A imagem é enviada via requisição POST para a **API Flask (`app.py`)** local.
6.  A **API** recebe o GeoTIFF, usa `Rasterio` e `NumPy` para processá-lo e calcula todos os índices.
7.  A **API** retorna um relatório completo em formato **JSON** para o cliente.
8.  O **Cliente** recebe o JSON, exibe-o formatado no terminal e gera um **mapa interativo (`.html`)** com os resultados, que abre automaticamente no navegador.

## Funcionalidades

### API (Servidor - `app.py`)

* **Cálculo de Índices Espectrais:**
    * `NDVI` (Índice de Vigor)
    * `GNDVI` (Índice de Clorofila)
    * `NDWI` (Índice de Umidade da Folha - baseado em NIR/SWIR)
    * `NDMI` (Índice de Umidade da Vegetação)
    * E outros, dependendo das bandas fornecidas.
* **Análise Estatística:** Extração de média, mínimo, máximo e desvio padrão para cada índice.
* **Zoneamento Agrícola:** Classificação automática da área em zonas de "Vigor Baixo", "Médio" e "Alto" (baseado em NDVI).
* **Interpretações Dinâmicas:** Geração de diagnósticos em texto (ex: "Risco de Fogo Baixo") baseados nos resultados numéricos.
* **Endpoint de Imagem RGB:** Converte um GeoTIFF multibanda numa imagem PNG visual.

### Cliente (`requisidor.py`)

* **Definição Paramétrica da Área:** Fácil configuração da área de interesse (AOI) através de variáveis de latitude, longitude e raio.
* **Automação GEE:** Conexão direta com a API do Google Earth Engine para download de imagens sem a necessidade de usar o Google Drive.
* **Análise em Memória:** Todo o fluxo de download e upload da imagem ocorre em memória, sem salvar ficheiros `.tif` intermédios no disco.
* **Visualização de Resultados:**
    * Impressão formatada ("pretty-print") da resposta JSON no terminal.
    * Geração automática de um **mapa interativo (Folium)** que mostra a área analisada, um pino central e um *popup* com o relatório JSON completo.

## Tecnologias Utilizadas

* **Backend:** Python 3, Flask
* **Análise Geoespacial:** Rasterio, NumPy
* **Fonte de Dados na Nuvem:** Google Earth Engine API (`earthengine-api`)
* **Visualização de Mapas:** Folium
* **Processamento de Imagem:** Pillow
* **Cliente HTTP:** Requests

## Configuração e Instalação

Siga estes passos para configurar o projeto no seu ambiente local.

### 1. Pré-requisitos

* Python 3.9 ou superior
* Git
* Uma conta Google com o [Google Earth Engine](https://earthengine.google.com/) ativado.
* Um Projeto [Google Cloud Platform](https://console.cloud.google.com/) com a **"Earth Engine API"** ativada.

### 2. Instalação

1.  Clone o repositório:
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO_AQUI]
    cd [NOME_DA_PASTA_DO_PROJETO]
    ```

2.  Crie e ative um ambiente virtual:
    * **macOS/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    * **Windows (PowerShell):**
        ```bash
        python -m venv venv
        .\venv\Scripts\Activate.ps1
        ```

3.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Autenticação Google

O projeto requer autenticação para aceder ao Google Earth Engine e ao seu projeto Google Cloud.

1.  **Autenticar no GEE:**
    * O script `requisidor.py` tentará fazer isso automaticamente na primeira execução (`ee.Authenticate()`), abrindo uma janela do navegador para login.

2.  **Configurar o Projeto Google Cloud:**
    * Encontre o **ID do seu Projeto** no Google Cloud Console.
    * Este ID **não deve** ser escrito no código. Ele deve ser definido como uma **variável de ambiente** antes de executar o script.

## Como Executar

O projeto requer dois terminais a funcionar em simultâneo.

### Terminal 1: Iniciar o Servidor API

Neste terminal, vamos iniciar o servidor Flask.

```bash
# Ative o ambiente virtual (se ainda não o fez)
# source venv/bin/activate

# Inicie a API
flask run

O servidor estará disponível em http://127.0.0.1:5000. Deixe este terminal a funcionar.

Terminal 2: Executar o Cliente
Neste novo terminal, vamos definir a variável de ambiente e executar o script cliente.

Ative o ambiente virtual:

(Ex: .\venv\Scripts\Activate.ps1)

Defina a variável de ambiente com o seu ID do Projeto Google:

Windows (PowerShell):

PowerShell

$env:GEE_PROJECT = "seu-id-de-projeto-aqui"
macOS/Linux:

Bash

export GEE_PROJECT="seu-id-de-projeto-aqui"
(Opcional) Edite o ficheiro requisidor.py para alterar as variáveis latitude_central, longitude_central ou raio_em_metros ao seu gosto.

Execute o script cliente:

Bash

python requisidor.py
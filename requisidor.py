import ee
import time
import requests
import io
import json
import os

# --- CONFIGURAÇÕES ---
# Endereço da sua API de análise local que está a ser executada
API_URL = "http://127.0.0.1:5000/analisar_lote"


# --- FUNÇÕES AUXILIARES ---

def obter_imagem_diretamente_do_gee(regiao):
    """
    Busca a imagem no GEE e descarrega-a diretamente para a memória
    através de uma URL de download.

    Argumentos:
        regiao (ee.Geometry): A área de interesse definida para a busca da imagem.

    Retorna:
        io.BytesIO: Um buffer em memória com os dados da imagem, ou None se falhar.
    """
    print(">>> Passo 1: A contactar o Google Earth Engine...")
    try:
        # 1. Encontrar a melhor imagem na coleção do Sentinel-2
        imagem = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(regiao) \
            .filterDate('2025-01-01', '2025-10-15') \
            .sort('CLOUDY_PIXEL_PERCENTAGE') \
            .first()

        # 2. Selecionar as bandas de interesse (Verde, Vermelho, NIR, SWIR 1)
        imagem_para_api = imagem.select(['B3', 'B4', 'B8', 'B11'])

        # 3. Definir os parâmetros para o download
        params_download = {
            'scale': 10,  # Resolução em metros. GEE irá reamostrar a B11 (20m) para 10m.
            'region': regiao.getInfo()['coordinates'],  # Usa a geometria da região definida
            'format': 'GeoTIFF'  # Formato do ficheiro de imagem
        }

        # 4. Obter a URL de download do GEE
        print("A aguardar a geração da URL pelo GEE...")
        url = imagem_para_api.getDownloadURL(params_download)
        print(">>> URL gerada com sucesso!")

        # 5. Descarregar a imagem diretamente da URL para a memória
        print(f">>> Passo 2: A descarregar a imagem...")
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            print(">>> Download direto concluído!")
            buffer_da_imagem = io.BytesIO(response.content)
            buffer_da_imagem.seek(0)
            return buffer_da_imagem
        else:
            print(f"!!! Falha ao descarregar a imagem. O GEE disse: {response.text}")
            return None

    except ee.ee_exception.EEException as e:
        print(f"!!! Ocorreu um erro ao comunicar com o GEE: {e}")
        print("Verifique se a sua área e datas têm imagens disponíveis ou se a autenticação é válida.")
        return None
    except Exception as e:
        print(f"!!! Ocorreu um erro inesperado: {e}")
        return None


def enviar_para_api(buffer_da_imagem, nome_ficheiro):
    """Envia a imagem em memória para a API local e imprime a resposta."""
    print(">>> Passo 3: A enviar a imagem para a API de análise local...")
    files = {'imagem': (f'{nome_ficheiro}.tif', buffer_da_imagem, 'image/tiff')}
    try:
        response = requests.post(API_URL, files=files)
        if response.status_code == 200:
            print(">>> Análise recebida com sucesso da API!")
            print("\n--- RESULTADO DA ANÁLISE ---")
            dados_analise = response.json()
            print(json.dumps(dados_analise, indent=4, ensure_ascii=False))
        else:
            print(f"!!! A API retornou um erro: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        print("!!! ERRO DE CONEXÃO: Não foi possível conectar à API.")
        print(f"   Verifique se a sua aplicação Flask está a ser executada em {API_URL}")


# --- SCRIPT PRINCIPAL ---
if __name__ == '__main__':
    # Autenticar no GEE (só é necessário na primeira execução ou se a autenticação expirar)


    try:
        GEE_PROJECT_ID = os.environ.get('GEE_PROJECT')
        if not GEE_PROJECT_ID:
            raise KeyError
    except KeyError:
        print("!!! ERRO DE CONFIGURAÇÃO !!!")
        print("A variável de ambiente 'GEE_PROJECT' não foi definida.")
        print("Defina-a com o seu ID do Projeto do Google Cloud antes de executar.")
        exit()  # Encerra o script se a variável não estiver definida
    try:
        # A inicialização verifica se as credenciais já existem
        ee.Initialize(project=GEE_PROJECT_ID)
    except Exception as e:
        print("Autenticação no GEE necessária. A executar ee.Authenticate()...")
        # Se falhar, o fluxo de autenticação é iniciado
        ee.Authenticate()
        ee.Initialize()

    # --------------------------------------------------------------------------
    # --- PARÂMETROS DE ANÁLISE (ALTERE ESTES VALORES CONFORME NECESSÁRIO) ---
    latitude_central = -20.9876686
    longitude_central = -89.503267
    raio_em_metros = 300
    # --------------------------------------------------------------------------

    # 1. Definir a área de interesse usando as variáveis acima
    # A ordem no GEE é sempre (Longitude, Latitude)
    print(f"A definir a área de interesse com um raio de {raio_em_metros}m.")
    ponto_central = ee.Geometry.Point(longitude_central, latitude_central)
    area_de_interesse = ponto_central.buffer(raio_em_metros)

    # 2. Obter a imagem diretamente do GEE
    buffer_da_imagem = obter_imagem_diretamente_do_gee(area_de_interesse)

    # 3. Se a imagem foi obtida com sucesso, enviar para a API
    if buffer_da_imagem:
        # Criar um nome de ficheiro único para a API
        nome_do_ficheiro_para_api = f"analise_direta_{int(time.time())}"
        enviar_para_api(buffer_da_imagem, nome_do_ficheiro_para_api)
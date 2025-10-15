from flask import Flask, request, jsonify
import rasterio
import numpy as np

app = Flask(__name__)


# --- FUNÇÕES DE INTERPRETAÇÃO (SEM ALTERAÇÃO) ---
def interpretar_estatisticas_ndvi(stats_ndvi):
    media = stats_ndvi['media']
    desvio_padrao = stats_ndvi['desvio_padrao']
    if media < 0.25:
        texto_media = f"A média do NDVI ({media:.2f}) é muito baixa, indicando solo exposto ou cultura em estágio inicialíssimo."
    elif 0.25 <= media < 0.5:
        texto_media = f"A média do NDVI ({media:.2f}) indica que a cultura está em fase de desenvolvimento vegetativo."
    else:
        texto_media = f"A média do NDVI ({media:.2f}) é alta, indicando uma lavoura com bom vigor e dossel bem desenvolvido."
    if desvio_padrao > 0.2:
        texto_desvio = f"ALERTA: O desvio padrão ({desvio_padrao:.2f}) é alto, sugerindo alta desuniformidade. Recomenda-se investigação a campo."
    elif 0.1 <= desvio_padrao <= 0.2:
        texto_desvio = f"O desvio padrão ({desvio_padrao:.2f}) é moderado, indicando alguma variabilidade no talhão."
    else:
        texto_desvio = f"O desvio padrão ({desvio_padrao:.2f}) é baixo, o que é um ótimo sinal de uniformidade."
    return f"{texto_media} {texto_desvio}"


def interpretar_umidade_ndwi(stats_ndwi):
    media = stats_ndwi['media']
    desvio_padrao = stats_ndwi['desvio_padrao']
    if media < -0.1:
        texto_media = f"A média do NDWI ({media:.2f}) é negativa, indicando solo seco ou vegetação com baixo teor de umidade."
    elif -0.1 <= media < 0.2:
        texto_media = f"A média do NDWI ({media:.2f}) sugere umidade adequada no talhão."
    else:
        texto_media = f"A média do NDWI ({media:.2f}) é alta, podendo indicar solo saturado ou presença de corpos d'água."
    if desvio_padrao > 0.15:
        texto_desvio = f"ALERTA: O desvio padrão ({desvio_padrao:.2f}) é alto, indicando grande variabilidade na umidade. Pode haver falhas na irrigação."
    else:
        texto_desvio = f"O desvio padrão ({desvio_padrao:.2f}) é baixo, sugerindo umidade uniforme na área."
    return f"{texto_media} {texto_desvio}"


def interpretar_savi(stats_savi):
    """Gera um texto interpretativo para as estatísticas do SAVI."""
    media = stats_savi['media']

    # Limiares para o SAVI são similares aos do NDVI, mas a interpretação é focada
    # na sua capacidade de lidar com o efeito do solo.
    if media < 0.2:
        texto_interpretacao = (f"O SAVI médio ({media:.2f}) é muito baixo, indicando uma forte "
                               f"predominância de solo exposto na área analisada.")
    elif 0.2 <= media < 0.4:
        texto_interpretacao = (f"O SAVI médio ({media:.2f}) sugere uma vegetação esparsa ou em estágio inicial. "
                               f"Nesta fase, o SAVI tende a ser um indicador mais preciso que o NDVI, "
                               f"pois minimiza a interferência do brilho do solo.")
    else:  # media >= 0.4
        texto_interpretacao = (f"O SAVI médio ({media:.2f}) indica uma cobertura vegetal moderada a densa. "
                               f"Neste ponto, com o dossel mais fechado, os valores de SAVI e NDVI "
                               f"tendem a ser bastante similares.")

    return texto_interpretacao

def interpretar_delta(delta_stats):
    delta_ndvi = delta_stats['delta_ndvi_medio']
    if delta_ndvi > 0.05:
        return f"Evolução positiva: Houve um aumento significativo de {delta_ndvi:.2f} no NDVI médio, indicando bom desenvolvimento da cultura."
    elif delta_ndvi < -0.05:
        return f"ALERTA: Houve uma queda significativa de {abs(delta_ndvi):.2f} no NDVI médio. A lavoura pode estar sofrendo de estresse ou senescência."
    else:
        return f"Estabilidade: A variação do NDVI médio ({delta_ndvi:.2f}) foi mínima, indicando que a lavoura se manteve estável entre as duas datas."


# --- LÓGICA DE ANÁLISE REUTILIZÁVEL ---
def processar_imagem_individual(arquivo_geotiff):
    """Processa um único ficheiro de imagem e devolve um dicionário com a análise completa."""
    with rasterio.open(arquivo_geotiff) as src:

        # Assumindo que o ficheiro está na ordem: 1:Vermelho, 2:Verde, 3:NIR
        banda_vermelho = src.read(1).astype(float) / 10000.0
        banda_verde = src.read(2).astype(float) / 10000.0
        banda_nir = src.read(3).astype(float) / 10000.0

        np.seterr(divide='ignore', invalid='ignore')


        ndvi = np.nan_to_num((banda_nir - banda_vermelho) / (banda_nir + banda_vermelho))
        ndwi = np.nan_to_num((banda_verde - banda_nir) / (banda_verde + banda_nir))
        gndvi = np.nan_to_num((banda_nir - banda_verde) / (banda_nir + banda_verde))
        L = 0.5
        savi = np.nan_to_num(((banda_nir - banda_vermelho) / (banda_nir + banda_vermelho + L)) * (1 + L))



        # --- Estatísticas ---
        estatisticas_ndvi = {
            'media': round(np.mean(ndvi), 4), 'minimo': round(np.min(ndvi), 4),
            'maximo': round(np.max(ndvi), 4), 'desvio_padrao': round(np.std(ndvi), 4)
        }
        estatisticas_ndwi = {
            'media': round(np.mean(ndwi), 4), 'minimo': round(np.min(ndwi), 4),
            'maximo': round(np.max(ndwi), 4), 'desvio_padrao': round(np.std(ndwi), 4)
        }
        estatisticas_gndvi = {
            'media': round(np.mean(gndvi), 4), 'minimo': round(np.min(gndvi), 4),
            'maximo': round(np.max(gndvi), 4), 'desvio_padrao': round(np.std(gndvi), 4)
        }
        estatisticas_savi = {
            'media': round(np.mean(savi), 4), 'minimo': round(np.min(savi), 4),
            'maximo': round(np.max(savi), 4), 'desvio_padrao': round(np.std(savi), 4)
        }

        # --- Zoneamento ---
        total_pixels = ndvi.size
        zoneamento = {
            'vigor_baixo': {'percentual': round(np.count_nonzero(ndvi < 0.33) / total_pixels * 100, 2)},
            'vigor_medio': {
                'percentual': round(np.count_nonzero((ndvi >= 0.33) & (ndvi < 0.66)) / total_pixels * 100, 2)},
            'vigor_alto': {'percentual': round(np.count_nonzero(ndvi >= 0.66) / total_pixels * 100, 2)}
        }

        # --- Adicionar Interpretações ---
        estatisticas_ndvi['interpretacao_geral'] = interpretar_estatisticas_ndvi(estatisticas_ndvi)
        estatisticas_ndwi['interpretacao_geral'] = interpretar_umidade_ndwi(estatisticas_ndwi)
        estatisticas_savi['interpretacao_geral'] = interpretar_savi(estatisticas_savi)

        # --- Montar o resultado para esta imagem ---
        return {
            'nome_arquivo': arquivo_geotiff.filename,
            'analise_ndvi': {'estatisticas': estatisticas_ndvi, 'zoneamento': zoneamento},
            'analise_gndvi': {'estatisticas': estatisticas_gndvi},
            'analise_savi': {'estatisticas': estatisticas_savi},
            'analise_umidade_ndwi': {'estatisticas': estatisticas_ndwi}
        }


@app.route('/analisar_lote', methods=['POST'])
def analisar_lote():
    """Recebe múltiplos arquivos e retorna uma lista de análises."""
    arquivos_recebidos = request.files.getlist('imagem')
    if not arquivos_recebidos or not arquivos_recebidos[0].filename:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

    lista_de_resultados = []
    # Faz um loop em cada arquivo recebido e processa individualmente
    for arquivo in arquivos_recebidos:
        try:
            resultado_individual = processar_imagem_individual(arquivo)
            lista_de_resultados.append(resultado_individual)
        except Exception as e:
            lista_de_resultados.append({
                'nome_arquivo': arquivo.filename,
                'erro': f'Falha no processamento: {e}'
            })
    return jsonify(lista_de_resultados), 200



@app.route('/analisar_temporal', methods=['POST'])
def analisar_temporal():
    """Recebe uma imagem de 'antes' e 'depois' e calcula o delta."""
    if 'imagem_antes' not in request.files or 'imagem_depois' not in request.files:
        return jsonify(
            {'erro': "É necessário enviar dois arquivos com as chaves 'imagem_antes' e 'imagem_depois'."}), 400

    imagem_antes = request.files['imagem_antes']
    imagem_depois = request.files['imagem_depois']

    try:
        # Processa cada imagem para obter suas estatísticas
        analise_antes = processar_imagem_individual(imagem_antes)
        analise_depois = processar_imagem_individual(imagem_depois)

        # Calcula o delta para as métricas principais
        delta_stats = {
            'delta_ndvi_medio': round(
                analise_depois['analise_ndvi']['estatisticas']['media'] - analise_antes['analise_ndvi']['estatisticas'][
                    'media'], 4),
            'delta_ndwi_medio': round(analise_depois['analise_umidade_ndwi']['estatisticas']['media'] -
                                      analise_antes['analise_umidade_ndwi']['estatisticas']['media'], 4),
        }
        delta_stats['interpretacao'] = interpretar_delta(delta_stats)

        # Monta a resposta final
        resposta_final = {
            'mensagem': 'Análise temporal concluída com sucesso.',
            'analise_temporal': delta_stats,
            'dados_imagem_antes': analise_antes,
            'dados_imagem_depois': analise_depois
        }
        return jsonify(resposta_final), 200

    except Exception as e:
        return jsonify({'erro': f'Ocorreu um erro no processamento temporal: {e}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
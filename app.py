from flask import Flask, request, jsonify
import rasterio
import numpy as np


def interpretar_estatisticas_ndvi(stats_ndvi):
    """Gera um texto interpretativo para as estatísticas do NDVI."""
    media = stats_ndvi['media']
    desvio_padrao = stats_ndvi['desvio_padrao']

    # Interpretando a média do NDVI
    if media < 0.25:
        texto_media = "A média do NDVI (%.2f) é muito baixa, indicando solo exposto ou cultura em estágio inicialíssimo." % media
    elif 0.25 <= media < 0.5:
        texto_media = "A média do NDVI (%.2f) indica que a cultura está em fase de desenvolvimento vegetativo." % media
    else:  # media >= 0.5
        texto_media = "A média do NDVI (%.2f) é alta, indicando uma lavoura com bom vigor e dossel bem desenvolvido." % media

    # Interpretando o desvio padrão do NDVI
    if desvio_padrao > 0.2:
        texto_desvio = "ALERTA: O desvio padrão (%.2f) é alto, sugerindo alta desuniformidade na lavoura. Recomenda-se investigação a campo." % desvio_padrao
    elif 0.1 <= desvio_padrao <= 0.2:
        texto_desvio = "O desvio padrão (%.2f) é moderado, indicando alguma variabilidade no talhão." % desvio_padrao
    else:  # desvio_padrao < 0.1
        texto_desvio = "O desvio padrão (%.2f) é baixo, o que é um ótimo sinal de uniformidade da lavoura." % desvio_padrao

    return f"{texto_media} {texto_desvio}"


def interpretar_umidade_ndwi(stats_ndwi):
    """Gera um texto interpretativo para as estatísticas do NDWI."""
    media = stats_ndwi['media']
    desvio_padrao = stats_ndwi['desvio_padrao']

    # Interpretando a média do NDWI
    if media < -0.1:
        texto_media = "A média do NDWI (%.2f) é negativa, indicando solo seco ou vegetação com baixo teor de umidade." % media
    elif -0.1 <= media < 0.2:
        texto_media = "A média do NDWI (%.2f) sugere umidade adequada no talhão." % media
    else:  # media >= 0.2
        texto_media = "A média do NDWI (%.2f) é alta, podendo indicar solo saturado ou presença de corpos d'água." % media

    # Interpretando o desvio padrão do NDWI
    if desvio_padrao > 0.15:
        texto_desvio = "ALERTA: O desvio padrão (%.2f) é alto, indicando grande variabilidade na umidade. Pode haver falhas na irrigação." % desvio_padrao
    else:
        texto_desvio = "O desvio padrão (%.2f) é baixo, sugerindo umidade uniforme na área." % desvio_padrao

    return f"{texto_media} {texto_desvio}"

app = Flask(__name__)


@app.route('/analisar_satelite', methods=['POST'])
def analisar_lavoura():
    if 'imagem' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo GeoTIFF enviado'}), 400

    arquivo_geotiff = request.files['imagem']

    if arquivo_geotiff.filename == '':
        return jsonify({'erro': 'Nome de arquivo vazio'}), 400

    try:
        with rasterio.open(arquivo_geotiff) as src:
            # Lendo as 4 bandas do arquivo (Azul, Verde, Vermelho, NIR)
            banda_azul = src.read(1).astype(float)
            banda_verde = src.read(2).astype(float)
            banda_vermelho = src.read(3).astype(float)
            banda_nir = src.read(4).astype(float)

            # --- 1. CÁLCULO DO NDVI ---
            np.seterr(divide='ignore', invalid='ignore')
            ndvi = (banda_nir - banda_vermelho) / (banda_nir + banda_vermelho)
            ndvi = np.nan_to_num(ndvi)  # Remove valores inválidos

            # --- 2. ANÁLISE ESTATÍSTICA DETALHADA DO NDVI ---
            estatisticas_ndvi = {
                'media': round(np.mean(ndvi), 4),
                'minimo': round(np.min(ndvi), 4),
                'maximo': round(np.max(ndvi), 4),
                'desvio_padrao': round(np.std(ndvi), 4)
            }

            # --- 3. ZONEAMENTO DA LAVOURA (EM 3 NÍVEIS) ---
            total_pixels = ndvi.size
            zona_baixa = np.count_nonzero(ndvi < 0.33)
            zona_media = np.count_nonzero((ndvi >= 0.33) & (ndvi < 0.66))
            zona_alta = np.count_nonzero(ndvi >= 0.66)

            zoneamento = {
                'vigor_baixo': {'percentual': round((zona_baixa / total_pixels) * 100, 2)},
                'vigor_medio': {'percentual': round((zona_media / total_pixels) * 100, 2)},
                'vigor_alto': {'percentual': round((zona_alta / total_pixels) * 100, 2)},
                'interpretacao': 'Percentual da área em cada classe de vigor vegetativo.'
            }

            # --- 4. CÁLCULO DO NDWI (ÍNDICE DE ÁGUA) ---
            ndwi = (banda_verde - banda_nir) / (banda_verde + banda_nir)
            ndwi = np.nan_to_num(ndwi)

            estatisticas_ndwi = {
                'media': round(np.mean(ndwi), 4),
                'minimo': round(np.min(ndwi), 4),
                'maximo': round(np.max(ndwi), 4),
                'desvio_padrao': round(np.std(ndwi), 4),
                'interpretacao': 'Valores mais altos indicam maior umidade ou presença de água.'
            }

            gndvi = (banda_nir - banda_verde) / (banda_nir + banda_verde)
            gnvdi = np.nan_to_num(gndvi)

            estatisticas_gndvi = {
                'media': round(np.mean(gnvdi), 4),
                'minimo': round(np.min(gndvi), 4),
                'maximo': round(np.max(gnvdi), 4),
                'desvio_padrao': round(np.std(gndvi), 4),
            }
            # --- Adicionando as interpretações dinâmicas ---
            interpretacao_ndvi = interpretar_estatisticas_ndvi(estatisticas_ndvi)
            interpretacao_ndwi = interpretar_umidade_ndwi(estatisticas_ndwi)

            # Adiciona as novas interpretações aos dicionários
            estatisticas_ndvi['interpretacao_geral'] = interpretacao_ndvi
            estatisticas_ndwi['interpretacao_geral'] = interpretacao_ndwi

            # --- Montando a Resposta Final ATUALIZADA ---
            resposta = {
                'mensagem': 'Análise da lavoura concluída!',
                'analise_ndvi': {
                    'estatisticas': estatisticas_ndvi,
                    'zoneamento': zoneamento
                },
                'analise_umidade_ndwi': estatisticas_ndwi
            }
            return jsonify(resposta), 200

    except Exception as e:
        return jsonify({'erro': 'Ocorreu um erro no processamento', 'detalhe': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
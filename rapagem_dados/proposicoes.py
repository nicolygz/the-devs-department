import json
import aiohttp
from datetime import datetime
from tqdm.asyncio import tqdm_asyncio
import threading
import requests
import asyncio
import threading
import time
import os


# Função para verificar a resposta e ajustar a quantidade (`qtd`) de registros retornados
def ajustar_quantidade(url_base, ano, tipo_id):
    tentativas = [100, 50, 20, 16, 10]  # Quantidades a tentar
    for qtd in tentativas:
        url = f'{url_base}&qtd={qtd}&ano={ano}&tipoId={tipo_id}'
        resposta = requests.get(url).json()
        
        # Verifica se a estrutura 'Paginacao' existe na resposta
        if resposta.get('Paginacao'):
            print(f'Usando qtd={qtd} para tipo {tipo_id} e ano {ano}')
            return resposta, qtd
    print("Nenhuma quantidade válida encontrada.")
    return None, None

# Função assíncrona para realizar as requisições de cada página
async def criar_requisicao(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            return await response.json()

# Função principal assíncrona para processar as requisições das páginas restantes
async def coletar_dados(total_paginas, url_base):
    async with aiohttp.ClientSession() as session:
        list_json = []
        tasks = [
            criar_requisicao(session, f"{url_base}&pag={i}") for i in range(1, total_paginas + 1)
        ]

        # Usa tqdm para acompanhar o progresso
        for task in tqdm_asyncio.as_completed(tasks, desc="Processando páginas", unit="página"):
            pagina = await task
            if pagina and pagina['total'] != 0:

                for proposicao in pagina['Data']:
                    proposicao = {
                        'id_prop': proposicao['id'],
                        'processo': proposicao['processo'],
                        'protocolo': proposicao['protocolo'],
                        'ano': proposicao['ano'],
                        'numero': proposicao['numero'],
                        'tipo': proposicao['tipo'],
                        'assunto': proposicao['assunto'],
                        'data': proposicao['data'],
                        'nomeRazao': proposicao['AutorRequerenteDados']['nomeRazao'],
                        'autorId': proposicao['AutorRequerenteDados']['autorId'],
                        'situacao': proposicao['situacao'],
                        'requerimento_num': '-',
                    }
                    if not proposicao['nomeRazao'] == 'Poder Executivo':
                        list_json.append(proposicao)

        return list_json
        
def indicador_processo():
    print("\nProcessando", end="")
    while not stop_event.is_set():
        print(".", end="", flush=True)
        time.sleep(1)
    print()  # Para pular para a nova linha após parar

def salvar_json(list_json, tipo):

    # Define o caminho relativo ao diretório do script
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'ArquivosJson', f'Dados{tipo}.json')

    try:
        # Salva os dados no arquivo JSON
        with open(file_path, encoding='utf-8', mode='w') as f:
            json.dump(list_json, f, indent=4, ensure_ascii=False)
        print("Lista salva com sucesso!")  # Mensagem de sucesso

    except Exception as e:
        print(f"Ocorreu um erro ao salvar a lista: {e}")  # Mensagem de erro

# Cria um evento de parada para a thread do indicador
stop_event = threading.Event()

# Inicia a thread do indicador
indicador_thread = threading.Thread(target=indicador_processo)
indicador_thread.start()

# Iniciando variáveis importantes
url_base = 'https://camarasempapel.camarasjc.sp.gov.br//api/publico/proposicao/?'
tipos_proposicao = [341, 348, 340]  # mocao, projeto de lei, requerimento

anos = [2021, 2022, 2023, 2024]  # Lista de anos

# Dicionário para mapear tipo_id para nomes
tipo_map = {
    340: "_Requerimento",
    341: "_Mocao",
    348: "_ProjetoLei"
}

for tipo_id in tipos_proposicao:
    list_json_total = []  # Reinicia a lista total para cada tipo de proposição
    for ano in anos:
        # Requisição inicial síncrona para obter a paginação
        
        resposta_inicial, qtd = ajustar_quantidade(url_base, ano, tipo_id)

        # Para o indicador assim que a resposta for recebida
        stop_event.set()
        indicador_thread.join()  # Aguarda a thread do indicador terminar

        # Processa a resposta
        if resposta_inicial and qtd:
            total_paginas = int(resposta_inicial['Paginacao']['quantidade'])
            print(f'\nTotal de páginas para tipo {tipo_id} e ano {ano} com qtd={qtd}: {total_paginas}')

            # Executa a função principal assíncrona
            list_json = asyncio.run(coletar_dados(total_paginas, f'{url_base}&ano={ano}&tipoId={tipo_id}&qtd={qtd}'))
            list_json_total.extend(list_json)  # Adiciona os dados coletados à lista total

        
        # Obter o sufixo do nome da propositura
        tipo = tipo_map.get(tipo_id, "")  # Obtém o tipo correspondente

    # SALVAR A LISTA PARA O TIPO ATUAL
    print(f"Salvando lista para o tipo {tipo}.\n")
    
    salvar_json(list_json_total, tipo)  # Salva a lista para o tipo atual
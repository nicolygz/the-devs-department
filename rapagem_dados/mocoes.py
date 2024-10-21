import json
import requests
import mysql.connector
from datetime import datetime

# Função principal para capturar moções de um intervalo de anos e salvar tudo em um único arquivo JSON
def get_mocoes_anos(inicio_ano, fim_ano):
    all_mocoes = []  # Lista para armazenar todas as moções de todos os anos
    
    for ano in range(inicio_ano, fim_ano + 1):  # Loop pelos anos de 2021 até 2024
        print(f"Buscando moções do ano {ano}...")
        url = f"https://camarasempapel.camarasjc.sp.gov.br//api/publico/proposicao/?qtd=100&tipoID=341&ano={ano}"
        listJson = get_mocoes(url)
        
        # Adiciona as moções do ano atual à lista geral
        all_mocoes.extend(listJson)
    
    # Salva todas as moções de todos os anos em um único arquivo JSON
    with open(f'rapagem_dados/ArquivosJson/dadosMocoes_2021_a_2024.json', encoding='utf-8', mode='w') as f:
        json.dump(all_mocoes, f, indent=4, ensure_ascii=False)
    
    print("Dados de 2021 até 2024 salvos com sucesso em um único arquivo.")

# Função para capturar moções de cada ano específico
def get_mocoes(url):
    listJson = []  # Lista para armazenar os dados coletados
    
    # Retorna o JSON da página inicial
    response = criar_requisicao(url)

    # Extrai a quantidade de páginas dentro do JSON
    qtd_paginas = response.get('Paginacao', {}).get('quantidade', 0)
    print(f"Total de páginas: {qtd_paginas}")
     
    # Inicia contador de páginas
    i = 1
    
    # Enquanto i estiver dentro do número de páginas
    while i <= int(qtd_paginas):
        try:
            # Monta URL para a página atual
            por_pagina = url + '&pag=' + str(i)
            print(f"Requisitando página: {por_pagina}")
        
            # Faz a requisição da página
            response_pag = criar_requisicao(por_pagina)
            
            # Captura as moções da página atual
            mocoes = response_pag.get('Data', [])
            
            # Itera sobre as moções e monta o dicionário com os dados
            for mocao in mocoes:
                try:
                    # Tratamento para campos que podem não existir
                    idProposicao = mocao.get('id', 'N/A')
                    processoNum = mocao.get('processo', 'N/A')
                    protocoloNum = mocao.get('protocolo', 'N/A')
                    numeroProp = mocao.get('numero', 'N/A')
                    tipoProposicao = mocao.get('tipo', 'N/A')
                    assuntoProposicao = mocao.get('assunto', 'Sem assunto')
                    dataProposicao = mocao.get('data', 'N/A')
                    situacaoProposicao = mocao.get('situacao', 'N/A')
                    autorProposicao = mocao.get('AutorRequerenteDados', {}).get('nomeRazao', 'N/A')
                    idAutorProp = mocao.get('AutorRequerenteDados', {}).get('autorId', 'N/A')

                    # Dicionário com todos os dados
                    dicionario = {
                        'ID': str(idProposicao),
                        'Numero Processo': str(processoNum),
                        'Numero Protocolo': str(protocoloNum),
                        'Numero Proposicao': str(numeroProp),
                        'Tipo': str(tipoProposicao),
                        'Assunto': str(assuntoProposicao),
                        'Data': str(dataProposicao),
                        'Autor': str(autorProposicao),
                        'Id Autor': str(idAutorProp),
                        'Situacao': str(situacaoProposicao)
                    }

                    # Adiciona o dicionário à lista
                    listJson.append(dicionario)

                except Exception as e:
                    print(f"Erro ao processar moção: {e}")
        
            # Próxima página
            i += 1

        except Exception as e:
            print(f"Erro na requisição da página {i}: {e}")
            break  # Quebra o loop em caso de erro

    return listJson

# Função para realizar a requisição HTTP
def criar_requisicao(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro na requisição: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Erro na conexão: {e}")
        return {}

# Chama a função para obter moções dos anos de 2021 a 2024 e salvar tudo em um único arquivo JSON
get_mocoes_anos(2021, 2024)

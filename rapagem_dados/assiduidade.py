import os
import requests
import json
import time
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
         port=os.getenv('MYSQL_PORT', 3306)
    )
    return connection

def get_api_assiduidade(ids):
    url = "https://camarasempapel.camarasjc.sp.gov.br/api/publico/parlamentar"

    all_results = [] 

    for ID in ids:
        params = {
            "qtd": 1,
            "parlamentarID": ID,
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()

            for parlamentar in data.get("parlamentares", []):
                parlamentar_id = parlamentar.get("parlamentarID")
                frequencia = parlamentar.get("frequenciaPlenario", [])
                anos_filtrados = range(2021, 2025)

                for ano in anos_filtrados:
                    presenca = 0
                    faltas = 0
                    justif = 0

                    # Coletar dados de presença, faltas e justificativas
                    for situacao in frequencia:
                        ano_data = next((item for item in situacao["frequenciaSituacaoAnos"] if item["ano"] == ano), None)
                        if ano_data:
                            quantidade = int(ano_data["quantidade"])
                            if situacao["frequenciaSituacaoNome"] == "Presente":
                                presenca = quantidade
                            elif situacao["frequenciaSituacaoNome"] == "Falta":
                                faltas = quantidade
                            elif situacao["frequenciaSituacaoNome"] == "Falta Justificada":
                                justif = quantidade

                    # Adiciona os dados ao resultado
                    all_results.append({
                        "ver_id": parlamentar_id,
                        "ano": ano,
                        "presenca": presenca,
                        "faltas": faltas,
                        "justif": justif
                    })

            print(f"Dados processados para o ID {ID}.")
        else:
            print(f"Erro ao fazer a solicitação para o ID {ID}: {response.status_code}")

        time.sleep(0.1)
    
    with open('rapagem_dados/assiduidades/assiduidade_total.json', 'w') as json_file:
        json.dump(all_results, json_file, indent=4)

    print("Todos os dados salvos em assiduidade_total.json.")
    return all_results


def get_assiduidade_totais(vereador_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    query = """
    SELECT 
        ver_id,
        SUM(faltas) AS faltas_totais,
        SUM(presenca) AS presencas_totais,
        SUM(justif) AS justificadas_totais
    FROM 
        assiduidade
    WHERE 
        ver_id = %s
    GROUP BY 
        ver_id;
    """
    
    cursor.execute(query, (vereador_id,))
    resultados = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    # Calcular a porcentagem de faltas
    for resultado in resultados:
        total_part = resultado['faltas_totais'] + resultado['presencas_totais'] + resultado['justificadas_totais']
        if total_part > 0:
            resultado['porcentagem_faltas'] = (resultado['faltas_totais'] / total_part) * 100
        else:
            resultado['porcentagem_faltas'] = 0

    return resultados

def get_menos_faltas(vereadores_ids):
    if isinstance(vereadores_ids, int):  # Verifica se é um único ID
        vereadores_ids = [vereadores_ids]  # Converte para lista
    
    todos_resultados = []
    for vereador_id in vereadores_ids:
        resultados = get_assiduidade_totais(vereador_id)
        todos_resultados.extend(resultados)

    # Ordenar por porcentagem de faltas e pegar o vereador com menos faltas
    menos_faltas = min(todos_resultados, key=lambda x: x['porcentagem_faltas'], default=None)

    return "%s" % menos_faltas['porcentagem_faltas'] if menos_faltas else None




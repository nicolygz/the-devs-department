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


def get_assiduidade_vereador(vereador_id):
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
    
    return resultados

def get_assiduidade_totais():
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
    GROUP BY 
        ver_id;
    """
    
    cursor.execute(query)
    resultados = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return resultados


def calcular_porcentagem_presenca(vereador_id):
    resultados = get_assiduidade_totais()
    
    # Filtra o resultado para o vereador_id específico
    dados = next((dado for dado in resultados if dado['ver_id'] == vereador_id), None)

    if dados is None:
        return None  # Retorna None se não houver dados para o vereador

    faltas_totais = dados['faltas_totais']
    presencas_totais = dados['presencas_totais']  # Corrigido para acessar presenças
    justificadas_totais = dados['justificadas_totais']  # Acesso corrigido

    total_faltas = faltas_totais + justificadas_totais  # Total de faltas
    total = total_faltas + presencas_totais  # Total geral

    if total == 0:  # Evitar divisão por zero
        return 0.0  # Retorna 0% se não houve faltas nem presenças

    porcentagem_falta = (presencas_totais / total) * 100
    porcentagem_falta = round(porcentagem_falta, 2)
    return porcentagem_falta

# Exemplo de uso
print(calcular_porcentagem_presenca(35))

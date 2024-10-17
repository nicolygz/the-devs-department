import requests
import json
import time

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

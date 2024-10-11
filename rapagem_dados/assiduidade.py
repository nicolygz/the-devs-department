import requests
import mysql.connector

def get_api_assiduidade(ID):
    url = "https://camarasempapel.camarasjc.sp.gov.br/api/publico/parlamentar"
    params = {
        "qtd": 1,
        "parlamentarID": ID,
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()

        try:    
            db_connection = mysql.connector.connect(
                host="[SEGREDO]",           
                user="[SEGREDO]",       
                password="[SEGREDO]",   
                database="[SEGREDO]"
            )
            cursor = db_connection.cursor()

            for parlamentar in data.get("parlamentares", []):
                parlamentar_id = parlamentar.get("parlamentarID")
                frequencia = parlamentar.get("frequenciaPlenario", [])
                anos_filtrados = range(2021, 2025)

                for ano in anos_filtrados:
                    presenca = 0
                    faltas = 0
                    justificada = 0

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
                                justificada = quantidade

                    # Verificar se os dados já existem
                    check_query = """
                    SELECT COUNT(*) FROM assiduidade 
                    WHERE ver_id = %s AND ano = %s
                    """
                    cursor.execute(check_query, (parlamentar_id, ano))
                    exists = cursor.fetchone()[0]

                    if exists == 0:  # Se não existir, insere os dados
                        insert_query = """
                        INSERT INTO assiduidade (ver_id, ano, presenca, faltas, justif)
                        VALUES (%s, %s, %s, %s, %s)
                        """
                        cursor.execute(insert_query, (
                            parlamentar_id,
                            ano,
                            presenca,
                            faltas,
                            justificada
                        ))

            db_connection.commit()

        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            if db_connection.is_connected():
                cursor.close()
                db_connection.close()

        return f"Dados processados para o parlamentar ID {ID}."
    else:
        return f"Erro ao fazer a solicitação: {response.status_code}"

print(get_api_assiduidade(35))
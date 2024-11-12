import os
import aiomysql
import dotenv
import mysql.connector
from dotenv import load_dotenv
import json
import glob
from tqdm import tqdm

vereadores = {
    35: "Amélia Naomi",
    38: "Dulce Rita",
    40: "Fernando Petiti",
    43: "Juliana Fraga",
    44: "Juvenil Silvério",
    45: "Lino Bispo",
    47: "Marcão da Academia",
    50: "Robertinho da Padaria",
    55: "Walter Hayashi",
    234: "Roberto do Eleven",
    237: "Zé Luis",
    238: "Dr. José Claudio",
    239: "Thomaz Henrique",
    240: "Roberto Chagas",
    242: "Milton Vieira Filho",
    243: "Rafael Pascucci",
    244: "Marcelo Garcia",
    245: "Renato Santiago",
    246: "Júnior da Farmácia",
    247: "Fabião Zagueiro",
    249: "Rogério da Acasem"
}

# Invertendo o dicionário para obter {nome: id}
vereadores = {nome: ver_id for ver_id, nome in vereadores.items()}

# Carregar variáveis do .env
load_dotenv()

# Função para criar a conexão com o banco de dados assíncrona
# Create a MySQL connection
def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),  # Fetch directly from environment variables
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
        port=os.getenv('MYSQL_PORT', 3306)  # 
    )
    return connection


# Função para criar a conexão com o banco de dados assíncrona
async def get_async_db_connection():
    return await aiomysql.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        db=os.getenv('MYSQL_DATABASE'),
        port=int(os.getenv('MYSQL_PORT', 3306))
    )

def abrirJsons():
    # Caminho para a pasta com os arquivos JSON
    caminho_diretorio = '/Users/pedrovaz/Library/Mobile Documents/com~apple~CloudDocs/iCloud/4. Estudos/Fatec - DSM/1-SEM/API/the-devs-department/rapagem_dados/ArquivosJson/Votacoes/*.json'
    
    # Usar glob para pegar todos os arquivos .json no diretório
    arquivos_json = glob.glob(caminho_diretorio)
    
    c = 0

    # Iterar sobre cada arquivo JSON
    for caminho_arquivo in tqdm(arquivos_json, desc="Processando arquivos JSON"):
        
        # Abrir e carregar o conteúdo do arquivo JSON
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            dados = json.load(arquivo)

            # Verificar se o arquivo contém uma lista de JSONs
            if isinstance(dados, list):
                # Get a database connection
                connection = get_db_connection()
                cursor = connection.cursor()

                for item in tqdm(dados, desc="Processando votacao:"):
                    nome_vereador = item['autoria'].split(',')[0].replace("  ", " ")
                    nome_presidente = item['presidente'].replace("  ", " ")

                    num_pl = item['projeto_de_lei'].split('/')[0]
                    ano_pl = item['projeto_de_lei'].split('/')[-1]
                    autoria_pl = vereadores.get(nome_vereador)
                    presidente = vereadores.get(nome_presidente)
                    resultado = item['status']
                
                    try:
                        # Execute a query to fetch vereadores
                        cursor.execute("""
                                    INSERT INTO votacao (num_pl, ano_pl, resultado, presidente, autoria_pl) 
                                    VALUES (%s, %s, %s, %s, %s) 
                        """, (num_pl, ano_pl, resultado, presidente, autoria_pl ))

                    except mysql.connector.Error as err:
                        print(f"Erro ao inserir dados: {err}")
                        connection.rollback()

                    votacao_id = cursor.lastrowid

                    # eu quero buscar qual o id o banco criou para essa linha da tabela.
                    for vereador in item['vereadores']:
                        vereador_voto = vereador['vereador'].replace("  ", " ")

                        ver_id = vereadores.get(vereador_voto)
                        voto = vereador['voto']

                        try:
                            # inserir na table extrato_votacao como o vereador votou naquele id
                            cursor.execute("""
                                    INSERT INTO extrato_votacao (votacao_id, ver_id, voto) 
                                    VALUES (%s, %s, %s) 
                        """, (votacao_id, ver_id, voto))
                        except mysql.connector.Error as err:
                            print(f"Erro ao inserir dados: {err}")
                            connection.rollback()

                    # Confirma as transações após cada inserção de votação e votos
                    connection.commit()
                
                # Limpar e fechar o cursor e a conexão
                cursor.close()
                connection.close()

        print('sucesso')
    return 'Inserção realizada com sucesso'

print(abrirJsons())
import asyncio
import json
import glob
import aiofiles
from aiohttp import ClientSession
import aiomysql
from tqdm.asyncio import tqdm_asyncio
from dotenv import load_dotenv
import os

# Carregar variáveis do .env
load_dotenv()

async def get_db_connection():
    return await aiomysql.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        db=os.getenv('MYSQL_DATABASE'),
        port=int(os.getenv('MYSQL_PORT', 3306))
    )

async def processar_arquivo(caminho_arquivo, connection, vereadores):
    async with aiofiles.open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        dados = json.loads(await arquivo.read())
        
        if isinstance(dados, list):
            async with connection.cursor() as cursor:
                for item in tqdm_asyncio(dados, desc="Processando votacao:"):
                    nome_vereador = item['autoria'].split(',')[0].replace("  ", " ")
                    nome_presidente = item['presidente'].replace("  ", " ")

                    num_pl = item['projeto_de_lei'].split('/')[0]
                    ano_pl = item['projeto_de_lei'].split('/')[-1]
                    autoria_pl = vereadores.get(nome_vereador)
                    presidente = vereadores.get(nome_presidente)
                    resultado = item['status']

                    try:
                        await cursor.execute("""
                            INSERT INTO votacao (num_pl, ano_pl, resultado, presidente, autoria_pl) 
                            VALUES (%s, %s, %s, %s, %s)
                        """, (num_pl, ano_pl, resultado, presidente, autoria_pl))

                    except Exception as err:
                        print(f"Erro ao inserir dados: {err}")
                        await connection.rollback()

                    votacao_id = cursor.lastrowid

                    batch_insert = []

                    for vereador in item['vereadores']:
                        vereador_voto = vereador['vereador'].replace("  ", " ")

                        ver_id = vereadores.get(vereador_voto)
                        voto = vereador['voto']

                        # Adicionar cada inserção ao batch
                        batch_insert.append((votacao_id, ver_id, voto))

                    try:
                        if batch_insert:
                            # Realizar a inserção em lote
                            await cursor.executemany("""
                                INSERT INTO extrato_votacao (votacao_id, ver_id, voto) 
                                VALUES (%s, %s, %s)
                            """, batch_insert)
                    except Exception as err:
                        print(f"Erro ao inserir dados em lote: {err}")
                        await connection.rollback()

                    # Confirmar as transações após cada inserção de votação e votos
                    await connection.commit()
                
                print('Processamento do arquivo concluído.')

async def abrirJsons():
    caminho_diretorio = '/Users/pedrovaz/Library/Mobile Documents/com~apple~CloudDocs/iCloud/4. Estudos/Fatec - DSM/1-SEM/API/the-devs-department/rapagem_dados/ArquivosJson/Votacoes/*.json'
    arquivos_json = glob.glob(caminho_diretorio)

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

    connection = await get_db_connection()

    for caminho_arquivo in tqdm_asyncio(arquivos_json, desc="Processando arquivos JSON"):
        await processar_arquivo(caminho_arquivo, connection, vereadores)

    await connection.close()

    print('Todos os arquivos foram processados e inseridos com sucesso.')

# Rodar o loop assíncrono
asyncio.run(abrirJsons())

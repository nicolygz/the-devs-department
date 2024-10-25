import sys
import os
from flask import Flask, render_template, request
from flask_paginate import Pagination, get_page_parameter
import mysql.connector
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv  # Adicione esta linha
from math import ceil


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..',)))

# Carregar variáveis do .env
load_dotenv()  # Adicione esta linha para carregar o .env

app = Flask(__name__)

id_vereadores = [35,238,38,247,40,43,246,44,45,47,244,242,243,245,50,240,234,249,239,55,237]

# Create a MySQL connection
def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),  # Fetch directly from environment variables
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
        port=os.getenv('MYSQL_PORT', 3306)  # Provide a default port if not defined
    )
    return connection

@app.route('/test_connection')
def test_connection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DATABASE();')
        result = cursor.fetchone()
        conn.close()
        return f"Connected to database: {result[0]}"
    except Exception as e:
        return str(e)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/visao-geral')
def geral():
    return render_template('visao-geral.html')

@app.route('/lista-vereadores')
def lista_vereadores():
    
   # Get a database connection
    connection = get_db_connection()
    cursor = connection.cursor()

    # Execute a query to fetch vereadores
    cursor.execute('SELECT * FROM vereadores')  # Replace 'vereadores' with your actual table name
    vereadores = cursor.fetchall()

    # Clean up
    cursor.close()
    connection.close()

    # Pass the vereadores data to the template
    return render_template("lista-vereadores.html", verea2dores = vereadores)

@app.route('/vereador')
def pagina_vereador():
    return render_template('vereador.html')

@app.route('/pagina-proposicao/<int:id_prop>')
def pagVer(id_prop):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute('SELECT * FROM proposicoes WHERE id_prop = %s', (id_prop,))
    prop = cursor.fetchone()
    
    cursor.execute('SELECT ver_id FROM proposicoes WHERE id_prop = %s', (id_prop,))
    id = cursor.fetchone()
    id = id[0]
    print(id)
    
    cursor.execute(f'SELECT ver_nome FROM vereadores WHERE ver_id = {id}')
    vereador = cursor.fetchone()

    
    
    cursor.close()
    connection.close()
    
    return render_template('pagina-proposicao.html', prop = prop, vereador = vereador)

@app.route('/proposicoes')
def listProp():
    # Conecte-se ao banco de dados
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Get current page from the query string, default is page 1
    page = request.args.get('page', 1, type=int)
    
    # Define how many items per page
    per_page = 10

    # Get the total number of records
    cursor.execute('SELECT COUNT(*) FROM proposicoes')
    total = cursor.fetchone()[0]
    
    # Calculate total number of pages
    total_pages = ceil(total / per_page)

    print(total_pages)

    # Calculate the offset for the SQL query
    offset = (page - 1) * per_page

    print(offset)
    
    # Fetch the data for the current page
    cursor.execute('SELECT * FROM proposicoes LIMIT %s OFFSET %s', (per_page, offset))
    proposicoes = cursor.fetchall()
    print(proposicoes)
    
    cursor.close()
    connection.close()
    
    # Renderiza o template e passa a paginação junto com os dados
    return render_template('filtro.html', proposicoes=proposicoes, page=page, total_pages=total_pages)


# ATUALIZA O BANCO DE DADOS COM AS INFORMAÇÕES DO VEREADOR
@app.route('/atualiza_vereadores')
def atualiza_vereadores():
    vereadores = []
    for i in id_vereadores:
        vereador = get_vereadores(str(i))
        if vereador:
            vereadores.append(vereador)

    # Get a database connection
    connection = get_db_connection()
    cursor = connection.cursor()
    
    for vereador in vereadores:
        ver_id = vereador['ver_id']
        ver_nome = vereador['ver_nome']
        ver_partido = vereador['ver_partido']
        ver_tel1 = vereador['ver_tel1']
        ver_tel2 = vereador['ver_tel2']
        ver_celular = vereador['ver_celular']
        ver_email = vereador['ver_email']
        ver_posicionamento = ""
        ver_foto = vereador['ver_foto']

        # Checar se o vereador já existe
        cursor.execute("SELECT ver_id FROM vereadores WHERE ver_id = %s", (ver_id,))
        resposta = cursor.fetchone()
        print(resposta)

        # Se o vereador não existir, faz o INSERT
        if not resposta:
            cursor.execute("""
                INSERT INTO vereadores 
                (ver_id, ver_nome, ver_partido, ver_tel1, ver_tel2, ver_celular, ver_email,ver_posicionamento,ver_foto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, 
            (ver_id, ver_nome, ver_partido, ver_tel1, ver_tel2, ver_celular, ver_email,ver_posicionamento,ver_foto))    

   # Confirmar as mudanças no banco de dados
    connection.commit()

    # Fechar conexão
    cursor.close()
    connection.close()

    return "deu certo"

# BUSCA AS INFORMAÇÕES DE UM VEREADOR NO SITE DA CAMARA
def get_vereadores(id):

    # URL da página
    url = 'https://camarasempapel.camarasjc.sp.gov.br/parlamentar.aspx?id=' + id

    print(url)

    response = requests.get(url)
    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        
        # Criando um objeto BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Encontrando a imagem pelo class name
        id = soup.find('form', id="formulario")
        if id:
            # Extraindo o ID da URL
            ver_id = id['action'].split('id=')[-1]
        ver_foto = soup.find('img', class_='w-auto mw-100 m-auto')['src']
        ver_nome = soup.find('div', id="nome_parlamentar").text.strip()
        ver_partido = soup.find('span', id="partido").text.split("(")[-1][0:-1]
        ver_tel1 = ""
        ver_tel2 = ""
        ver_celular = ""
        ver_email = ""

        dados_parlamentar_div = soup.find('div', id="dados_parlamentar")
        if dados_parlamentar_div:

            divs = dados_parlamentar_div.find_all('div')
            if len(divs) > 1:
                i = 0
                while i < len(divs):
                    if 'Telefone' in divs[i].text.strip():
                        telefones = divs[i].text.split(':')[-1].strip().split("/")
                        ver_tel1 = telefones[0].strip()
                        ver_tel2 = telefones[1].strip()
                    if 'Celular' in divs[i].text.strip():
                        ver_celular = divs[i].text.split(":")[-1]
                        if "A Câmara não disponibiliza celular para os vereadores" in ver_celular:
                            ver_celular = "-"

                    if 'E-mail' in divs[i].text.strip():
                        ver_email = divs[i].text.split(":")[-1].strip()
                    
                    i+= 1
        vereador = {
           "ver_id":ver_id,
            "ver_nome":ver_nome,
            "ver_partido":ver_partido,
            "ver_tel1":ver_tel1, 
            "ver_tel2":ver_tel2, 
            "ver_celular":ver_celular, 
            "ver_email":ver_email, 
            "ver_foto":ver_foto
        }

        return vereador

    else:
        print(f'Erro ao acessar a página: {response.status_code}')


# INSERIR PROPOSIÇÕES NO BANCO DE DADOS ATRAVÉS DO ARQUIVO JSON
@app.route('/insere_proposicoes')
def readJson_SendData():
    diretorio =  "../rapagem_dados/ArquivosJson/DadosRequerimento.json"
    connection = get_db_connection()
    cursor = connection.cursor()
    years = ['2021', '2022', '2023', '2024']
    
    # Abrir arquivos json com as informações das proposições
    with open(diretorio, encoding='utf-8', mode='+r') as file:
        pagData = json.load(file)
    cont = 0
    
    # Fazer loop para cada item presente no dicionário json 
    for i in tqdm(pagData, desc="Inserindo proposições no banco"):
        try:
            
            # Transforma a data para o padrão do banco mysql
            date = datetime.strptime(i['Data'], '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            date = '0000-00-00 00:00:00'
            
            # Filtra o ano para o mandato atual (2021-2024)
        if date[:4] in years:
            requerimento_num = i['Numero Proposicao']
            ementa = i['Assunto']
            num_processo = i['Numero Processo']
            num_protocolo = i['Numero Protocolo']
            id_prop = i['ID']
            data_hora = date
            situacao = i['Situacao']
            tipo = i['Tipo']
            ver_id = int(i['Id Autor'])
            autor = str(i['Autor'].strip())
            tema = ''
            
            # Consultar o ver_id usando o nome do vereador
            cursor.execute("SELECT ver_id FROM vereadores WHERE ver_nome = %s", (autor,))
            resultado = cursor.fetchone()

            if resultado is None:
                print(f"Vereador '{autor}' não encontrado. A inserção do requerimento será ignorada.")
                continue  # Ignora se o vereador não for encontrado
            else:
                id_vereador = resultado[0]  # Obtém o ID do vereador

            
            # Pesquisa se a proposição já existe no banco
            cursor.execute("SELECT id_prop FROM proposicoes WHERE id_prop = %s", (id_prop,))
            resp = cursor.fetchone()
            
            # Caso não exista, insere a proposição no banco de dados
            if not resp:
                query = """ 
                            INSERT INTO proposicoes
                            (ver_id,requerimento_num, ementa, num_processo, num_protocolo, id_prop, data_hora, situacao, tipo, tema)
                            VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                try:
                    # Sua consulta de inserção
                    cursor.execute(query, 
                            (id_vereador,requerimento_num, ementa, num_processo, num_protocolo, id_prop, data_hora, situacao, tipo, tema))
                except mysql.connector.MySQLInterfaceError as e:
                    if "Lock wait timeout exceeded" in str(e):
                        print("Erro de bloqueio: Reiniciando transação...")
                        # Reinicie a consulta de inserção
                        cursor.execute(query, 
                            (id_vereador,requerimento_num, ementa, num_processo, num_protocolo, id_prop, data_hora, situacao, tipo, tema))
                    else:
                        print("Erro inesperado:", e)
        if cont%50 == 0:
            connection.commit()
            print('Alterações salvas no banco')
        cont += 1
    # Confirmar as mudanças no banco de dados
    connection.commit()
    
    # Fechar conexão
    cursor.close()
    connection.close()
    
    return "Dados inseridos com sucesso!" 

@app.route('/projetos-lei')
def plsenddata():
    cont = 0
    diretorio = '../rapagem_dados/ArquivosJson/DadosPL.json'
    connection = get_db_connection()
    cursor = connection.cursor()
    years = ['2021', '2022', '2023', '2024']
    with open (diretorio, encoding='utf-8',mode='r+') as file:
        dadojson = json.load(file)
    for i in tqdm(dadojson,desc= 'Inserindo proposições no banco'):
        try:
            date = datetime.strptime(i['Data'], '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            date = '0000-00-00 00:00:00'
        if date[:4] in years:
            requerimento_num = i['Numero Proposicao']
            ementa = i['Assunto']
            num_processo = i['Numero Processo']
            num_protocolo = i['Numero Protocolo']
            id_prop = i['ID']
            data_hora = date
            situacao = i['Situacao']
            tipo = i['Tipo']
            ver_id = int(i['Id Autor'])
            autor = str(i['Autor'].strip())
            tema = ''

            cursor.execute("SELECT ver_id FROM vereadores WHERE ver_nome = %s", (autor,))
            resultado = cursor.fetchone()

            if resultado is None:
                print(f"Vereador '{autor}' não encontrado. A inserção do Projeto de lei será ignorada.")
                continue  # Ignora se o vereador não for encontrado
            else:
                id_vereador = resultado[0]  # Obtém o ID do vereador
            cursor.execute("SELECT id_prop FROM proposicoes WHERE id_prop = %s", (id_prop,))
            resp = cursor.fetchone()
            if not resp:
                query = """ 
                            INSERT INTO proposicoes
                            (ver_id,requerimento_num, ementa, num_processo, num_protocolo, id_prop, data_hora, situacao, tipo, tema)
                            VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                try:
                    # Sua consulta de inserção
                    cursor.execute(query, 
                            (id_vereador,requerimento_num, ementa, num_processo, num_protocolo, id_prop, data_hora, situacao, tipo, tema))
                except mysql.connector.InterfaceError as e:
                    if "Lock wait timeout exceeded" in str(e):
                        print("Erro de bloqueio: Reiniciando transação...")
                        # Reinicie a consulta de inserção
                        cursor.execute(query, 
                            (id_vereador,requerimento_num, ementa, num_processo, num_protocolo, id_prop, data_hora, situacao, tipo, tema))
                    else:
                        print("Erro inesperado:", e)
        if cont %50 == 0:
            connection.commit()
            print('Alterações salvas no banco de dados')
        cont +=1
    connection.commit()
    cursor.close()
    connection.close()

@app.route("/comissoes")
def comissoesbd():
    diretorio="../rapagem_dados/ArquivosJson/comissoes.json"
    connection = get_db_connection()
    cursor = connection.cursor()
    with open (diretorio,encoding="utf-8",mode="+r") as file:
        dadosjson=json.load(file)
    cont = 0
    for x in tqdm(dadosjson, desc="Inserindo proposições no banco"):
        comissaoNome=x["Nome comissao"]
        comissaoId= x["ID comissao"]
        comissaoTema=" "
        comissaoLink=x["Link"]
        try:
            # Transforma a data para o padrão do banco mysql
            date = datetime.strptime(x['Data inicio'], '%d/%m/%Y').strftime('%Y-%m-%d')
            dateEnd = datetime.strptime(x['Data final'], '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            date = '0000-00-00 00:00:00'

        cursor.execute("SELECT id FROM comissoes WHERE id= %s",(comissaoId,))
        resp = cursor.fetchone()
        if not resp:
            query=""" 
            INSERT INTO comissoes 
            (id,nome,tema,data_inicio,data_fim,link)
            VALUES(%s,%s,%s,%s,%s,%s)
                """
            try:
                cursor.execute(query,
                    (comissaoId,comissaoNome,comissaoTema,date,dateEnd,comissaoLink))
                connection.commit()
            except mysql.connector.InterfaceError as e:
                if "lock wait timeout exceeded" in str(e):
                    print("erro de bloqueio, reinicie a transação...")
                    cursor.execute(query,
                    (comissaoId,comissaoNome,comissaoTema,date,dateEnd,comissaoLink))
                else:
                    print("erro inesperado:",e)
                    
            for i in x["Outras infos"]:
                pID = None
                pNOME = i["ParlamentarNome"]
                pCARGO = i["Cargo"]
                cursor.execute("SELECT ver_id FROM vereadores WHERE ver_nome=%s",(pNOME,))
                resultado = cursor.fetchone()
                
                if resultado:
                    verID = resultado[0]
                    cursor.execute("SELECT * FROM vereadores_comissoes WHERE ver_id = %s AND comissao_id = %s AND cargo = %s",
                    (verID, comissaoId, pCARGO))
                    resp = cursor.fetchone()
                    print(resp)
                    
                    if not resp: 
                        query= """
                        INSERT INTO vereadores_comissoes(ver_id,comissao_id,cargo)
                        VALUES (%s,%s,%s)
                        """
                        print(i)
                        
                        try: 
                            cursor.execute(query,(verID,comissaoId,pCARGO),)
                            
                        except mysql.connector.InterfaceError as e:
                            if "lock wait timeout exceeded" in str(e):
                                print("erro de bloqueio, reinicie a transação...")
                                cursor.execute(query,
                                (verID,comissaoId,pCARGO))
                            else:
                                print("erro inesperado:",e)
                    else:
                        return "Dados já existem no Banco de Dados"
                    
        cont += 1   
        connection.commit() 
           
    cursor.close()
    connection.close()
    
    return "Dados inseridos com sucesso!"


if __name__ == "__main__":
    app.run(debug=True)
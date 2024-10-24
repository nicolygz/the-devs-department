import sys
import os
from flask import Flask, render_template
import mysql.connector
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from rapagem_dados import *


app = Flask(__name__)

id_vereadores = [35,238,38,247,40,43,246,44,45,47,244,242,243,245,50,240,234,249,239,55,237]

# Create a MySQL connection
def get_db_connection():
    connection = mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DATABASE'],
        port=app.config.get('MYSQL_PORT')  # Fetch the port from config
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
    return render_template("lista-vereadores.html", vereadores = vereadores)

@app.route('/vereador')
def pagina_vereador():
    return render_template('vereador.html')

@app.route('/pagina-proposicao')
def pagVer():
    return render_template('pagina-proposicao.html')

@app.route('/proposicoes')
def listProp():
    return render_template('filtro.html')


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

@app.route("/comissoes")
def comissoesbd():
    diretorio="../rapagem_dados/ArquivosJson/comissoes.json"
    connection = get_db_connection()
    cursor = connection.cursor()
    with open (diretorio,encoding="utf-8",mode="+r") as file:
        dadosjson=json.load(file)
    print(dadosjson)
    for x in dadosjson:
        comissaoNome=x["Nome comissao"]
        comissaoId=x["ID comissao"]
        comissaoInicio=x["Data inicio"]
        comissaoInicio=datetime.strptime(comissaoInicio,"%d/%m/%Y").strftime("%Y-%m-%d")
        comissaoFinal=x["Data final"]
        comissaoFinal=datetime.strptime(comissaoFinal,"%d/%m/%Y").strftime("%Y-%m-%d")
        comissaoTema=" "
        comissaoLink=x["Link"]

        cursor.execute("SELECT id FROM comissoes WHERE id=%s,"(comissaoId,))
        resp=cursor.fetchone()
        if not resp:
            query=""" INSERT INTO comissoes 
              (id,nome,tema,data_inicio,data_fim,link)
              VALUES(%s,%s,%s,%s,%s,%s)
                  """
            try:
                cursor.execute(query,
                    (comissaoId,comissaoNome,comissaoTema,comissaoInicio,comissaoFinal,comissaoLink))
            except mysql.connector.MySQLInterfacError as e:
                if "lock wait timeout exceeded" in str(e):
                    print("erro de bloqueio, reinicie a transação...")
                    cursor.execute(query,
                    (comissaoId,comissaoNome,comissaoTema,comissaoInicio,comissaoFinal,comissaoLink))
                else:
                    print("erro inesperado:",e)
            for i in x["Outras infos"]:
                pID=i["parlamentarID"]
                pNOME=i["parlamentarNome"]
                pCARGO=i["cargo"]
                cursor.execute("SELECT ver_id FROM veradores WHERE ver_nome=%s",(pNOME,))
                resultado = cursor.fetchone()
                if resultado is None:
                    print(f"Vereador {pNOME} não encontrado.A inserção do requerimento será ignorada")
                    continue
                else:
                    verID=resultado [0]
            query= """   INSERT INTO vereadores_comissoes(id,ver_id,comissao_id,cargo)
        VALUES (%s,%s,%s,%s)
            """
            try: 
                cursor.execute(query,(pID,verID,comissaoId,pCARGO))
            except mysql.connector.MySQLInterfacError as e:
                if "lock wait timeout exceeded" in str(e):
                    print("erro de bloqueio, reinicie a transação...")
                    cursor.execute(query,
                    (pID,verID,comissaoId,pCARGO))
                else:
                    print("erro inesperado:",e)
            connection.commit()
        connection.commit()
        
            
    cursor.close()
    connection.close()

if __name__ == "__main__":
    app.run(debug=True)
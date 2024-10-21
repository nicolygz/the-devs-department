import sys
import os
from flask import Flask, render_template
import mysql.connector
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv  # Adicione esta linha
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
    return render_template("lista-vereadores.html", vereadores = vereadores)

@app.route('/vereador')
def pagina_vereador():
    return render_template('vereador.html')

@app.route('/pagina-proposicao')
def pagVer():
    return render_template('pagina-proposicao.html')

@app.route('/proposicoes')
def listProp():
    try:
        connection = get_db_connection()  # Conecte-se ao banco de dados
        cursor = connection.cursor(dictionary=True)

        # Execute a consulta para buscar todas as proposições
        cursor.execute('SELECT * FROM proposicoes')
        todas_proposicoes = cursor.fetchall()

        # Filtre apenas as moções
        mocoes = [prop for prop in todas_proposicoes if prop['tipo'] == 'Moção']

        cursor.close()
        connection.close()

        # Imprimir os dados para verificação
        print("Todas as proposições:", todas_proposicoes)  # Para verificação no console
        print("Moções filtradas:", mocoes)  # Para verificação no console
        
        return render_template('filtro.html', proposicoes=mocoes)  # Passa as moções para o template

    except Exception as e:
        print("Erro ao conectar ao banco de dados ou executar a consulta:", e)
        return "Erro ao acessar os dados"



@app.route('/proposicao/<int:id_prop>')
def pagina_proposicao(id_prop):
    # Aqui você poderia buscar e exibir detalhes da proposição específica
    return f"Página da proposição com ID: {id_prop}"


@app.route('/insere_mocoes')
def insere_mocoes():
    caminho_mocoes = 'rapagem_dados/ArquivosJson/dadosMocoes_2021_a_2024.json'

    try:
        with open(caminho_mocoes, 'r', encoding='utf-8') as file:
            mocoes = json.load(file)

    except FileNotFoundError:
        return {'status': 'error', 'message': 'Arquivo não encontrado. Verifique o caminho.'}

    connection = get_db_connection()
    cursor = connection.cursor()
    inserted_count = 0

    # Itera sobre as moções e insere no banco de dados
    for mocao in mocoes:
        assunto = mocao.get('Assunto', 'Sem assunto')
        
        # Converter a data para o formato correto
        data_str = mocao.get('Data', '0000-00-00 00:00:00')
        try:
            data_hora = datetime.strptime(data_str, '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            print(f"Data inválida: {data_str}. Usando data padrão.")
            data_hora = '0000-00-00 00:00:00'
            
        situacao = mocao.get('Situacao', 'Indefinido')
        tipo = mocao.get('Tipo', 'Moção')
        autor_nome = mocao.get('Autor')  # Usando o nome do autor
        tema = mocao.get('Tema', 'Sem tema')
        requerimento_num = mocao.get('Numero Proposicao', 'N/A')
        num_processo = mocao.get('Numero Processo', 'N/A')
        num_protocolo = mocao.get('Numero Protocolo', 0)
        id_prop = mocao.get('Numero Proposicao', 0)

        # Consultar o ver_id usando o nome do vereador
        cursor.execute("SELECT ver_id FROM vereadores WHERE ver_nome = %s", (autor_nome,))
        resultado = cursor.fetchone()

        if resultado is None:
            print(f"Vereador '{autor_nome}' não encontrado. A inserção da moção será ignorada.")
            continue  # Ignora se o vereador não for encontrado
        else:
            id_vereador = resultado[0]  # Obtém o ID do vereador

        # Comando SQL para inserir os dados na tabela proposicoes
        sql = """INSERT INTO proposicoes 
                (requerimento_num, ementa, num_processo, num_protocolo, id_prop, data_hora, situacao, tipo, ver_id, tema)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        valores = (requerimento_num, assunto, num_processo, num_protocolo, id_prop, data_hora, situacao, tipo, id_vereador, tema)
        
        try:
            cursor.execute(sql, valores)
            print(f"Moção inserida com sucesso: {id_prop}")
            inserted_count += 1
        except Exception as e:
            print(f"Erro ao inserir moção: {e}. ver_id: {id_vereador}")

    connection.commit()
    cursor.close()
    connection.close()

    return {'status': 'success', 'inserted_count': inserted_count}



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

if __name__ == "__main__":
    app.run(debug=True)
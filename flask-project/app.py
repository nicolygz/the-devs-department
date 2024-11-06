import sys
import os
from flask import Flask, jsonify, render_template, request, redirect
from flask_paginate import Pagination, get_page_parameter
import mysql.connector
import requests
from tqdm import tqdm # type: ignore
from datetime import datetime
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv 
from math import ceil
import aiomysql
import locale
import asyncio

# diretório para os arquivos JSON de PROPOSIÇÕES
DIRETORIO_JSON = "../rapagem_dados/ArquivosJson/"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..',)))
from rapagem_dados import assiduidade

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

try:
    conn = get_db_connection()
    print("Conexão bem-sucedida!")
except mysql.connector.Error as err:
    print(f"Erro de conexão: {err}")
finally:
    if conn:
        conn.close()

# Função para criar a conexão com o banco de dados assíncrona
async def get_async_db_connection():
    return await aiomysql.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        db=os.getenv('MYSQL_DATABASE'),
        port=int(os.getenv('MYSQL_PORT', 3306))
    )

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

@app.route('/vereadores')
def vereadores():
    
   # Get a database connection
    connection = get_db_connection()
    cursor = connection.cursor()

    # Execute a query to fetch vereadores
    cursor.execute('SELECT * FROM vereadores')
    vereadores = cursor.fetchall()

    # Clean up
    cursor.close()
    connection.close()

    # Pass the vereadores data to the template
    return render_template("lista-vereadores.html", vereadores = vereadores)
    
@app.route('/vereadores/<int:vereador_id>')
async def pagina_vereador(vereador_id):
    
    # Configura o locale para português do Brasil
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

    # Cria conexões e cursores independentes
    connection1 = await get_async_db_connection()
    connection2 = await get_async_db_connection()

    async with connection1.cursor() as cursor1, \
               connection2.cursor() as cursor2:
        
        assiduidades = assiduidade.get_assiduidade_vereador(vereador_id)

        # Garante que cada função retorna uma tarefa única
        vereador_task = getVereadorById(cursor1, vereador_id)
        comissoes_task = getComissoesByVereadorId(cursor2, vereador_id)

        # Aguarda as tarefas
        vereador, comissoesBd = await asyncio.gather(vereador_task, comissoes_task)

        # Criar o objeto vereador e formatar o patrimônio
        vereadorObj = vereadorListaToObj(vereador)
        vereadorObj['ver_patrimonio'] = locale.currency(
            float(vereadorObj['ver_patrimonio']), symbol=True, grouping=True
        ).replace(" R$", "")
        
        # Conectar no banco
        connection = get_db_connection()
        cursor = connection.cursor()

        # Transformar cada comissão em objeto
        comissoes = []
        for comissaoDetalhe in comissoesBd:

            # Realizar busca da proposição
            cursor.execute('SELECT * FROM comissoes WHERE id = %s', (comissaoDetalhe[2],))
            comissao = cursor.fetchone()
            
            comissaoObj = comissaoListaToObj(comissao)

            comissaoDetalheObj = comissaoDetalheToObj(comissaoDetalhe)

            obj = {
                "nome_comissao":comissaoObj['nome'],
                "data_inicio":comissaoObj['data_inicio'],
                "data_fim":comissaoObj['data_fim'],
                "link":comissaoObj['link'],
                "cargo":comissaoDetalheObj['cargo'],
                "comissao_id":comissaoDetalheObj['id'],
            }
            comissoes.append(obj)
        
        query = """
            SELECT 
            COUNT(CASE WHEN tipo = %s THEN 1 END) AS qtd_requerimento,
            COUNT(CASE WHEN tipo = %s THEN 1 END) AS qtd_mocao,
            COUNT(CASE WHEN tipo = %s THEN 1 END) AS qtd_pl
        FROM 
            proposicoes
        WHERE 
            ver_id = %s;
        """
        cursor.execute(query, ('Requerimento','Moção', 'Projeto de Lei', vereador_id))

        response = cursor.fetchone()
        if response:
            print(response[0])
        proposicoes = {"qtd_requerimento":response[0],"qtd_mocao":response[1], "qtd_pl":response[2]}

        # Obter totais de assiduidade e calcular porcentagem de presença
        assiduidade_totais = assiduidade.get_assiduidade_totais()
        porcentagem_presenca = assiduidade.calcular_porcentagem_presenca(vereador_id)

    # Fecha a conexão
    connection1.close()
    connection2.close()

    # Renderiza o template com os dados
    return render_template('vereador.html',
        assiduidades=assiduidades,
        vereador=vereadorObj,
        assiduidade_totais=assiduidade_totais,
        porcentagem_presenca=porcentagem_presenca,
        comissoes=comissoes,
        proposicoes= proposicoes
    )

# Função para buscar os dados do vereador com cursor assíncrono
async def getVereadorById(cursor, vereador_id):
    await cursor.execute('SELECT * FROM vereadores WHERE ver_id = %s', (vereador_id,))
    vereador = await cursor.fetchone()
    return vereador

# Função para buscar as comissões do vereador com cursor assíncrono
async def getComissoesByVereadorId(cursor, vereador_id):
    await cursor.execute('SELECT * FROM vereadores_comissoes WHERE ver_id = %s', (vereador_id,))
    comissoes = await cursor.fetchall()
    return comissoes

# Função para buscar uma comissão específica com cursor assíncrono
async def getComissaoById(cursor, comissao_id):
    print(f"Buscando comissão com ID: {comissao_id}")  # Verifica o ID
    await cursor.execute('SELECT * FROM comissoes WHERE id = %s', (comissao_id,))
    comissao = await cursor.fetchone()
    return comissao

def comissaoListaToObj(comissao):
    comissaoObj = {
        "id":comissao[0],
        "nome":comissao[1],
        "tema":comissao[2],
        "data_inicio":comissao[3],
        "data_fim":comissao[4],
        "link":comissao[5],
    }
    return comissaoObj

def comissaoDetalheToObj(comissao):
    comissaoObj = {
        "id":comissao[0],
        "ver_id":comissao[1],
        "comissao_id":comissao[2],
        "cargo":comissao[3]
    }
    return comissaoObj

def vereadorListaToObj(vereador):
    vereadorObj = {
        "ver_id":vereador[0],
        "ver_nome":vereador[1],
        "ver_partido":vereador[2],
        "ver_tel1":vereador[3],
        "ver_tel2":vereador[4],
        "ver_celular":vereador[5],
        "ver_email":vereador[6],
        "ver_gabinete":vereador[7],
        "ver_posicionamento":vereador[8],
        "ver_foto":vereador[9],
        "ver_biografia":vereador[10],
        "ver_patrimonio":vereador[11],
    }
    return vereadorObj

@app.route('/proposicoes/<int:id_prop>')
def pagina_proposicao(id_prop):
    # Conectar no banco
    connection = get_db_connection()
    cursor = connection.cursor()

    # Realizar busca da proposição
    cursor.execute('SELECT * FROM proposicoes WHERE id_prop = %s', (id_prop,))
    proposicao = cursor.fetchone()

    if proposicao is None:
        # Se não encontrar a proposição, pode redirecionar ou mostrar uma mensagem
        return "Proposição não encontrada", 404

    # Transforma em objeto
    proposicaoObj = {
        "requerimento_num": proposicao[0],
        "assunto": proposicao[1],
        "processo": proposicao[2],
        "protocolo": proposicao[3],
        "id_prop": proposicao[4],
        "data": proposicao[5],
        "situacao": proposicao[6],
        "tipo": proposicao[7],
        "autorId": proposicao[8],
        "tema": proposicao[9],
        "ano": proposicao[5].year,
        "numero": proposicao[11],
    }

    print(proposicaoObj)

    # Buscar nome do vereador
    cursor.execute('SELECT ver_nome FROM vereadores WHERE ver_id = %s', (proposicaoObj['autorId'],))
    nome_vereador = cursor.fetchone()  # Isso retorna uma tupla, extraia o nome depois

    # Verifica se o vereador foi encontrado
    if nome_vereador is not None:
        nome_vereador = nome_vereador[0]  # Pega o nome da tupla
    else:
        nome_vereador = "Vereador não encontrado"

    cursor.close()
    connection.close()
    
    return render_template('pagina-proposicao.html', proposicao=proposicaoObj, nome_vereador=nome_vereador)

@app.route('/proposicoes')
def proposicoes():
    # Verifica se os parâmetros estão vazios na URL
    # Se encontrar exatamente "busca=&data_inicio=&data_fim=" na URL, redireciona
    if 'busca=&data_inicio=&data_fim=' in request.full_path:
        return redirect('/proposicoes')
    
    # Conecte-se ao banco de dados
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Obter parâmetros da query
    page = request.args.get('page', 1, type=int)
    search = request.args.get('busca', '')
    tipos = request.args.getlist('tipos') # Lista de tipos selecionados
    date_start = request.args.get('data_inicio')
    date_end = request.args.get('data_fim')
    
    # Definir itens por página
    per_page = 10
    
    # Construir a query base
    query = 'SELECT * FROM proposicoes WHERE situacao = %s'
    params = ['Aprovada']
    count_query = 'SELECT COUNT(*) FROM proposicoes WHERE situacao = %s'
    
    # Adicionar filtros se existirem
    if search:
        query += ' AND (ementa LIKE %s OR tema LIKE %s)'
        count_query += ' AND (ementa LIKE %s OR tema LIKE %s)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param])
    
    if tipos:
        query += ' AND tipo IN ({})'.format(','.join(['%s'] * len(tipos)))
        count_query += ' AND tipo IN ({})'.format(','.join(['%s'] * len(tipos)))
        params.extend(tipos)
    
    if date_start:
        query += ' AND DATE(data_hora) >= %s'
        count_query += ' AND DATE(data_hora) >= %s'
        params.append(date_start)
    
    if date_end:
        query += ' AND DATE(data_hora) <= %s'
        count_query += ' AND DATE(data_hora) <= %s'
        params.append(date_end)
    
    # Contar total de registros para paginação
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]
    total_pages = ceil(total / per_page)
    
    # Adicionar paginação à query
    query += ' LIMIT %s OFFSET %s'
    params.extend([per_page, (page - 1) * per_page])
    
    # Executar query final
    cursor.execute(query, params)
    proposicoes = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('proposicoes.html', 
                         proposicoes=proposicoes, 
                         page=page, 
                         total_pages=total_pages,
                         tipos=tipos)

# ATUALIZA O BANCO DE DADOS COM AS INFORMAÇÕES DO VEREADOR
@app.route('/atualiza_vereadores')
def atualiza_vereadores():
    # Chamar a API e pegar os dados de assiduidade
    dados_atuais = assiduidade.get_api_assiduidade(id_vereadores)
    
    # Guardar o JSON da API para inspeção
    with open('rapagem_dados/assiduidades/assiduidade_total.json', 'w') as json_file:
        json.dump(dados_atuais, json_file, indent=4)
    
    # Obter conexão com o banco de dados
    connection = get_db_connection()
    cursor = connection.cursor()
    
    inserted_count = 0  # Contador de inserções
    updated_count = 0   # Contador de atualizações
    try:
        for vereador in dados_atuais:
            ver_id = vereador['ver_id']
            ano = vereador['ano']
            presenca = vereador['presenca']
            faltas = vereador['faltas']
            justif = vereador['justif']

            # Checar se o vereador e o ano já existem no banco de dados
            cursor.execute("SELECT presenca, faltas, justif FROM assiduidade WHERE ver_id = %s AND ano = %s", (ver_id, ano))
            resposta = cursor.fetchone()

            if not resposta:
                # Se o vereador e o ano não existirem, faz o INSERT
                cursor.execute(""" 
                    INSERT INTO assiduidade 
                    (ver_id, ano, presenca, faltas, justif)
                    VALUES (%s, %s, %s, %s, %s)
                """, 
                (ver_id, ano, presenca, faltas, justif)) 
                inserted_count += 1  # Incrementar o contador de inserção
            else:
                # Se já existe, verificar se houve mudanças nos dados
                presenca_db, faltas_db, justif_db = resposta
                if (presenca_db != presenca) or (faltas_db != faltas) or (justif_db != justif):
                    # Se os dados são diferentes, faz o UPDATE
                    cursor.execute("""
                        UPDATE assiduidade
                        SET presenca = %s, faltas = %s, justif = %s
                        WHERE ver_id = %s AND ano = %s
                    """, (presenca, faltas, justif, ver_id, ano))
                    updated_count += 1  # Incrementar o contador de atualização

        # Confirmar as mudanças no banco de dados
        connection.commit()

    except Exception as e:
        print(f"Erro: {e}")
        connection.rollback()  # Reverter em caso de erro
        return {'status': 'error', 'message': str(e)}

    finally:
        # Fechar conexão
        cursor.close()
        connection.close()

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

    return redirect(request.referrer)

@app.route('/ranking')  
def ranking():
    return render_template('filtroranking.html')

@app.route('/filtrar/<criterio>')
def filtrar_ranking(criterio):
    if criterio == 'proposicoes':
        query = """
            SELECT v.ver_id, v.ver_nome, COUNT(p.ver_id) AS qtd_proposicoes,
                   COUNT(CASE WHEN p.tipo = 'Requerimento' THEN 1 END) as requerimentos,
                   COUNT(CASE WHEN p.tipo = 'Moção' THEN 1 END) as mocoes,
                   COUNT(CASE WHEN p.tipo = 'Projeto de Lei' THEN 1 END) as projetos_lei
            FROM vereadores v
            LEFT JOIN proposicoes p ON v.ver_id = p.ver_id
            GROUP BY v.ver_id, v.ver_nome
            ORDER BY qtd_proposicoes DESC;
        """
    elif criterio == 'assiduidade':
        query = """
            SELECT v.ver_id, v.ver_nome, 
                   SUM(a.presenca) as total_presencas,
                   SUM(a.faltas) as total_faltas,
                   SUM(a.justif) as total_justificadas,
                   ROUND((SUM(a.presenca) * 100.0) / (SUM(a.presenca) + SUM(a.faltas) + SUM(a.justif)), 2) as percentual_presenca
            FROM vereadores v
            LEFT JOIN assiduidade a ON v.ver_id = a.ver_id
            GROUP BY v.ver_id, v.ver_nome
            ORDER BY percentual_presenca DESC;
        """
    elif criterio == 'comissoes':
        query = """
            SELECT v.ver_id, v.ver_nome, COUNT(vc.ver_id) AS total_comissoes,
                   GROUP_CONCAT(DISTINCT c.nome SEPARATOR ', ') as comissoes
            FROM vereadores v
            LEFT JOIN vereadores_comissoes vc ON v.ver_id = vc.ver_id
            LEFT JOIN comissoes c ON vc.comissao_id = c.id
            GROUP BY v.ver_id, v.ver_nome
            ORDER BY total_comissoes DESC;
        """
    elif criterio == 'avaliacoes':
        query = """
            SELECT v.ver_id, v.ver_nome, 
                   COUNT(a.id) as total_avaliacoes,
                   ROUND(AVG(a.nota), 2) as media_avaliacoes
            FROM vereadores v
            LEFT JOIN avaliacao a ON v.ver_id = a.ver_id
            GROUP BY v.ver_id, v.ver_nome
            ORDER BY media_avaliacoes DESC;
        """
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(query)
    resultado = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(resultado)

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

@app.route("/atualiza_comissoes")
def atualiza_comissoes():
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
                cursor.execute("SELECT ver_id FROM vereadores WHERE ver_nome = %s",(pNOME,))
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

# Função para definir o arquivo JSON com base no tipo de proposição
def obter_diretorio_json(tipo_proposicao):
    diretorios = {
        'requerimento': "../rapagem_dados/ArquivosJson/Dados_Requerimento.json",
        'mocao': "../rapagem_dados/ArquivosJson/Dados_Mocao.json",
        'projeto_lei': "../rapagem_dados/ArquivosJson/Dados_ProjetoLei.json"
    }
    return diretorios.get(tipo_proposicao)

vereador_cache = {}

# Função de busca com cache
async def buscar_vereador(nome_vereador, cursor):
    if nome_vereador in vereador_cache:
        return vereador_cache[nome_vereador]
    await cursor.execute("SELECT ver_id FROM vereadores WHERE ver_nome = %s", (nome_vereador,))
    result = await cursor.fetchone()
    vereador_cache[nome_vereador] = result[0] if result else None
    return vereador_cache[nome_vereador]

# Função para inserir ou atualizar proposições em lote
async def inserir_proposicoes_em_lote(cursor, proposicoes):
    # Listas para valores de inserção e atualização
    insert_args = []
    update_args = []
    
    for proposicao in tqdm(proposicoes, desc=f"Inserindo {len(proposicoes)} proposições."):
        data_hora = datetime.strptime(proposicao['data'], '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        autor = proposicao['nomeRazao'].strip()

        # Obter ID do vereador com cache
        id_vereador = await buscar_vereador(autor, cursor)
        
        if not id_vereador:
            print(f"Vereador '{autor}' não encontrado. A inserção do requerimento será ignorada.")
            continue

        # Verificar se a proposição já existe
        await cursor.execute("SELECT id_prop FROM proposicoes WHERE id_prop = %s", (proposicao['id_prop'],))
        exists = await cursor.fetchone()

        if exists:
            # Preparar argumentos de atualização
            update_args.append((
                id_vereador,
                proposicao['requerimento_num'],
                proposicao['assunto'],
                proposicao['processo'],
                proposicao['protocolo'],
                proposicao['ano'],
                proposicao['numero'],
                data_hora,
                proposicao['situacao'],
                proposicao['tipo'],
                '',
                proposicao['id_prop']
            ))
        else:
            # Preparar argumentos de inserção
            insert_args.append((
                id_vereador,
                proposicao['requerimento_num'],
                proposicao['assunto'],
                proposicao['processo'],
                proposicao['protocolo'],
                proposicao['id_prop'],
                data_hora,
                proposicao['situacao'],
                proposicao['tipo'],
                '',
                proposicao['ano'],
                proposicao['numero']
            ))

    # Inserir em lote
    if insert_args:
        insert_query = """
            INSERT INTO proposicoes
            (ver_id, requerimento_num, ementa, num_processo, num_protocolo, id_prop, data_hora, situacao, tipo, tema, ano, numero)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        await cursor.executemany(insert_query, insert_args)

    # Atualizar em lote
    if update_args:
        update_query = """
            UPDATE proposicoes
            SET 
                ver_id = %s,
                requerimento_num = %s,
                ementa = %s,
                num_processo = %s,
                num_protocolo = %s,
                ano = %s,
                numero = %s,
                data_hora = %s,
                situacao = %s,
                tipo = %s,
                tema = %s
            WHERE id_prop = %s
        """
        await cursor.executemany(update_query, update_args)

# Função principal para processar proposições
async def processar_proposicoes(tipo_proposicao):
    diretorio = obter_diretorio_json(tipo_proposicao)
    if not diretorio:
        print(f"Tipo de proposição '{tipo_proposicao}' inválido.")
        return

    with open(diretorio, encoding='utf-8') as file:
        proposicoes = json.load(file)

    connection = await get_async_db_connection()
    async with connection.cursor() as cursor:
        count = 0
        total_inserts = 0  # Contador de inserções
        batch_size = 150
        total = len(proposicoes)
        
        # Processa em lotes
        for i in tqdm(range(0, total, batch_size), desc=f"Inserindo {tipo_proposicao}s"):
            batch = proposicoes[i:i + batch_size]
            await inserir_proposicoes_em_lote(cursor, batch)
            await connection.commit()
            print(f"Lote {i // batch_size + 1} confirmado no banco de dados.")

        await connection.commit()  # Commit final para garantir que todos os dados sejam persistidos
    connection.close()
    print(f"{tipo_proposicao.capitalize()}s inseridos com sucesso!")

@app.route('/atualiza_requerimentos', methods=['GET'])
async def atualiza_requerimentos_async():
    await processar_proposicoes('requerimento')
    return jsonify({"message": "Processo de inserção de requerimentos iniciado com sucesso!"}), 200

@app.route('/atualiza_mocoes', methods=['GET'])
async def atualiza_mocoes():
    await processar_proposicoes('mocao')
    return jsonify({"message": "Processo de inserção de moções iniciado com sucesso!"}), 200

@app.route('/atualiza_projetos_lei', methods=['GET'])
async def atualiza_projetos_lei():
    await processar_proposicoes('projeto_lei')
    return jsonify({"message": "Processo de inserção de projetos de lei iniciado com sucesso!"}), 200

@app.route('/atualiza_tema_projetos_lei', methods=['GET'])
async def atualiza_temas_proposicoes():
    # Buscar a lista de pls com temas
    diretorio = '../rapagem_dados/output/pl_com_temas.json'

    # Conectar ao banco de dados
    conn = await get_async_db_connection()

    with open(diretorio, encoding='utf-8') as file:
        proposicoes = json.load(file)

    # Iterar pelas proposições e atualizar o tema
    for proposicao in tqdm(proposicoes, unit='it'):
        await atualizar_proposicao(conn, proposicao)

    # Fechar a conexão
    conn.close()

    return jsonify({"message": "Atualização concluída"})

async def atualizar_proposicao(conn, proposicao):
    
    # Criar um cursor
    async with conn.cursor() as cursor:
        num_processo = proposicao['num_processo']
        tema = proposicao['tema']
        numero = proposicao['num_pl']
        ano = proposicao['ano_pl']
        situacao = 'Aprovada'

        # Buscar no banco por proposição usando parâmetros
        query = """
            SELECT COUNT(*) 
            FROM proposicoes 
            WHERE num_processo = %s AND numero = %s AND ano = %s;
        """

        # Executar a consulta
        await cursor.execute(query, (num_processo, numero, ano))

        # Obter o resultado da contagem
        count = await cursor.fetchone()

        if count[0] > 0:
            # Atualizar o tema no banco de dados
            update_query = """
                UPDATE proposicoes 
                SET tema = %s, situacao = %s
                WHERE num_processo = %s AND numero = %s AND ano = %s;
            """
            await cursor.execute(update_query, (tema, situacao ,num_processo, numero, ano))
            await conn.commit()  # Commit as mudanças

if __name__ == "__main__":
    app.run(debug=True)
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
import plotly.graph_objects as go
import time
from better_profanity import profanity


# diretório para os arquivos JSON de PROPOSIÇÕES
DIRETORIO_JSON = "../rapagem_dados/ArquivosJson/"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..',)))
from rapagem_dados import assiduidade

# Carregar variáveis do .env
load_dotenv()  # Adicione esta linha para carregar o .env

app = Flask(__name__)

arquivo = 'static/badWords.txt'
profanity.load_censor_words_from_file(arquivo)

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

@app.route('/ranking')
def geral():
    # Conectar ao banco de dados
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)  # Retorna os resultados como dicionários

    # Query para pegar todos os vereadores
    query_vereadores = """
    SELECT ver_id, ver_nome, ver_partido, ver_tel1, ver_tel2, ver_celular, ver_email, ver_foto
    FROM vereadores
    ORDER BY ver_nome ASC;
    """
    cursor.execute(query_vereadores)
    vereadores = cursor.fetchall()  # Pega todos os vereadores

    # Query para calcular a média da posição política
    query_media_posicao = """
    SELECT AVG(posicao_politica) AS media_posicao
    FROM vereadores;
    """
    cursor.execute(query_media_posicao)
    resultado_media = cursor.fetchone()  # Pega o resultado da média

    # Verificar se a média foi calculada corretamente
    media_posicao = None
    if resultado_media and resultado_media['media_posicao'] is not None:
        media_posicao = resultado_media['media_posicao']

    # Fechar a conexão com o banco após executar as queries
    cursor.close()
    connection.close()

    # Renderiza o template 'ranking.html' com os dados
    return render_template('ranking.html', vereadores=vereadores, media_posicao=media_posicao)


@app.route('/filtrar/<criterio>')
def filtrar_ranking(criterio):
    # Definir a query com base no critério selecionado
    if criterio == 'proposicoes':
        query = """
            SELECT v.ver_id, v.ver_nome, v.ver_partido, v.ver_foto, COUNT(p.ver_id) AS qtd_proposicoes
            FROM vereadores v
            LEFT JOIN proposicoes p ON v.ver_id = p.ver_id
            GROUP BY v.ver_id
            ORDER BY qtd_proposicoes DESC;
        """
    elif criterio == 'assiduidade':
        query = """
            SELECT v.ver_id, v.ver_nome, v.ver_partido, v.ver_foto,
                   ROUND((SUM(a.presenca) * 100.0) / (SUM(a.presenca) + SUM(a.faltas) + SUM(a.justif)), 2) as percentual_presenca
            FROM vereadores v
            LEFT JOIN assiduidade a ON v.ver_id = a.ver_id
            GROUP BY v.ver_id
            ORDER BY percentual_presenca DESC;
        """
    elif criterio == 'comissoes':
        query = """
            SELECT v.ver_id, v.ver_nome, v.ver_partido, v.ver_foto, COUNT(vc.ver_id) AS total_comissoes
            FROM vereadores v
            LEFT JOIN vereadores_comissoes vc ON v.ver_id = vc.ver_id
            GROUP BY v.ver_id
            ORDER BY total_comissoes DESC;
        """
    elif criterio == 'avaliacoes':
        query = """
            SELECT v.ver_id, v.ver_nome, v.ver_partido, v.ver_foto, ROUND(AVG(a.nota), 2) as media_avaliacoes
            FROM vereadores v
            LEFT JOIN avaliacao a ON v.ver_id = a.ver_id
            GROUP BY v.ver_id
            ORDER BY media_avaliacoes DESC;
        """
    elif criterio == 'todos':  # Exibir todos os vereadores com todos os critérios relevantes
        query = """
             SELECT v.ver_id, v.ver_nome, v.ver_partido, v.ver_foto, v.ver_patrimonio,
               COALESCE(ROUND(AVG(a.nota), 2), 'N/A') as media_avaliacoes,  -- Média de avaliações
               COALESCE(COUNT(p.ver_id), 0) AS qtd_proposicoes,  -- Quantidade de proposições
               COALESCE(ROUND((SUM(a2.presenca) * 100.0) / (SUM(a2.presenca) + SUM(a2.faltas) + SUM(a2.justif)), 2), 0) as percentual_presenca,  -- Percentual de presença
               COALESCE(COUNT(vc.ver_id), 0) AS total_comissoes  -- Total de comissões
        FROM vereadores v
        LEFT JOIN proposicoes p ON v.ver_id = p.ver_id
        LEFT JOIN avaliacao a ON v.ver_id = a.ver_id
        LEFT JOIN assiduidade a2 ON v.ver_id = a2.ver_id
        LEFT JOIN vereadores_comissoes vc ON v.ver_id = vc.ver_id
        GROUP BY v.ver_id, v.ver_nome, v.ver_partido, v.ver_foto, v.ver_patrimonio  -- Incluindo dados pessoais no GROUP BY
        ORDER BY media_avaliacoes DESC, qtd_proposicoes DESC, percentual_presenca DESC, total_comissoes DESC;
    """



    elif criterio == 'patrimonio':  # Vai exibir o patrimônio dos vereadores em ordem decrescente
     query = """
        SELECT v.ver_id, v.ver_nome, v.ver_partido, v.ver_foto, v.ver_patrimonio
        FROM vereadores v
        ORDER BY v.ver_patrimonio DESC;
    """

    else:
        return jsonify({"error": "Critério inválido"}), 400

    # Conectar ao banco de dados e executar a query
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    resultado = cursor.fetchall()

    # Substituir valores `None` por valores padrão
    for item in resultado:
        item['media_avaliacoes'] = item.get('media_avaliacoes', 'N/A')  # Estático como 'N/A' se não houver avaliação
        item['ver_partido'] = item.get('ver_partido', '')  # Partido vazio se não houver
        item['ver_foto'] = item.get('ver_foto', 'caminho/padrao.jpg')  # Caminho padrão para a foto se ausente

    cursor.close()
    connection.close()

    return jsonify(resultado)

@app.route('/vereadores')
def vereadores():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Obter parâmetros de filtro
    busca = request.args.get('busca', '').strip()

    # Construir a query base
    query = '''
        SELECT DISTINCT v.* 
        FROM vereadores v 
        WHERE 1=1
    '''
    params = []

    # Adicionar filtros condicionais
    if busca:
        termos = busca.split()
        if len(termos) > 1:
            nome = termos[0]
            partido = termos[1]
            query += ' AND (v.ver_nome LIKE %s AND v.ver_partido LIKE %s)'
            params.extend([f'%{nome}%', f'%{partido}%'])
        else:
            query += ' AND (v.ver_nome LIKE %s OR v.ver_partido LIKE %s)'
            params.extend([f'%{busca}%', f'%{busca}%'])

    # Ordenar por nome
    query += ' ORDER BY v.ver_nome'

    # Executar query
    cursor.execute(query, params)
    vereadores = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("lista-vereadores.html", 
                         vereadores=vereadores,
                         filtros={
                             'busca': busca
                         })

# Funções para a verificação do texto
def aliaseTxt(texto):
    substituicoes = {
        '@': 'a',
        '2': 'a',
        '4': 'a',
        '#': 'a',
        '3': 'e',
        '1': 'i',
        '0': 'o',
        '5': 's',
        '7': 't'
    }
    for letter in texto.lower():
        if letter in substituicoes:
            newletter = substituicoes[letter]
            texto = texto.replace(letter, newletter)
    return texto

def letrasRepetidas(texto):
    novoTexto= []
    for letra in texto:
        if len(novoTexto) == 0:
            novoTexto.append(letra)
        elif len(novoTexto) != 0 and letra != novoTexto[-1]:
            novoTexto.append(letra)
    novoTexto = ''.join(novoTexto)
    return novoTexto

def verificaTexto(texto):
    textoAliase =  aliaseTxt(texto)
    if profanity.contains_profanity(textoAliase.lower()) == True:
        return None
    else:
        newText = letrasRepetidas(textoAliase)
        if profanity.contains_profanity(newText.lower()) == True:
            print('Frase inválida')
            return newText
        else: 
            print('Frase válida')
            return texto
    
def AddAvaliacaoNoBancoDeDados(nome, nota, comentario, ver_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO avaliacao (nome, nota, comentario, ver_id) VALUES (%s, %s, %s, %s) ", (nome, nota, comentario, ver_id))
    connection.commit()
    cursor.close()
    connection.close()

async def getavaliacaoesByvereadorId (cursor, ver_id):
    await cursor.execute("SELECT * FROM avaliacao WHERE ver_id = %s", (ver_id,))
    avaliacoes = await cursor.fetchall()
    return avaliacoes

def avaliacoes_lista_to_obj(avaliacoes_vereador):
    lista = []
    listaNotas = []
    for avaliacao in avaliacoes_vereador:
        obj = {
            'id': avaliacao[0],
            'nome': avaliacao[1],
            'nota': avaliacao[2],
            'comentario': avaliacao[3],
            'datahora': avaliacao[4],
            'id_vereador': avaliacao[5]
        }
        listaNotas.append(avaliacao[2])
        lista.append(obj)
    avg = round(sum(listaNotas)/ len(listaNotas), 1) if len(listaNotas) > 0 else 0
    return lista, avg

  
@app.route('/vereadores/<int:vereador_id>', methods=['GET', 'POST'])
async def pagina_vereador(vereador_id):

    print(request.method)
    if request.method == 'POST':
        
        dados = request.get_data()
        # Decodifica para string e converte para JSON
        json_data = json.loads(dados.decode('utf-8'))

        # Validar o comentário
        # if tem_palavrao(json_data['nome'], json_data['comentario']):
        #      return jsonify({"message": "Comentário inválido, contém palavrão!"}), 403
        nome = verificaTexto(json_data['nome'])
        comentario = verificaTexto(json_data['comentario'])
        if nome == None or comentario == None:
            return jsonify({"message": "Comentário inválido, contém palavrão!"}), 403
        else:
            avalicoes_json = []
            
            # Chamar uma função para adicionar no banco de dados
            if AddAvaliacaoNoBancoDeDados(json_data['nome'], json_data['nota'], json_data['comentario'], vereador_id):
                # Buscar as avaliações do vereador no banco de dados
                avaliacoes =  getavaliacaoesByvereadorId(json_data['id_vereador'])
                
                # Formatar a resposta com a lista de avaliações
                avalicoes_json = [avaliacao.to_dict() for avaliacao in avaliacoes]
            return jsonify({"message": "Avaliação recebida com sucesso!", "avaliacoes": avalicoes_json}), 200
        
    
    if request.method == 'GET':
        # Configura o locale para português do Brasil
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

        # Start timing
        start_time = time.time()

        # Cria conexões e cursores independentes
        connection1_task = get_async_db_connection()
        connection2_task = get_async_db_connection()
        connection3_task = get_async_db_connection()
        connection4_task = get_async_db_connection()
        connection5_task = get_async_db_connection()
        connection6_task = get_async_db_connection()
        connection7_task = get_async_db_connection()
        connection8_task = get_async_db_connection()
        

        conn1, conn2, conn3, conn4, conn5, conn6, conn7, conn8 = await asyncio.gather(
            connection1_task, 
            connection2_task, 
            connection3_task, 
            connection4_task, 
            connection5_task, 
            connection6_task,
            connection7_task,
            connection8_task)

        # End timing
        end_time = time.time()
        # Calculate duration
        duration = end_time - start_time
        print(f"Connection process took {duration:.2f} seconds")

        async with conn1.cursor() as cursor1, \
                conn2.cursor() as cursor2, \
                conn3.cursor() as cursor3, \
                conn4.cursor() as cursor4, \
                conn5.cursor() as cursor5, \
                conn6.cursor() as cursor6, \
                conn7.cursor() as cursor7, \
                conn8.cursor() as cursor8:

            start_time = time.time()
            
            # Garante que cada função retorna uma tarefa única
            vereador_task = getVereadorById(cursor1, vereador_id)
            comissoesInfoGeral_task = getComissoesDetailByVereadorId(cursor2, vereador_id)
            all_comissoes_task = getAllComissoes(cursor3)
            proposicoes_task = getProposicoesByVereadorId(cursor4, vereador_id)
            assiduidadesVereador_task = getAssiduidadeVereador(cursor5, vereador_id)
            assiduidades_total_task = getAssiduidadesTotais(cursor6)
            extrato_votacao_task = getExtratoVotacaoByVereadorId(cursor7, vereador_id)
            avaliacoes_task =  getavaliacaoesByvereadorId(cursor8, vereador_id)

            # Aguarda as tarefas
            vereadorInfo, comissoesInfoGeral, proposicoesByVereador, all_comissoes, assiduidadesVereador, assiduidadesTotal, extrato_votacao, avaliacoes_vereador= await asyncio.gather(
                vereador_task, 
                comissoesInfoGeral_task, 
                proposicoes_task,
                all_comissoes_task,
                assiduidadesVereador_task,
                assiduidades_total_task,
                extrato_votacao_task,
                avaliacoes_task
            )
            
            lista_extrato_votacao = extratoVotacaoListaToObj(extrato_votacao)
            temas_unicos = sorted(set(item['tema'] for item in lista_extrato_votacao))

            end_time = time.time()
            # Calculate duration
            duration = end_time - start_time
            print(f"MySQL & assiduidade process took {duration:.2f} seconds")

            # Criar o objeto vereador e formatar o patrimônio
            vereadorObj = vereadorListaToObj(vereadorInfo)
            vereadorObj['ver_patrimonio'] = locale.currency(
                float(vereadorObj['ver_patrimonio']), symbol=True, grouping=True
            ).replace(" R$", "")

            listaComissoesObj=[]

            for comissao in all_comissoes:
                comissaoObj = comissaoListaToObj(comissao)
                listaComissoesObj.append(comissaoObj)

            listaInfoGeralComissao = []

            for comissao in comissoesInfoGeral:
                infoGeralComissao = comissaoDetalheToObj(comissao)
                listaInfoGeralComissao.append(infoGeralComissao)

            listaComissoes = gerarComissoesLista(listaInfoGeralComissao, listaComissoesObj)

            listaProposicoesObj = []
            for proposicao in proposicoesByVereador:
                proposicaoObj = proposicaoListaToObj(proposicao)
                listaProposicoesObj.append(proposicaoObj)

            chart_html = gerarGrafico(listaProposicoesObj)
            ver_assiduidade=comparar_assiduidades(assiduidadesVereador, assiduidadesTotal)
            
            avaliacoes, avg = avaliacoes_lista_to_obj(avaliacoes_vereador)
            avaliacao = {'ver_id': vereador_id,'avg': avg, 'qtd': len(avaliacoes)}

            # Renderiza o template com os dados
            return render_template('vereador.html',
                ver_assiduidade=ver_assiduidade,
                vereador=vereadorObj,
                comissoes=listaComissoes,
                proposicoes=listaProposicoesObj,
                chart_html=chart_html,
                avaliacoes=avaliacoes,
                avaliacao=avaliacao,
                lista_extrato_votacao=lista_extrato_votacao,
                temas=temas_unicos
            )

def extratoVotacaoListaToObj(extrato_votacao):
    lista_extrato_votacao = []
    
    for extrato in extrato_votacao:
        extrato_Obj = {
            'id_prop':extrato[0],
            'num_pl':extrato[1],
            'ano_pl':extrato[2],
            'resultado':extrato[3],
            'presidente':extrato[4],
            'ementa':extrato[5],
            'tema':extrato[6],
            'id_vereador':extrato[7],
            'voto':extrato[8],
        }
        lista_extrato_votacao.append(extrato_Obj)
    return lista_extrato_votacao

def gerarComissoesLista(listaInfoGeralComissao, listaComissoesObj):

    comissoes =[]

    for comissao in listaInfoGeralComissao:
        for i in range(len(listaComissoesObj)):
            if listaComissoesObj[i]['id'] == comissao['comissao_id']:
                comissaoObj = {
                    'comissao_id':comissao['comissao_id'], 
                    'cargo':comissao['cargo'],
                    'nome':listaComissoesObj[i]['nome'],
                    'data_inicio':listaComissoesObj[i]['data_inicio'],
                    'data_fim':listaComissoesObj[i]['data_fim'],
                    'link':listaComissoesObj[i]['link']
                }
                comissoes.append(comissaoObj)
    return comissoes
    


def gerarGrafico(listaProposicoesObj):
    # Dados de exemplo (aqui você usa os dados reais da variável 'proposicoes')
    categorias = ['Requerimentos', 'Moções', 'Projetos de Lei']

    requerimento, mocao, projeto_lei = calcularQtdProposicoes(listaProposicoesObj)

    valores = [requerimento,mocao, projeto_lei]

    fig = go.Figure([go.Bar(x=categorias, y=valores,marker_color='#193D87')])

    # Configurando o gráfico minimalista
    fig.update_layout(
        xaxis_visible=True,
        yaxis_visible=True,
        plot_bgcolor='rgba(0,0,0,0)',  # Remove o fundo
        paper_bgcolor='rgba(0,0,0,0)',  # Remove o fundo da área do gráfico
        xaxis_showgrid=False,  # Remove as linhas de grade do eixo X
        yaxis_showgrid=False,  # Remove as linhas de grade do eixo Y
        xaxis_title=None,  # Remove título do eixo X
        yaxis_title=None,  # Remove título do eixo Y
        showlegend=False,  # Remove a legenda
        title=None,  # Remove o título do gráfico
        margin=dict(t=10, b=10, l=10, r=10),
        bargap=0.2,  # Menor valor = barras mais finas
        bargroupgap=0.1,
        height=300,  # Tamanho fixo para a altura do gráfico
    )

    # Convertendo o gráfico para HTML
    chart_html = fig.to_html(full_html=False)
    return chart_html

def calcularQtdProposicoes(listaProposicoesObj):
    requerimento=0
    mocao=0
    projeto_lei=0
    for proposicao in listaProposicoesObj:
        if proposicao['tipo'] == 'Requerimento':
            requerimento+=1
        if proposicao['tipo'] == 'Moção':
            mocao+=1
        if proposicao['tipo'] == 'Projeto de Lei':
            projeto_lei+=1
    return requerimento, mocao, projeto_lei

def comparar_assiduidades(assiduidade_vereador, assiduidadeAllVereadores):

    total_participacoes = assiduidade_vereador['faltas'] + assiduidade_vereador['presencas'] + assiduidade_vereador['justificadas']

    ver_presenca = round((assiduidade_vereador['presencas'] / total_participacoes), 2) * 100
    ver_faltas = round((assiduidade_vereador['faltas'] / total_participacoes), 2) * 100
    ver_justificadas = round((assiduidade_vereador['justificadas'] / total_participacoes), 2) * 100

    vereadores = []

    total_presenca_geral = 0
    for vereador in assiduidadeAllVereadores:
        total_participacoes = vereador['faltas'] + vereador['presencas'] + vereador['justificadas']
        presencas = round((vereador['presencas'] / total_participacoes), 2) * 100
        faltas = round((vereador['faltas'] / total_participacoes), 2) * 100
        justificadas = round((vereador['justificadas'] / total_participacoes), 2) * 100
        total_presenca_geral += presencas

        vereadores.append({
            'presenca': presencas,
            'faltas': faltas,
            'justificadas': justificadas
        })

    # Ordenar vereadores pela presença
    vereadores.sort(key=lambda a: a['presenca'], reverse=True)

    # Calcular o 90º percentil
    n = len(vereadores)
    posicao_percentil_90 = (90 / 100) * (n + 1)

   # Encontrar o valor do 90º percentil
    if posicao_percentil_90.is_integer():
        percentil_90 = float(vereadores[int(posicao_percentil_90) - 1]['presenca'])
    else:
        # Interpolar
        pos1 = int(posicao_percentil_90) - 1
        pos2 = pos1 + 1
        percentil_90 = float(vereadores[pos1]['presenca']) + (posicao_percentil_90 - (pos1 + 1)) * (float(vereadores[pos2]['presenca']) - float(vereadores[pos1]['presenca']))


    comparacao = "acima" if presencas > percentil_90 else "inferior"
    comparacao_presencas = f"Este vereador tem presença {comparacao} a 90% dos vereadores."

    return {
        'porc_presenca': ver_presenca,
        'porc_faltas': ver_faltas,
        'porc_justificadas': ver_justificadas,
        'comparacao_presencas': comparacao_presencas
    }

# Função para buscar a consolidação de dados de Votação
async def getExtratoVotacaoByVereadorId(cursor, vereador_id):
    await cursor.execute(""" 
        SELECT 
            p.id_prop as id_prop,
            v.num_pl AS numero_pl,
            v.ano_pl AS ano_pl,
            v.resultado AS resultado,
            ver.ver_nome AS presidente,
            p.ementa AS ementa,
            p.tema AS tema,
            e.ver_id AS vereador_id,
            e.voto AS voto
        FROM votacao v
        RIGHT JOIN extrato_votacao e ON v.id = e.votacao_id 
        INNER JOIN proposicoes p ON p.numero = v.num_pl AND p.ano = v.ano_pl
        LEFT JOIN vereadores ver ON v.presidente = ver.ver_id
        WHERE e.ver_id = %s AND p.tema <> ''
    """, (vereador_id,))
    resultado = await cursor.fetchall()
    return resultado

# Função para buscar os dados do vereador com cursor assíncrono
async def getVereadorById(cursor, vereador_id):
    await cursor.execute('SELECT * FROM vereadores WHERE ver_id = %s', (vereador_id,))
    vereador = await cursor.fetchone()
    return vereador

# Função para buscar as comissões do vereador com cursor assíncrono
async def getComissoesDetailByVereadorId(cursor, vereador_id):
    await cursor.execute('SELECT * FROM vereadores_comissoes WHERE ver_id = %s', (vereador_id,))
    comissoes = await cursor.fetchall()
    return comissoes

# Função para buscar as comissões do vereador com cursor assíncrono
async def getProposicoesByVereadorId(cursor, vereador_id):
    await cursor.execute('SELECT * FROM proposicoes WHERE ver_id = %s', (vereador_id,))
    proposicoesByVereador = await cursor.fetchall()

    return proposicoesByVereador

# Função para buscar uma comissão específica com cursor assíncrono
async def getAllComissoes(cursor):
    await cursor.execute('SELECT * FROM comissoes')
    comissoes = await cursor.fetchall()
    return comissoes

async def getAssiduidadeVereador(cursor, ver_id):
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
    await cursor.execute(query, (ver_id,))
    assiduidadeVereador = await cursor.fetchall()

    assiduidadeObj = assiduidadeToObj(assiduidadeVereador)

    return assiduidadeObj

def assiduidadeToObj(assiduidadeVereador):
    return {
        'ver_id':assiduidadeVereador[0][0],
        'faltas':assiduidadeVereador[0][1],
        'presencas':assiduidadeVereador[0][2],
        'justificadas':assiduidadeVereador[0][3],
    }


async def getAssiduidadesTotais(cursor):
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
    await cursor.execute(query)
    assiduidadesTotais = await cursor.fetchall()

    listaAssiduidades = []

    for assid in assiduidadesTotais:
        assidObj = {
            'ver_id':assid[0],
            'faltas':assid[1],
            'presencas':assid[2],
            'justificadas':assid[3]
        }
        listaAssiduidades.append(assidObj)
    return listaAssiduidades

def proposicaoListaToObj(proposicao):
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
    return proposicaoObj

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
        "ver_foto":vereador[8],
        "ver_biografia":vereador[9],
        "ver_patrimonio":vereador[10],
        "posicao_politica":vereador[11]
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
        placeholders = ', '.join(['%s'] * len(tipos))
        query += f' AND tipo IN ({placeholders})'
        count_query += f' AND tipo IN ({placeholders})'
        params.extend(tipos)
    
    # Converter Mocao de volta para Moção para a query do banco
    tipos_convertidos = []
    if tipos:
        for tipo in tipos:
            if tipo == 'Mocao':
                tipos_convertidos.append('Moção')
            else:
                tipos_convertidos.append(tipo)
        
        placeholders = ', '.join(['%s'] * len(tipos_convertidos))
        query += f' AND tipo IN ({placeholders})'
        count_query += f' AND tipo IN ({placeholders})'
        params.extend(tipos_convertidos)
    
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
    if (nome_vereador) in vereador_cache:
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
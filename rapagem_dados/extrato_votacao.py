import camelot
import pandas as pd
import PyPDF2
import re
import json
from tqdm import tqdm
import time  # para simular requisições

# Lê todas as tabelas do PDF
tables = camelot.read_pdf("votacao.pdf", pages='all', flavor='stream')

# Variáveis para armazenar o autor e PL
autor = ""
pl = ""

lista_vereadores = [
    "Amélia Naomi",
    "Dulce Rita",
    "Fernando Petiti",
    "Juliana Fraga",
    "Juvenil Silvério",
    "Lino Bispo",
    "Marcão da Academia",
    "Robertinho da Padaria",
    "Walter Hayashi",
    "Roberto do Eleven",
    "Zé Luis",
    "Dr. José Claudio",
    "Thomaz Henrique",
    "Roberto Chagas",
    "Milton Vieira Filho",
    "Rafael Pascucci",
    "Marcelo Garcia",
    "Renato Santiago",
    "Júnior da Farmácia",
    "Fabião Zagueiro",
    "Rogério da Acasem"
]

# LISTA DE INFORMAÇÃO DAS PLS 
extrato_info_pls = []

def normalize_texto_linha(nome):
    return nome.replace("\n", "").strip()

# Percorre todas as tabelas e busca pelas linhas com o nome e o voto dos vereadores
def buscar_extrato_votacao(tables):

    # LISTA DOS JSONS EXTRATO DE VOTAÇÃO PARA SALVAR
    extrato_votacao_lista = []
    
    votacoes = []

    for table_idx, table in enumerate(tables):
        print(f"Realizando requisição {table_idx + 1}")
        df = table.df

        # Verifica se há pelo menos 4 colunas e ignora as tabelas que não têm os dados desejados
        if df.shape[1] < 2:
            continue

        vereador = ''
        voto = ''
        
        # Itera pelas linhas da tabela atual para capturar vereadores e votos
        for i in range(len(df)):
            coluna = df.iloc[i]
            lista_voto = ["Contrário", "Favorável", "Presidente*"]
            
            for j in range(0,len(coluna)):
                texto_linha = normalize_texto_linha(coluna[j])
                if texto_linha != '' and texto_linha not in lista_voto and texto_linha in lista_vereadores:
                    vereador = texto_linha
                
                elif texto_linha != '' and texto_linha in lista_voto:
                    voto = texto_linha

                if vereador != '' and voto != '':
                    extrato = {"vereador":vereador,"voto":voto}
                    extrato_votacao_lista.append(extrato)
                    vereador=''
                    voto=''
        
        votacoes.append({
            "tabela":table_idx + 1,
            "extrato_votacao":extrato_votacao_lista
        })
        extrato_votacao_lista = []
    
    # Retorna a lista de json
    return votacoes

# Função para buscar texto em um PDF
def buscar_texto_pdf(path_to_pdf):

    projetos = []

    with open(path_to_pdf, 'rb') as file:
        reader = PyPDF2.PdfReader(file)

        # Itera página por página
        for pagina in range(len(reader.pages)):
            texto = reader.pages[pagina].extract_text()

            # Expressão regular para encontrar os dados
            # O padrão busca o número do projeto, o ano e o auto
            
           # Padrão flexível para capturar número, ano, autor e resultado com formatação inconsistente

           # Número e ano, com espaços e quebras
           # Autor com texto e espaços variados
           # Resultado com texto e espaços variados
            padrao_flexivel = (
                r'(?:Projeto de (?:Lei|Decreto Legislativo|Emenda)(?: nº)?\s*(\d+)[\s\n]*/[\s\n]*(\d{4}))?'
                r'.*?(?:Autoria:\s*([\w\s]+?))?'
                r'.*?(?:Resultado:\s*([\w\s]+))?'
            )

            # Busca todas as ocorrências no texto usando findall
            resultados = re.findall(padrao_flexivel, texto, re.DOTALL | re.IGNORECASE)

            # Exibe cada correspondência encontrada
            for i, (numero, ano, autor, resultado_status) in enumerate(resultados, 1):
                print(f"\nProjeto {i}:")
                print(f"Número: {numero}")
                print(f"Ano: {ano}")
                print(f"Autor: {autor}")
                print(f"Resultado: {resultado_status}")

            # Armazene os dados em uma lista de dicionários
            # for numero, ano, autor in resultados:
            #     projetos.append({
            #         'numero': numero,
            #         'ano': ano,
            #         'autor': autor.strip()
            #     })

    # Retorna a lista de JSONS com informações de nº PL, ano e autoria
    return projetos


def main():

    # Criar um código para iterar entre vários pdfs do diretório
        ## TODO

    # Ao abrir cada pdf, busca as referências de nº pl e ano e autoria
    projeto_de_lei = buscar_texto_pdf("votacao.pdf")

    # print(projeto_de_lei)
    # Faz a chamada para buscar o extrato de votação no pdf.
    # extrato = buscar_extrato_votacao(tables)

    # AQUI VAI A LOGICA PARA SALVAR O ARQUIVO extrato EM UM JSON

    # output_path = "output/extrato_votacao_tabela.json"
    # with open(output_path, 'a', encoding='utf-8') as f:
    #    json.dump(extrato, f, indent=4, ensure_ascii=False)

# Chamada para executar a função MAIN
main()
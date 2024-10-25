import camelot
import pandas as pd
import PyPDF2
import re
import json

# Lê todas as tabelas do PDF
tables = camelot.read_pdf("votacao.pdf", pages='all', flavor='stream')

# Variáveis para armazenar o autor e PL
autor = ""
pl = ""

nomes = [
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

# Percorre todas as tabelas e busca pelas linhas com o nome e o voto dos vereadores
def buscar_extrato_votacao(tables):

    # LISTA DOS JSONS EXTRATO DE VOTAÇÃO PARA SALVAR
    extrato_votacao_lista = []
    
    votacoes = []

    for table_idx, table in enumerate(tables):
        
        df = table.df

        # Verifica se há pelo menos 4 colunas e ignora as tabelas que não têm os dados desejados
        if df.shape[1] < 2:
            continue

        vereador = ''
        voto = ''
        
        # Itera pelas linhas da tabela atual para capturar vereadores e votos
        for i in range(len(df)):
            coluna = df.iloc[i]

            # print(coluna)
            lista_voto = ["Contrário", "Favorável", "Presidente*"]

            for j in range(0,5):

                if coluna[j].strip() != '' and coluna[j].strip() not in lista_voto and coluna[j].strip() in nomes:
                    # print(f"vereador: {coluna[j]}")
                    vereador = coluna[j].strip()
                
                elif coluna[j].strip() != '' and coluna[j].strip() in lista_voto:
                    # print(f"voto: {coluna[j]}")
                    voto = coluna[j].strip()

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
            
            # Padrão para capturar número, ano, autor e resultado
            padrao = r'(?:(?:Projeto de Lei nº|Emenda nº|Projeto de Decreto Legislativo nº)\s*(\d+)/(\d{4})\s*-\s*Autoria:\s*(.+?)(?:\s+ao)?\s*(?:Projeto de Lei nº \d+/\d+)?(?:\s*Resultado:\s*(.+?))?)'

            resultados = re.findall(padrao, texto)

            print(resultados)

            # Exibir os resultados encontrados
            for resultado in resultados:
                numero = resultado[0]
                ano = resultado[1]
                autor = resultado[2].strip()
                resultado_texto = resultado[3].strip() if len(resultado) > 3 and resultado[3] else "Não especificado"
                print(f"Número do Projeto: {numero}, Ano: {ano}, Autor: {autor}, Resultado: {resultado_texto}")

            # Armazene os dados em uma lista de dicionários
            for numero, ano, autor in resultados:
                projetos.append({
                    'numero': numero,
                    'ano': ano,
                    'autor': autor.strip()
                })

    # Retorna a lista de JSONS com informações de nº PL, ano e autoria
    return projetos


def main():

    # Criar um código para iterar entre vários pdfs do diretório
        ## TODO

    # Ao abrir cada pdf, busca as referências de nº pl e ano e autoria
    projeto_de_lei = buscar_texto_pdf("votacao.pdf")

    print(projeto_de_lei)
    # Faz a chamada para buscar o extrato de votação no pdf.
    extrato = buscar_extrato_votacao(tables)

    # AQUI VAI A LOGICA PARA SALVAR O ARQUIVO extrato EM UM JSON
    # print(extrato)
    output_path = "output/extrato_votacao_tabela.json"
    with open(output_path, 'a', encoding='utf-8') as f:
        json.dump(extrato, f, indent=10, ensure_ascii=False)

# Chamada para executar a função MAIN
main()
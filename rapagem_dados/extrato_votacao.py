import camelot
import pandas as pd
import PyPDF2
import re

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


# LISTA DOS JSONS EXTRATO DE VOTAÇÃO PARA SALVAR
extrato_lista = []

# LISTA DE INFORMAÇÃO DAS PLS 
extrato_pls = []

# Percorre todas as tabelas e busca pelas linhas com o nome e o voto dos vereadores
def buscar_extrato_votacao(tables):
    for table_idx, table in enumerate(tables):
        df = table.df
        print(f"--- Tabela {table_idx+1} ---")

        # print(df)
        
        # Verifica se a tabela contém o cabeçalho com o autor e PL
        if "autoria" in df.iloc[0, 0].lower():
            for i in range(df.shape[0]):
                linha = df.iloc[i, 0]
                if "autoria" in linha.lower():
                    autor = linha.split("Autoria:")[-1].strip()
                if "projeto de lei" in linha.lower():
                    pl = linha.split("Projeto de Lei")[-1].strip()
            print(f"Autor: {autor}")
            print(f"Projeto de Lei: {pl}")
        
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
                    extrato_lista.append(extrato)
                    vereador=''
                    voto=''

# Função para buscar texto em um PDF
def buscar_texto_pdf(pdf, texto_busca):
    with open(pdf, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for pagina in range(len(reader.pages)):
            texto = reader.pages[pagina].extract_text()

            # Expressão regular para encontrar os dados
            # O padrão busca o número do projeto, o ano e o autor
            padrao = r'Projeto de Lei nº (\d+)/(\d{4}) - Autoria: Ver\.?(?:\.ª)? (.+?)\s*(?=Resultado:|$)'

            # Encontre todas as correspondências
            resultados = re.findall(padrao, texto)

            # Armazene os dados em uma lista de dicionários
            projetos = []
            for numero, ano, autor in resultados:
                projetos.append({
                    'numero': numero,
                    'ano': ano,
                    'autor': autor.strip()
                })

            # Exiba os resultados
            for projeto in projetos:
                print(f"Número: {projeto['numero']}, Ano: {projeto['ano']}, Autor: {projeto['autor']}")

            if texto and texto_busca.lower() in texto.lower():
                print(f'Texto encontrado na página {pagina + 1}:')
                # print(texto)

buscar_texto_pdf("votacao.pdf", "Projeto de Lei")

# Faz a chamada para buscar o extrato de votação no pdf.
buscar_extrato_votacao(tables)
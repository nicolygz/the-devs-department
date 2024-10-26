import camelot
import pandas as pd
import PyPDF2
import re
import os
import json
from PyPDF2 import PdfReader

# Lê todas as tabelas do PDF
# filename = f"sessao_{i + 1}.pdf"
# tables = camelot.read_pdf("votacao.pdf", pages='all', flavor='stream')

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

# Normaliza o texto
def normalize_texto_linha(nome):
    return nome.replace("\n", "").strip()

# Percorre todas as tabelas e busca pelas linhas com o nome e o voto dos vereadores
def buscar_extrato_votacao(tables):
    votacoes = []
    id_votacao = 1  # ID único para cada votação

    for table_idx, table in enumerate(tables):
        print(f"Realizando requisição {table_idx + 1}")
        df = table.df

        # Verifica se há pelo menos 4 colunas e ignora as tabelas que não têm os dados desejados
        if df.shape[1] < 2:
            continue

        extrato_votacao_lista = []
        vereador = ''
        voto = ''

        # Itera pelas linhas da tabela atual para capturar vereadores e votos
        for i in range(len(df)):
            coluna = df.iloc[i]
            lista_voto = ["Contrário", "Favorável", "Presidente*"]

            for j in range(0, len(coluna)):
                texto_linha = normalize_texto_linha(coluna[j])
                if texto_linha != '' and texto_linha not in lista_voto and texto_linha in lista_vereadores:
                    vereador = texto_linha

                elif texto_linha != '' and texto_linha in lista_voto:
                    voto = texto_linha

                if vereador != '' and voto != '':
                    extrato = {"vereador": vereador, "voto": voto}
                    extrato_votacao_lista.append(extrato)
                    vereador = ''
                    voto = ''

        # Estrutura final da votação com o novo formato especificado
        votacoes.append({
            "id": id_votacao,
            "num_pl": None,  # Defina ou substitua conforme necessário
            "resultado": {
                "status": "Aprovada",  # Exemplo de status
                "vereadores": extrato_votacao_lista
            },
            "presidente": None,
            "autoria_pl": None,
            "tabela": table_idx + 1
        })
        id_votacao += 1  # Incrementa o ID único

    # Retorna a lista de JSONs
    return votacoes

pasta_pdfs = "downloaded_pdfs"

resultados = []

for i in range(23):
    pdfs = os.path.join(pasta_pdfs, f"sessao_{i + 1}.pdf")
    tables = camelot.read_pdf(pdfs, pages='all', flavor='stream')
    votacao = buscar_extrato_votacao(tables)
    resultados.extend(votacao)  # Adiciona cada votação com formato final ao resultado

# Certifique-se de que a pasta 'json' existe
os.makedirs("json", exist_ok=True)

# Salva os resultados em um arquivo JSON dentro da pasta 'json'
with open("json/resultados_votacao.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=4)

print("Os resultados foram salvos em 'json/resultados_votacao.json'")
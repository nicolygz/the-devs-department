import requests
from bs4 import BeautifulSoup
import os
import json

# Muda o diretório de trabalho para 'rapagem_dados'
#os.chdir("/Users/pedrovaz/Library/Mobile Documents/com~apple~CloudDocs/iCloud/4. Estudos/Fatec - DSM/1-SEM/API/the-devs-department/rapagem_dados/output")

# Agora salve o arquivo
file_path = "/Users/pedrovaz/Library/Mobile Documents/com~apple~CloudDocs/iCloud/4. Estudos/Fatec - DSM/1-SEM/API/the-devs-department/rapagem_dados/output/links_para_leis.txt"

def buscar_tema(soup):
    # Encontrar o elemento <p> com o id "ContentPlaceHolder1_p_temas"
    p_element = soup.find('p', id='ContentPlaceHolder1_p_temas')

    if p_element:
        # Extrair o texto do link dentro do <p>
        a_element = p_element.find('a')
        if a_element:
            tema = a_element.text.strip()  # "Educação"
            return tema
        else:
            print('Elemento <a> não encontrado.')
    else:
        print('Elemento <p> não encontrado.')


def buscar_num_ano(soup):
    # Encontrar o elemento <span> com o id "ContentPlaceHolder1_span_proposicao"
    span_element = soup.find('span', id='ContentPlaceHolder1_span_proposicao')
    if span_element:
        # Extrair o texto do link dentro do <span>
        a_element = span_element.find('a')
        if a_element:
            texto = a_element.text.strip()  # "Projeto de Lei 236/2022"
            
            # Extrair os números da proposta e do ano
            pl, ano = texto.split()[-1].split('/')  # Pega "236/2022" e divide
            pl = pl.strip()  # "236"
            ano = ano.strip()  # "2022"
            
            return {"num":pl,"ano":ano}
        else:
            None
    else:
        return None

def buscar_num_processo(soup):
    # Encontrar o elemento <span> com o id "ContentPlaceHolder1_span_proposicao"
    span_element = soup.find('span', id='ContentPlaceHolder1_span_processo_numero')
    if span_element:
        return span_element.text.strip()
    else:
        # Se o elemento não for encontrado, retornar None
        return ""


# Função para extrair informações de uma página
def extrair_informacoes(url):
    response = requests.get(url)
    if response.status_code == 200:
        # Parsear o conteúdo HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Trazer o tema
        tema = buscar_tema(soup)

        # Trazer o numero da proposta e ano do PL
        dict_num_ano = buscar_num_ano(soup)

        num_pl = ""
        ano_pl = ""

        if dict_num_ano:
            num_pl = dict_num_ano["num"]
            ano_pl = dict_num_ano["ano"]


        # Buscar número do processo
        num_processo = buscar_num_processo(soup)

        json = {
            "num_processo":num_processo,
            "tema":tema,
            "num_pl":num_pl,
            "ano_pl":ano_pl
        }

        salvar_json(json)

        print(json)
        print()
       
        # print(f"\nPL nº {num_pl}/{ano_pl}, \ntema: {tema}\nnº processo: {num_processo}\n")

        
    else:
        print(f'Erro ao acessar {url}: Status {response.status_code}')


def salvar_json(json):
    
    file_path = "/Users/pedrovaz/Library/Mobile Documents/com~apple~CloudDocs/iCloud/4. Estudos/Fatec - DSM/1-SEM/API/the-devs-department/rapagem_dados/output/pl_com_temas.json"

    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(json)  # Salvar o href no arquivo

# Ler links do arquivo e fazer requisições
with open(file_path, 'r', encoding='utf-8') as file:
    c = 1
    for linha in file:
        print(f">> linha: {c}")
        url = linha.strip()  # Remove espaços em branco e quebras de linha
        if url:  # Verifica se a linha não está vazia
            extrair_informacoes(url)
        c+= 1
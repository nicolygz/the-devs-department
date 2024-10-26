import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import os

# Caminho do arquivo de saída
file_path = "/Users/pedrovaz/Library/Mobile Documents/com~apple~CloudDocs/iCloud/4. Estudos/Fatec - DSM/1-SEM/API/the-devs-department/rapagem_dados/output/links_para_leis.txt"

listaJson = []

async def buscar_tema(soup):
    p_element = soup.find('p', id='ContentPlaceHolder1_p_temas')
    if p_element:
        a_element = p_element.find('a')
        if a_element:
            return a_element.text.strip()
    return None

async def buscar_num_ano(soup):
    span_element = soup.find('span', id='ContentPlaceHolder1_span_proposicao')
    if span_element:
        a_element = span_element.find('a')
        if a_element:
            texto = a_element.text.strip()
            pl, ano = texto.split()[-1].split('/')
            return {"num": pl.strip(), "ano": ano.strip()}
    return None

async def buscar_num_processo(soup):
    span_element = soup.find('span', id='ContentPlaceHolder1_span_processo_numero')
    return span_element.text.strip() if span_element else ""

# Função para extrair informações de uma página assíncronamente
async def extrair_informacoes(session, url):
    async with session.get(url) as response:
        if response.status == 200:

            # Transforma o HTML em TEXT
            html = await response.text()

            # Transforma o HTML em um elemento soup
            soup = BeautifulSoup(html, 'html.parser')

            
            # Chama buscar_tema() que retira o elemento HTML que tem o TEMA
            tema = await buscar_tema(soup)

            # Chama buscar_num_ano() que retira o elemento HTML que tem o num e ano de proposição
            dict_num_ano = await buscar_num_ano(soup)

            # Chama buscar_num_processo() que retira o elemento HTML que tem o num_processo
            num_processo = await buscar_num_processo(soup)
            
            num_pl, ano_pl = "", ""
            
            if dict_num_ano:
                num_pl = dict_num_ano["num"]
                ano_pl = dict_num_ano["ano"]

            # Com todas essas informações retorna um dicionário
            return {
                "num_processo": num_processo,
                "tema": tema,
                "num_pl": num_pl,
                "ano_pl": ano_pl
            }
        else:
            return None

# Função para salvar o JSON em um arquivo
def salvar_json(listaJson):
    output_path = "/Users/pedrovaz/Library/Mobile Documents/com~apple~CloudDocs/iCloud/4. Estudos/Fatec - DSM/1-SEM/API/the-devs-department/rapagem_dados/output/pl_com_temas.json"
    with open(output_path, 'a', encoding='utf-8') as f:
        json.dump(listaJson, f, indent=10, ensure_ascii=False)

# Função assíncrona principal
async def main():
    async with aiohttp.ClientSession() as session:
        tasks = []

        # Ler links do arquivo e criar tarefas
        with open(file_path, 'r', encoding='utf-8') as file:
            for c, linha in enumerate(file, 1):
                print(f">> Processando linha: {c}")
                url = linha.strip()
                if url:
                    tasks.append(extrair_informacoes(session, url))

        # Executar as tarefas em paralelo
        resultados = await asyncio.gather(*tasks)

        # Filtrar resultados válidos e salvar
        listaJson = [resultado for resultado in resultados if resultado]
        salvar_json(listaJson)

# Executar o loop assíncrono
if __name__ == "__main__":
    asyncio.run(main())

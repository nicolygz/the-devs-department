from flask import Flask, render_template
import mysql.connector
import requests
from bs4 import BeautifulSoup
import json
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
from flask import Flask, render_template
import mysql.connector
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

# Configurações do banco de dados
db_config = {
    'host': '[SEGREDO]',
    'user': '[SEGREDO]',
    'password': '[SEGREDO]',
    'database': '[SEGREDO]'
}

def connect_to_db():
    return mysql.connector.connect(**db_config)

# Supondo que você tenha um valor para `id`
id_value = '35'  # Defina o ID aqui

# URL da página
url = 'https://camarasempapel.camarasjc.sp.gov.br/parlamentar.aspx?id=' + id_value

print(url)

response = requests.get(url)
# Verificando se a requisição foi bem-sucedida
if response.status_code == 200:
    
    # Criando um objeto BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Encontrando a imagem pelo class name
    form = soup.find('form', id="formulario")
    if form:
        # Extraindo o ID da URL
        ver_id = form['action'].split('id=')[-1]
        
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
                for div in divs:
                    if 'Telefone' in div.text.strip():
                        telefones = div.text.split(':')[-1].strip().split("/")
                        ver_tel1 = telefones[0].strip()
                        if len(telefones) > 1:
                            ver_tel2 = telefones[1].strip()
                    if 'Celular' in div.text.strip():
                        ver_celular = div.text.split(":")[-1].strip()
                        if "A Câmara não disponibiliza celular para os vereadores" in ver_celular:
                            ver_celular = "-"
                    if 'E-mail' in div.text.strip():
                        ver_email = div.text.split(":")[-1].strip()
        
        vereador = {
            "ver_id": ver_id,
            "ver_nome": ver_nome,
            "ver_partido": ver_partido,
            "ver_tel1": ver_tel1, 
            "ver_tel2": ver_tel2, 
            "ver_celular": ver_celular, 
            "ver_email": ver_email, 
            "ver_foto": ver_foto
        }

        # Adicionando ao banco de dados
        try:
            db_connection = connect_to_db()
            cursor = db_connection.cursor()

            # Verificando duplicatas
            check_query = "SELECT COUNT(*) FROM vereadores WHERE ver_id = %s"
            cursor.execute(check_query, (ver_id,))
            result = cursor.fetchone()

            if result[0] == 0:  # Se não existe duplicata
                insert_query = """
                INSERT INTO vereadores (ver_id, ver_nome, ver_partido, ver_tel1, ver_tel2, ver_celular, ver_email, ver_foto) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    ver_id,
                    ver_nome,
                    ver_partido,
                    ver_tel1,
                    ver_tel2,
                    ver_celular,
                    ver_email,
                    ver_foto
                ))
                db_connection.commit()
                print("Vereador adicionado ao banco de dados.")
            else:
                print("Vereador já existe no banco de dados.")

        except mysql.connector.Error as err:
            print(f"Erro ao interagir com o banco de dados: {err}")
        finally:
            cursor.close()
            db_connection.close()
else:
    print(f"Erro ao acessar a URL: {response.status_code}")

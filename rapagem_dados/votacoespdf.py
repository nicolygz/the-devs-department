import requests
import pdfplumber
import re
import os
import json

# Cria a pasta para armazenar PDFs baixados
os.makedirs("downloaded_pdfs", exist_ok=True)

# Extrai todas as URLs de PDFs do texto fornecido
txt = '''Ordinária    58      Extrato da Votação Eletrônica - Nº 58  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2428/sessao_2428_202410111342060849818ZYZSI.pdf?identificador=30003A005300   10/10/2024  16:00                    
Ordinária    56      Extrato da Votação Eletrônica - Nº 56  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2426/sessao_2426_202410041200521778769GQIO8.pdf?identificador=30003A005300   03/10/2024  16:00                    
Ordinária    54      Extrato da Votação Eletrônica - Nº 54  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2424/sessao_2424_202409271526045290448MTJX6.pdf?identificador=30003A005300   26/09/2024  16:00                    
Ordinária    52      Extrato da Votação Eletrônica - Nº 52  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2422/sessao_2422_2024092015561166996004UEGF.pdf?identificador=30003A005300   19/09/2024  16:00                    
Ordinária    46      Extrato da Votação Eletrônica - Nº 46  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2415/sessao_2415_202408301122556148058GI87A.pdf?identificador=30003A005300   29/08/2024  16:00                    
Ordinária    44      Extrato da Votação Eletrônica - Nº 44  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2412/sessao_2412_202408231130244072884US1KQ.pdf?identificador=30003A005300   22/08/2024  16:00                    
Ordinária    42      Extrato da Votação Eletrônica - Nº 42  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2410/sessao_2410_202408161150248186549WSIEN.pdf?identificador=30003A005300   15/08/2024  16:00                    
Ordinária    40      Extrato da Votação Eletrônica - Nº 40  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2398/sessao_2398_202408091414595254867P5MG5.pdf?identificador=30003A005300   08/08/2024  16:00                    
Ordinária    39      Extrato da Votação Eletrônica - Nº 39  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2397/sessao_2397_202408071440147956781NA8VG.pdf?identificador=30003A005300   06/08/2024  16:00                    
Ordinária    38      Extrato da Votação Eletrônica - Nº 38  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2396/sessao_2396_2024080211514157025517UF44.pdf?identificador=30003A005300   01/08/2024  16:00                    
Ordinária    37      Extrato da Votação Eletrônica - Nº 37  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2393/sessao_2393_2024062717012729426494CMGY.pdf?identificador=30003A005300   27/06/2024  08:30                    
Ordinária    36      Extrato da Votação Eletrônica - Nº 36  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2392/sessao_2392_202406261339193122036ULVN2.pdf?identificador=30003A005300   25/06/2024  16:00                    
Ordinária    35      Extrato da Votação Eletrônica - Nº 35  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2391/sessao_2391_2024062111293378747807A07E.pdf?identificador=30003A005300   20/06/2024  16:00                    
Ordinária    34      Extrato da Votação Eletrônica - Nº 34  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2389/sessao_2389_2024061911045293118900TAMV.pdf?identificador=30003A005300   18/06/2024  16:00                    
Ordinária    33      Extrato da Votação Eletrônica - Nº 33  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2388/sessao_2388_202406141006353542749BNL22.pdf?identificador=30003A005300   13/06/2024  16:00                    
Ordinária    32      Extrato da Votação Eletrônica - Nº 32  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2387/sessao_2387_202406121057006927083PJTIO.pdf?identificador=30003A005300   11/06/2024  16:00                    
Ordinária    31      Extrato da Votação Eletrônica - Nº 31  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2385/sessao_2385_202406071140000159252XUBU4.pdf?identificador=30003A005300   06/06/2024  16:00                    
Ordinária    30      Extrato da Votação Eletrônica - Nº 30  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2384/sessao_2384_202406051004008069653I6RAY.pdf?identificador=30003A005300   04/06/2024  16:00                    
Ordinária    29      Extrato da Votação Eletrônica - Nº 29  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2381/sessao_2381_202405291430164566683G393U.pdf?identificador=30003A005300   28/05/2024  16:00                    
Ordinária    28      Extrato da Votação Eletrônica - Nº 28  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2380/sessao_2380_2024052410594969832600RBP2.pdf?identificador=30003A005300   23/05/2024  16:00                    
Ordinária    27      Extrato da Votação Eletrônica - Nº 27  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2379/sessao_2379_202405221125028312178B6LTE.pdf?identificador=30003A005300   21/05/2024  16:00                    
Ordinária    26      Extrato da Votação Eletrônica - Nº 26  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2377/sessao_2377_202405171139048707472ZJAS9.pdf?identificador=30003A005300   16/05/2024  16:00                    
Ordinária    25      Extrato da Votação Eletrônica - Nº 25  https://camarasempapel.camarasjc.sp.gov.br/Arquivo/Documents/SES/2376/sessao_2376_202405151524332652867AML0A.pdf?identificador=30003A005300   14/05/2024  16:00  '''

# Expressão regular para capturar URLs válidas de PDF
pdf_urls = re.findall(r"https://camarasempapel\.camarasjc\.sp\.gov\.br/[^ ]+\.pdf\?identificador=[\w\d]+", txt)

# Função para baixar e extrair texto de um PDF
def download_and_extract_pdf(url, filename):
    try:
        print(f"Downloading: {filename}")
        response = requests.get(url, timeout=10)  # Timeout para confiabilidade
        response.raise_for_status()  # Levanta erro para falhas na requisição

        # Salva o PDF localmente
        pdf_path = os.path.join("downloaded_pdfs", filename)
        with open(pdf_path, "wb") as file:
            file.write(response.content)

        # Extrai texto do PDF
        with pdfplumber.open(pdf_path) as pdf:
            text = "".join([page.extract_text() or "" for page in pdf.pages])

        print(f"Extracted text from {filename}.")
        return text

    except requests.exceptions.RequestException as e:
        print(f"Network error while downloading {filename}: {e}")
    except pdfplumber.pdf.PDFSyntaxError as e:
        print(f"Failed to open PDF {filename}: {e}")
    except Exception as e:
        print(f"Unexpected error with {filename}: {e}")
    return ""  # Retorna string vazia se falhar

# Função para extrair campos específicos do texto
import re

def extract_fields_from_text(text):
    # Extrai todos os números de PL entre "Processo" e "Autoria"
    pl_matches = re.findall(r"(Processo.*?Projeto de Lei nº (\d+)/(\d+).*?Autoria.*?)(?=Processo|$)", text, re.DOTALL)

    # Cria uma lista para armazenar todos os projetos de lei encontrados
    pl_list = []

    for match in pl_matches:
        pl_text = match[0]  # Parte do texto específica do PL atual
        num_pl = f"{match[1]}{match[2]}"  # Concatena número e ano (ex: 4682021)

        # Extrai outras informações para cada PL dentro do trecho correspondente
        resultado = re.search(r"Resultado:\s*(\w+)", pl_text)
        presidente = re.search(r"Presidente:\s*(\d+)", pl_text)
        autoria_pl = re.search(r"Autoria:\s*(\d+)", pl_text)

        # Cria um dicionário com as informações do PL atual
        pl_data = {
            "num_pl": int(num_pl),
            "resultado": resultado.group(1) if resultado else "",
            "presidente": int(presidente.group(1)) if presidente else None,
            "autoria_pl": int(autoria_pl.group(1)) if autoria_pl else None
        }

        # Adiciona o dicionário à lista de PLs
        pl_list.append(pl_data)

    return pl_list

# Lista para armazenar todos os objetos extraídos de todos os PDFs
extracted_data = []

# Itera sobre as URLs extraídas e baixa + extrai o texto de cada PDF
for i, url in enumerate(pdf_urls):
    filename = f"sessao_{i + 1}.pdf"
    pdf_text = download_and_extract_pdf(url, filename)
    if pdf_text:
        # Extrai uma lista de projetos de lei para o PDF atual
        pl_list = extract_fields_from_text(pdf_text)

        # Adiciona cada PL encontrado ao JSON com um ID sequencial
        for pl in pl_list:
            pl["id"] = len(extracted_data) + 1  # Garante ID único para cada PL
            extracted_data.append(pl)  # Adiciona o PL à lista geral

# Salva os dados extraídos em um arquivo JSON
with open("extracted_data.json", "w", encoding="utf-8") as json_file:
    json.dump(extracted_data, json_file, ensure_ascii=False, indent=4)

print("Todos os PDFs foram processados e os dados salvos em extracted_data.json.")
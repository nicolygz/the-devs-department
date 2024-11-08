import pdfplumber
import json
import re
import os

# Lista de vereadores para referência
lista_vereadores = [
    "Amélia Naomi", "Dulce Rita", "Fernando Petiti", "Juliana Fraga",
    "Juvenil Silvério", "Lino Bispo", "Marcão da Academia",
    "Robertinho da Padaria", "Walter Hayashi", "Roberto do Eleven",
    "Zé Luis", "Dr. José Claudio", "Thomaz Henrique", "Roberto Chagas",
    "Milton Vieira Filho", "Rafael Pascucci", "Marcelo Garcia",
    "Renato Santiago", "Júnior da Farmácia", "Fabião Zagueiro",
    "Rogério da Acasem"
]

# Padrões de regex para capturar diferentes informações
padrao_projeto = (
    r'(Projeto de Decreto Legislativo|Proposta de Emenda à Lei Orgânica|'
    r'Projeto de Lei Complementar|Projeto de Resolução|Projeto de Lei) nº (\d+/\d{4})'
)
padrao_status = r"Resultado:\s*(Aprovada|Rejeitada)"
padrao_voto = r'(?P<vereador>' + '|'.join(lista_vereadores) + r'):\s*(?P<voto>Favorável|Contrário)'
padrao_autoria = r'Autoria:\s*Ver\.?\.?\s*([\w\s]+?)(?=\n|$)'
padrao_presidente = r'Presidente:\s*([\w\s]+)'

def extrair_votacoes(pdf_path):
    votacoes = []
    projetos_processados = set()  # Conjunto para rastrear projetos já processados

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()

            if texto:
                # Encontrar projetos de lei e seus status
                projetos = re.finditer(padrao_projeto, texto)
                status_matches = list(re.finditer(padrao_status, texto))

                # Encontrar votos dos vereadores
                votos = re.findall(padrao_voto, texto)

                # Encontrar presidente
                presidente = re.search(padrao_presidente, texto)

                # Estruturar dados
                for projeto in projetos:
                    tipo, numero = projeto.groups()
                    chave_projeto = f"{tipo} {numero}"
                    if chave_projeto not in projetos_processados:
                        projetos_processados.add(chave_projeto)

                        # Encontrar a autoria correspondente ao projeto
                        # Procurar a autoria logo após o projeto
                        match_autoria = re.search(padrao_autoria, texto[projeto.end():])
                        if match_autoria:
                            autoria = match_autoria.group(1).strip()
                            if autoria not in lista_vereadores:
                                # Tentar encontrar o nome do vereador mais próximo
                                for vereador in lista_vereadores:
                                    if vereador in texto[projeto.end():]:
                                        autoria = vereador
                                        break
                        else:
                            # Tentar encontrar o nome do vereador mais próximo
                            autoria = "Desconhecida"
                            for vereador in lista_vereadores:
                                if vereador in texto[projeto.end():]:
                                    autoria = vereador
                                    break

                        # Encontrar o status correspondente ao projeto
                        status = "Aprovada"  # Default status
                        for status_match in status_matches:
                            if projeto.end() < status_match.start():
                                status = status_match.group(1)
                                break

                        votacao = {
                            "tipo": tipo,
                            "projeto_de_lei": numero,
                            "presidente": presidente.group(1) if presidente else "Sem presidente",
                            "autoria": autoria,
                            "status": status,
                            "vereadores": [{"vereador": vereador, "voto": voto} for vereador, voto in votos]                                                  
                        }
                        votacoes.append(votacao)

    return votacoes

def salvar_json(dados, json_path):
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    print(f"Arquivo JSON salvo em: {json_path}")

def processar_pdfs(pasta_pdfs, pasta_json):
    for arquivo in os.listdir(pasta_pdfs):
        if arquivo.endswith('.pdf'):
            caminho_pdf = os.path.join(pasta_pdfs, arquivo)
            nome_json = f"{os.path.splitext(arquivo)[0]}.json"
            caminho_json = os.path.join(pasta_json, nome_json)

            dados_pdf = extrair_votacoes(caminho_pdf)
            salvar_json(dados_pdf, caminho_json)

# Defina os caminhos para a pasta dos PDFs e a pasta onde os JSONs serão salvos
pasta_pdfs = "downloaded_pdfs"
pasta_json = "json"

# Processa todos os PDFs na pasta especificada
processar_pdfs(pasta_pdfs, pasta_json)


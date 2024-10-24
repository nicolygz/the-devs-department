import json
import requests
from datetime import datetime
import time

def criarRequisicao(url):
  response =  requests.get(url)
  if response.status_code == 200:
    return response

url = f'https://camarasempapel.camarasjc.sp.gov.br//api/publico/proposicao/?&qtd=100&dataInicio=2021-01-01&tipoId=348'
resposta = criarRequisicao(url).json()
paginacao = resposta['Paginacao']['quantidade']
print(f'Total de páginas: {paginacao}')
total = resposta['total']
listJson = []
for i in range(1, int(paginacao)):
  
    inicio = datetime.now()
    pagina = criarRequisicao(url + f'&pag={i}').json()
    fim = datetime.now()
    
    if pagina['total'] != 0:
        duracao = fim - inicio
        quant_per_pag = int(len(pagina['Data']))
        print(f'Loop {i}, duração: {duracao}')
        
        for proposicao in range(quant_per_pag):
            idProposicao = pagina['Data'][proposicao]['id']
            anoProposicao = pagina['Data'][proposicao]['ano']
            processoNum = pagina['Data'][proposicao]['processo']
            protocoloNum = pagina['Data'][proposicao]['protocolo']
            numeroProp = pagina['Data'][proposicao]['numero']
            tipoProposicao = pagina['Data'][proposicao]['tipo']
            assuntoProposicao = pagina['Data'][proposicao]['assunto']
            dataProposicao = pagina['Data'][proposicao]['data']
            situacaoProposicao = pagina['Data'][proposicao]['situacao']
            autorProposicao = pagina['Data'][proposicao]['AutorRequerenteDados']['nomeRazao']
            idAutorProp = pagina['Data'][proposicao]['AutorRequerenteDados']['autorId']
            dicionario = {
            'ID': idProposicao,
            'NumeroProcesso': processoNum,
            'NumeroProtocolo': protocoloNum,
            'AnoProposicao': anoProposicao,
            'NumeroProposicao': numeroProp,
            'Tipo': tipoProposicao,
            'Assunto': assuntoProposicao,
            'Data': dataProposicao, # Transformar em tipo data
            'Autor': autorProposicao,
            'IdAutor': idAutorProp,
            'Situacao': situacaoProposicao
            }
            listJson.append(dicionario)
                
    elif pagina['total'] == 0:
       None
with open(f'ArquivosJson/DadosPL1.json', encoding='utf-8', mode='+a') as f:
    json.dump(listJson, f, indent=10, ensure_ascii=False)
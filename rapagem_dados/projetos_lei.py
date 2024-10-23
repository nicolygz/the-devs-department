import json
import requests
from datetime import datetime
import time

def criarRequisicao(url):
  response =  requests.get(url)
  if response.status_code == 200:
    return response

url = f'https://camarasempapel.camarasjc.sp.gov.br//api/publico/proposicao/?&qtd=400&dataInicio=2021-01-01&tipoId=348'
resposta = criarRequisicao(url).json()
paginacao = resposta['Paginacao']['quantidade']
print(f'Total de páginas: {paginacao}')
total = resposta['total']
listJson = []
listvazia = []
for i in range(1, int(paginacao)):
  
    inicio = datetime.now()
    pagina = criarRequisicao(url + f'&pag={i}').json()
    fim = datetime.now()
    if pagina['total'] != 0:
        duracao = fim - inicio
        quantPag = int(len(pagina['Data']))
        print(f'Loop {i}, duração: {duracao}')
        
        if i != 0:
            for x in range(quantPag):
                idProposicao = pagina['Data'][x]['id']
                processoNum = pagina['Data'][x]['processo']
                protocoloNum = pagina['Data'][x]['protocolo']
                numeroProp = pagina['Data'][x]['numero']
                tipoProposicao = pagina['Data'][x]['tipo']
                assuntoProposicao = pagina['Data'][x]['assunto']
                dataProposicao = pagina['Data'][x]['data']
                situacaoProposicao = pagina['Data'][x]['situacao']
                autorProposicao = pagina['Data'][x]['AutorRequerenteDados']['nomeRazao']
                idAutorProp = pagina['Data'][x]['AutorRequerenteDados']['autorId']
                dicionario = {
                'ID': str(idProposicao),
                'Numero Processo': str(processoNum),
                'Numero Protocolo': str(protocoloNum),
                'Numero Proposicao': str(numeroProp),
                'Tipo': str(tipoProposicao),
                'Assunto': str(assuntoProposicao),
                'Data': str(dataProposicao), # Transformar em tipo data
                'Autor': str(autorProposicao),
                'Id Autor': str(idAutorProp),
                'Situacao': str(situacaoProposicao)
                }
                listJson.append(dicionario)
        with open(f'rapagem_dados/ArquivosJson/DadosPL.json', encoding='utf-8', mode='+a') as f:
            json.dump(listJson, f, indent=10, ensure_ascii=False)
    elif pagina['total'] == 0:
       None


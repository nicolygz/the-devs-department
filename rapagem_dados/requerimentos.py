import json
import requests
from datetime import datetime
import time

def criarRequisicao(url):
  response =  requests.get(url)
  if response.status_code == 200:
    return response
url = f'https://camarasempapel.camarasjc.sp.gov.br//api/publico/proposicao/?&qtd=500&dataInicio=2021-01-01&tipoId=340'
resposta = criarRequisicao(url).json()
paginacao = resposta['Paginacao']['quantidade']
print(f'Total de páginas: {paginacao}')
total = resposta['total']
listJson = []
for i in range(1, int(paginacao)):
  try:
    inicio = datetime.now()
    pagina = criarRequisicao(url + f'&pag={i}').json()
    fim = datetime.now()
    duracao = fim - inicio
    quant_per_pag = int(len(pagina['Data']))
    print(f'Loop {i}, duração: {duracao}')
    if i != 0:
      for proposicao in range(quant_per_pag):
        idProposicao = pagina['Data'][proposicao]['id']
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
  except:
    response = requests.get(None)
with open(f'rapagem_dados\ArquivosJson\DadosRequerimentos.json', encoding='utf-8', mode='+a') as f:
  json.dump(listJson, f, indent=10, ensure_ascii=False)
    
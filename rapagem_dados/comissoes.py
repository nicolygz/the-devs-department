import requests
import json
from bs4 import BeautifulSoup
 
 
url="https://camarasempapel.camarasjc.sp.gov.br//api/publico/comissoes/"
 
def procurar (url):
    response = requests.get(url)
    if response.status_code ==200:
        return response
 
resposta = procurar(url).json()
comissoes = resposta ["comissoes"]
qtd = len(comissoes)
i = 0
verlista=[]
while i != int (qtd):
  diclista=[]
  nome_comissao = comissoes [i]["comissaoNome"]
  comissao_id = comissoes [i]["comissaoID"]
  id = len(comissoes[i]["comissaoParlamentar"])
  url = f"https://camarasempapel.camarasjc.sp.gov.br/spl/comissao.aspx?id=(comissao_id)"
  pag = procurar(url)
  html_content = pag.text
  date = BeautifulSoup(html_content).find(id="ContentPlaceHolder1_legislatura_data").get_text(strip=True)
  DataInicial = date.split(" ")[0]
  DataFinal = date.split(" ")[-1]
  x = 0
  while x != int(id):
      parlamentarID = comissoes[i]["comissaoParlamentar"][x]["parlamentarID"]
      parlamentarNome = comissoes[i]["comissaoParlamentar"][x]["parlamentarRazaoSocial"]
      cargo = comissoes[i]["comissaoParlamentar"][x]["comissaoCargo"]
      dic={
        "parlamentarID":parlamentarID,
        "parlamentarNome":parlamentarNome,
        "cargo":cargo
      }
      diclista.append(dic)
      x+=1
  dicionario={
      "Nome comissao": nome_comissao,
      "ID comissao": comissao_id,
      "Data inicio": DataInicial,
      "Data final": DataFinal,
      "Link": url,
      "Outras infos": diclista
  }
  verlista.append(dicionario)
  i +=1
with open("rapagem_dados/ArquivosJson/comissoes.json",encoding="utf-8",mode="+a")as f:
    json.dump(verlista,f,indent=5,ensure_ascii=False)
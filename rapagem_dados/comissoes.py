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
vararlista=[]
while i != int (qtd):
    diclista=[]
    nome_comissao = comissoes [i]["comissaoNome"]
    comissao_id = comissoes [i]["comissaoID"]
    print(vararlista)
    id= len(comissoes[i]["comissaoParlamentar"])
    url = f"https://camarasempapel.camarasjc.sp.gov.br/spl/comissao.aspx?id=(comissao_id)"
    pag = procurar(url)
    txt = pag.text
    date = BeautifulSoup(txt).find(id="ContentPlaceHolder1_legislatura_data").get_text(strip=True)
    inicial = date.split(" ") [0]
    final = date.split(" ")[-1]
    x = 0
    while x != int(id):
        parlamentarID=comissoes [i]["comissaoParlamentar"][x]["parlamentarID"]
        parlamentarNome=comissoes[i]["comissaoParlamentar"][x]["parlamentarRazaoSocial"]
        cargo=comissoes[i]["comissaoParlamentar"][x]["comissaoCargo"]
       
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
        "Data inicio": inicial,
        "Data final": final,
        "Link": url,
        "Outras infos": diclista
                }
    vararlista.append(dicionario)
    
    i +=1
  
with open("rapagem_dados/ArquivosJson/comissoes.json",encoding="utf-8",mode="+a")as f:
    json.dump(vararlista,f,indent=5,ensure_ascii=False)





# import requests
# import json
# from bs4 import BeautifulSoup
 
 
# url="https://camarasempapel.camarasjc.sp.gov.br//api/publico/comissoes/"
 
# def procurar (url):
#     response = requests.get(url)
#     if response.status_code ==200:
#         return response
# comissoesLista = []
# resposta = procurar(url).json()
# comissoes = resposta ["comissoes"]
# qtd = len(comissoes)
# i = 0
# while i != int(qtd):
#   listaParlamentar = []
#   nome_comissao = comissoes [i]["comissaoNome"]
#   comissao_id = comissoes [i]["comissaoID"]
#   id= len(comissoes[i]["comissaoParlamentar"])
#   url = f'https://camarasempapel.camarasjc.sp.gov.br/spl/comissao.aspx?id={comissao_id}'
#   pagina = procurar(url)
#   html_content = pagina.text
#   data = BeautifulSoup(html_content).find(id='ContentPlaceHolder1_legislatura_data').get_text(strip=True)
#   dataInicial = data.split(' ')[0]
#   dataFinal = data.split(' ')[-1]
#   x = 0
#   while x != int(id):
#     parlamentarID = comissoes[i]["comissaoParlamentar"][x]['parlamentarID']
#     parlamentarNome = comissoes[i]["comissaoParlamentar"][x]['parlamentarRazaoSocial']
#     parlamentarCargo = comissoes[i]["comissaoParlamentar"][x]['comissaoCargo']
#     parlamentares = {
#       'Id Parlamentar': parlamentarID,
#       'Nome Parlamentar': parlamentarNome,
#       'Cargo Parlamentar': parlamentarCargo
#     }
#     listaParlamentar.append(parlamentares)
#     x += 1
#   comissoesDic = {
#     "Nome comissao": nome_comissao,
#     "ID comissao": comissao_id,
#     "Data inicio": dataInicial,
#     "Data final": dataFinal,
#     "Link": url,
#     "Outras infos": listaParlamentar
#   }
#   comissoesLista.append(comissoesDic)
#   i += 1
# with open('RaspagemDados/Arquivos2/DadosComissao.json', encoding='utf-8', mode='+a') as file:
#   json.dump(comissoesLista, file, indent=10, ensure_ascii=False )
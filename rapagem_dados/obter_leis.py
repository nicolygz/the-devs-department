from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
import os

# Configurar o WebDriver (aqui estou usando o Chrome)
driver = webdriver.Chrome()

# URL da página
url = 'https://camarasempapel.camarasjc.sp.gov.br/legislacao/consulta-legislacao.aspx?tipo=22&situacao=3&interno=0&inicio=01%2f01%2f2021'

# Abrir a página no navegador
driver.get(url)

# Esperar a página carregar (ajuste se necessário)
time.sleep(5)

# Alterar a quantidade de itens exibidos para 100
select_element = driver.find_element(By.ID, 'ContentPlaceHolder1_ddl_ItensExibidos')
select = Select(select_element)
select.select_by_value('100')

# Esperar a página recarregar com 100 itens (ajuste conforme necessário)
time.sleep(5)

# Muda o diretório de trabalho para 'rapagem_dados'
os.chdir("the-devs-department/rapagem_dados/output")

# Agora salve o arquivo
file_path = "links_para_leis.txt"

with open(file_path, 'a', encoding='utf-8') as file:

    # Agora navegue pelas páginas
    for page in range(1, 6):  # Exemplo: primeiras 5 páginas
        print(f"Capturando dados da página {page}...")
        
        # Extrair o conteúdo da página (ajuste o seletor conforme a estrutura do HTML)
        # content = driver.page_source

        # Extrair os links dos elementos <a> com a classe kt-widget5__title
        links = driver.find_elements(By.CSS_SELECTOR, "a.kt-widget5__title")
        
        # Salvar os hrefs no arquivo
        for link in links:
            href = link.get_attribute('href')
            file.write(href + '\n')  # Salvar o href no arquivo
        
        # Salvar o conteúdo em um arquivo
        # with open(file_path, 'a', encoding='utf-8') as file:
        #    file.write(content)
        
        # Clicar no botão para ir para a próxima página, se não for a última
        if page < 5:
            next_button = driver.find_element(By.LINK_TEXT, str(page + 1))
            next_button.click()
            
            # Esperar a nova página carregar
            time.sleep(5)

# Fechar o navegador
driver.quit()

print("Finalizado!")
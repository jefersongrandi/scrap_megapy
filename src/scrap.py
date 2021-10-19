import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def getResultMegasenaScrapping():

    #1. Pegar conteúdo HTML a partir da URL
    url = 'http://www.loterias.caixa.gov.br/wps/portal/loterias/landing/megasena'

    #aponta para o driver correto (se não tiver na maquina é preciso fazer download)
    #geck = '/usr/local/bin/geckodriver'
    geck = '/home/user/geckodriver'

    service = Service(executable_path=geck)
    option = Options()
    option.headless = True
    driver = webdriver.Firefox(service=service, options=option) #option=option
    driver.implicitly_wait(10)
    driver.get(url)

    try:
        element_present = EC.presence_of_element_located((By.ID, 'ulDezenas'))
        WebDriverWait(driver, 10).until(element_present)

        elConcurso = driver.find_element(By.ID, 'conteudoresultado')
        #elConcurso = WebDriverWait(driver, 10).until(lambda d: d.find_element(By.ID, 'conteudoresultado'))

        elNumberRes = elConcurso.find_element(By.ID, 'ulDezenas')
        htmlNumberRes = elNumberRes.get_attribute('outerHTML')

        conc = elConcurso.find_element(By.TAG_NAME, 'h2').find_element(By.TAG_NAME, 'span')
        #print(elNumberRes)

        regData = r'(\d{2}/\d{2}/\d{4})+'  #desta forma captura a data correta
        regNrConc = r'([0-9]{4,6}) '
        DataConc = re.search(regData, conc.text)
        #print(DataConc)
        if (DataConc != None): 
            DataConc = DataConc.group(0)
        else:
            DataConc = ''

        NumConc = re.search(regNrConc, conc.text)
        if (NumConc != None): 
            NumConc = int(NumConc.group(0))
        else:
            NumConc = ''

        #2. Parsear o conteúdo HTML
        data = BeautifulSoup(htmlNumberRes, 'html.parser')
        ul = data.find('ul') 

        sorteados = []
        for li in ul.find_all("li"):
            sorteados.append(int(li.text))

        driver.quit()

        return {'sorteio': NumConc, 'data': DataConc, 'numeros': sorteados}

    except TimeoutException:
        return {'sorteio': '', 'data': '', 'numeros': [], 'excepction': 'Timeout load page Firefox'}


if __name__ == '__main__':
    teste = getResultMegasenaScrapping()
    print(teste)
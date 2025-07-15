# diagnostico.py

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

PAGE_URL = "https://lagarto.se.gov.br/portaltransparencia/?servico=cidadao/servidor"

def fazer_diagnostico():
    print("--- Script de Diagnóstico ---")
    
    print("\nIniciando o navegador Chrome...")
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("Navegando até o portal...")
        driver.get(PAGE_URL)

        print("\n" + "="*50)
        print(">>> AÇÃO MANUAL NECESSÁRIA <<<")
        print("="*50)
        print("1. Na janela do Chrome, selecione o MÊS e o ANO.")
        print("2. Clique no botão 'Pesquisar'.")
        print("3. Espere a primeira página de resultados carregar COMPLETAMENTE.")
        print("\nDepois que a tabela de resultados estiver VISÍVEL no navegador...")
        input(">>> VOLTE AQUI E PRESSIONE A TECLA 'ENTER' PARA CONTINUAR. <<<")
        print("="*50)
        
        print("\nOk, tirando uma 'fotografia' da página para análise...")
        
        # Tenta entrar no iframe
        try:
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
            driver.switch_to.frame(iframe)
            print("Entrou no iframe com sucesso.")
        except Exception as e:
            print(f"Não foi possível entrar no iframe. Erro: {e}")

        # Salva o screenshot e o código HTML
        time.sleep(2) # Garante que tudo renderizou
        driver.save_screenshot("debug_screenshot.png")
        
        with open("debug_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
            
        print("\n----------------------------------------------------")
        print("✅ DIAGNÓSTICO CONCLUÍDO!")
        print("Dois arquivos foram criados na sua pasta:")
        print("1. debug_screenshot.png (uma foto da tela)")
        print("2. debug_page_source.html (o código da página)")
        print("----------------------------------------------------")
        print("\nPor favor, me envie estes dois arquivos.")


    finally:
        print("Fechando o navegador...")
        driver.quit()

if __name__ == "__main__":
    fazer_diagnostico()
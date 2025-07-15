# coletor_final.py

import time
import os
from datetime import datetime
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

PAGE_URL = "https://lagarto.se.gov.br/portaltransparencia/?servico=cidadao/servidor"
DESTINATION_FOLDER = "dados_gastos"

def baixar_dados_pessoal():
    print("--- Coletor de Dados Híbrido (Humano + Robô) ---")
    
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
        print("A janela do Chrome foi aberta no portal.")
        print("1. Por favor, selecione o MÊS e o ANO que você deseja baixar.")
        print("2. Clique no botão 'Pesquisar' na página.")
        print("3. Espere a primeira página de resultados carregar.")
        print("\nDepois que a tabela de resultados aparecer no navegador...")
        input(">>> VOLTE AQUI E PRESSIONE A TECLA 'ENTER' PARA O ROBÔ CONTINUAR. <<<")
        print("="*50)
        
        print("\nOk, robô assumindo o controle para coletar os dados...")
        
        # Re-sincroniza com o iframe DEPOIS da ação humana
        WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))
        
        # Espera pela presença da tabela ou dos controles de página
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "resultado_table_wrapper")))
        
        all_dataframes = []
        page_num = 1

        while True:
            print(f"Lendo dados da Página {page_num}...")
            time.sleep(1)
            html_da_pagina = driver.page_source
            
            try:
                tabelas = pd.read_html(html_da_pagina, attrs={'id': 'resultado_table'})
                if tabelas:
                    all_dataframes.append(tabelas[0])
            except ValueError:
                print(f"  - Nenhum dado tabular encontrado na página {page_num}.")
                break

            try:
                next_button_li = driver.find_element(By.ID, "resultado_table_next")
                if "disabled" in next_button_li.get_attribute("class"):
                    print("Chegou na última página.")
                    break 
                
                driver.execute_script("arguments[0].click();", next_button_li.find_element(By.TAG_NAME, "a"))
                page_num += 1
                
                # Espera inteligente para a próxima página
                WebDriverWait(driver, 20).until(
                    EC.text_to_be_present_in_element((By.ID, "resultado_table_info"), f"Mostrando de {((page_num-1)*25)+1}")
                )
            except Exception:
                print("Finalizando a coleta (botão 'Próxima' não encontrado ou desabilitado).")
                break
        
        if not all_dataframes:
            print("Nenhuma tabela de dados foi coletada.")
            driver.quit()
            return
            
        print("\nCombinando dados de todas as páginas...")
        df_completo = pd.concat(all_dataframes, ignore_index=True)
        df_completo = df_completo.loc[:, ~df_completo.columns.str.contains('^Unnamed')]
        print(f"Sucesso! Um total de {len(df_completo)} registros foram coletados.")

        mes = int(input("\nPara salvar o arquivo, por favor, confirme o MÊS que você baixou (ex: 1): "))
        ano = int(input("Confirme o ANO que você baixou (ex: 2024): "))

        print("Formatando dados para o padrão do painel...")
        mapa_colunas = {'Nome': 'Nome', 'Cargo': 'Cargo', 'Líquido': 'Líquido'}
        df_limpo = df_completo[list(mapa_colunas.keys())].rename(columns=mapa_colunas)

        if not os.path.exists(DESTINATION_FOLDER):
            os.makedirs(DESTINATION_FOLDER)
        
        meses_pt = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
        nome_mes = meses_pt[mes - 1]
        
        output_filename = f"{nome_mes}_{ano}.xlsx"
        output_path = os.path.join(DESTINATION_FOLDER, output_filename)
        df_limpo.to_excel(output_path, index=False)
        
        print("\n----------------------------------------------------")
        print(f"✅ SUCESSO! O arquivo '{output_filename}' foi salvo em '{DESTINATION_FOLDER}/'")
        print("----------------------------------------------------")

    finally:
        print("Fechando o navegador...")
        driver.quit()

if __name__ == "__main__":
    baixar_dados_pessoal()
# coletor_dados.py (Versão Definitiva com a API Oficial de Dados Abertos)

import requests
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÕES FINAIS E CORRETAS ---
# Usando a URL base da API oficial de Dados Abertos que você encontrou.
# O [tipo-do-dado] para folha de pagamento é geralmente 'pessoal'.
API_BASE_URL = "https://lagarto.se.gov.br/api/pessoal"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Python Automated Scraper) - Buscando dados públicos para análise."
}

DESTINATION_FOLDER = "dados_gastos"

def baixar_dados_pessoal():
    """
    Função principal que pede o mês/ano, baixa os dados completos usando a API
    oficial de Dados Abertos e salva em um único arquivo Excel.
    """
    print("--- Coletor de Dados da Folha de Pagamento (API Oficial) ---")
    
    try:
        mes = int(input(f"Digite o MÊS (ex: 6 para Junho): "))
        ano = int(input(f"Digite o ANO (ex: 2024): "))
    except ValueError:
        print("\nERRO: Por favor, digite valores numéricos válidos.")
        return

    print(f"\nBuscando dados para {mes:02d}/{ano} usando a API oficial...")

    all_data = []
    page = 1
    
    while True:
        # Monta a URL para cada página, incluindo os parâmetros de mês e ano
        request_url = f"{API_BASE_URL}?mes={mes}&ano={ano}&page={page}"
        print(f"Buscando dados da página {page}...")
        
        try:
            response = requests.get(request_url, headers=HEADERS, timeout=30)
            response.raise_for_status() # Lança um erro para status 4xx ou 5xx
            data = response.json()
            
            # A maioria das APIs de dados abertos tem uma estrutura com uma chave principal
            # como 'data', 'results' ou 'registros'. Vamos procurar por 'data'.
            registros_da_pagina = data.get('data', [])
            
            if not registros_da_pagina:
                print("Chegou ao fim dos dados.")
                break
            
            all_data.extend(registros_da_pagina)
            page += 1
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404 and page > 1:
                # É comum a API retornar 404 quando não há mais páginas.
                print("Chegou ao fim dos dados (página não encontrada).")
                break
            else:
                print(f"\nERRO DE CONEXÃO: {e}")
                return
        except requests.exceptions.RequestException as e:
            print(f"\nERRO DE REDE: {e}")
            return
        except ValueError: # Erro se a resposta não for um JSON válido
            print(f"\nERRO: A resposta da API na página {page} não era um JSON válido. Pode não haver dados para o período.")
            break

    if not all_data:
        print(f"Nenhum registro encontrado para {mes:02d}/{ano}.")
        return

    print(f"\nSucesso! Um total de {len(all_data)} registros foram coletados.")
    df = pd.DataFrame(all_data)

    print("Formatando dados para o padrão do painel...")
    
    # Mapeamento das colunas da API para as do nosso dashboard.
    # É um palpite com base nos padrões, pode precisar de ajuste.
    mapa_colunas = {
        'Nome': 'nome',
        'Cargo': 'cargo',
        'Líquido': 'salario_liquido' # Supondo nomes comuns
    }
    
    # Verifica se as colunas esperadas existem
    colunas_reais = list(df.columns)
    colunas_api = [col for col in mapa_colunas.values() if col in colunas_reais]

    if len(colunas_api) != len(mapa_colunas):
        print("\nAVISO: Nem todas as colunas padrão foram encontradas.")
        print(f"As colunas disponíveis são: {colunas_reais}")
        print("Usando as colunas encontradas para gerar o arquivo...")
        # Atualiza o mapa para usar apenas as colunas que realmente existem
        mapa_colunas_existentes = {k: v for k, v in mapa_colunas.items() if v in colunas_reais}
        df_limpo = df[colunas_api].rename(columns={v: k for k, v in mapa_colunas_existentes.items()})
    else:
        df_limpo = df[list(mapa_colunas.values())].rename(columns={v: k for k, v in mapa_colunas.items()})

    # Garante que a pasta de destino exista
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

if __name__ == "__main__":
    baixar_dados_pessoal()
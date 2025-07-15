# juntador_arquivos.py

import pandas as pd
import os
import glob
from datetime import datetime

# Pasta onde o arquivo final será salvo, para uso do dashboard
DESTINATION_FOLDER = "dados_gastos"

def juntar_arquivos():
    print("--- Assistente Juntador de Planilhas da Folha de Pagamento ---")

    # 1. Pergunta ao usuário onde estão os arquivos baixados
    source_folder = input("\nPor favor, cole aqui o caminho completo da pasta onde você salvou os arquivos exportados do portal: \n> ")

    if not os.path.isdir(source_folder):
        print("\nERRO: O caminho informado não é uma pasta válida. Por favor, tente novamente.")
        return

    # Procura por todos os arquivos Excel ou CSV na pasta
    search_path_xlsx = os.path.join(source_folder, "*.xlsx")
    search_path_csv = os.path.join(source_folder, "*.csv")
    all_files = glob.glob(search_path_xlsx) + glob.glob(search_path_csv)

    if not all_files:
        print(f"\nERRO: Nenhum arquivo .xlsx ou .csv encontrado na pasta '{source_folder}'.")
        return

    print(f"\nEncontrados {len(all_files)} arquivos para processar. Iniciando a combinação...")

    # 2. Lê cada arquivo e junta todos em uma única lista
    lista_de_dataframes = []
    for f in all_files:
        try:
            print(f"Lendo arquivo: {os.path.basename(f)}...")
            if f.endswith('.csv'):
                # Tenta ler como CSV com diferentes separadores comuns
                try:
                    df = pd.read_csv(f, sep=';')
                except Exception:
                    df = pd.read_csv(f, sep=',')
            else:
                # Lê como Excel
                df = pd.read_excel(f)
            
            lista_de_dataframes.append(df)
        except Exception as e:
            print(f"  AVISO: Não foi possível ler o arquivo {os.path.basename(f)}. Erro: {e}. Pulando...")

    if not lista_de_dataframes:
        print("\nERRO: Nenhum arquivo pôde ser lido com sucesso.")
        return

    # 3. Combina todos os dataframes da lista em um só
    df_completo = pd.concat(lista_de_dataframes, ignore_index=True)
    print(f"\nCombinação concluída. Total de {len(df_completo)} registros juntados.")

    # 4. Limpeza e formatação final
    print("Formatando os dados para o padrão do painel...")
    
    # Remove colunas "Unnamed" que às vezes são criadas
    df_completo = df_completo.loc[:, ~df_completo.columns.str.contains('^Unnamed')]
    
    # Renomeia as colunas para o padrão que o dashboard precisa
    # O script é inteligente e só renomeia as colunas que encontrar
    mapa_colunas = {'Nome': 'Nome', 'Cargo': 'Cargo', 'Líquido': 'Líquido'}
    colunas_para_renomear = {col_antigo: col_novo for col_novo, col_antigo in mapa_colunas.items() if col_antigo in df_completo.columns}
    
    if colunas_para_renomear:
        df_completo.rename(columns=colunas_para_renomear, inplace=True)
        print(f"Colunas renomeadas para o padrão: {list(colunas_para_renomear.values())}")
    else:
        print("AVISO: Nenhuma coluna com os nomes 'Nome', 'Cargo' ou 'Líquido' foi encontrada para renomear.")


    # 5. Pede o mês/ano para nomear o arquivo de saída corretamente
    try:
        mes = int(input("\nDigite o MÊS de referência destes dados (ex: 1 para Janeiro): "))
        ano = int(input("Digite o ANO de referência (ex: 2024): "))
    except ValueError:
        print("ERRO: Mês e ano inválidos.")
        return

    # 6. Salva o arquivo final na pasta de destino
    if not os.path.exists(DESTINATION_FOLDER):
        os.makedirs(DESTINATION_FOLDER)

    meses_pt = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    nome_mes = meses_pt[mes - 1]
    
    output_filename = f"{nome_mes}_{ano}.xlsx"
    output_path = os.path.join(DESTINATION_FOLDER, output_filename)
    
    df_completo.to_excel(output_path, index=False)

    print("\n----------------------------------------------------")
    print(f"✅ SUCESSO! O arquivo final '{output_filename}' foi salvo em '{DESTINATION_FOLDER}/'")
    print("----------------------------------------------------")


if __name__ == "__main__":
    juntar_arquivos()
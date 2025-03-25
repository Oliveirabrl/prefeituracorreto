import streamlit as st
import pandas as pd
import os

# Configurações do dashboard
st.set_page_config(layout="wide")
st.title("Gastos da Prefeitura")
st.text("Painel de gastos da Prefeitura de Lagarto/Sergipe")

# Mensagem inicial para depuração
st.write("Iniciando o carregamento do dashboard...")

# Verifica se o arquivo 2025.xlsx existe
file_path = "2025.xlsx"
st.write(f"Verificando se o arquivo '{file_path}' existe no servidor...")
if os.path.exists(file_path):
    st.write("Arquivo encontrado com sucesso!")
    
    # Tenta carregar os dados do Excel
    try:
        st.write("Carregando os dados do arquivo 2025.xlsx, aba 'aaa'...")
        dados = pd.read_excel(file_path, sheet_name="aaa")
        st.write("Dados carregados com sucesso!")
        
        # Renomeia as colunas
        dados = dados.rename(columns={"Empenhado": "Projetado"})
        dados = dados.rename(columns={"Credor": "Quem Recebeu"})
        
        # Injetar CSS personalizado para mudar a cor do texto e centralizar a imagem
        st.markdown(
            """
            <style>
            /* Estiliza o texto digitado no campo de entrada */
            input[type="text"] {
                color: #FF0000 !important; /* Cor vermelha, pode mudar para outra */
            }
            /* Centraliza a imagem */
            .centered-image {
                display: block;
                margin-left: auto;
                margin-right: auto;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Rótulo e campo de entrada para o filtro
        st.markdown("<p style='font-size: 16px; margin-bottom: -10px;'>QUEM RECEBEU ?? ----- Digite o nome para filtrar: ---------- DICAS; pode ser; Nome, Sobrenome ou CNPJ</p>", unsafe_allow_html=True)
        nome_filtro = st.text_input("", placeholder="Digite aqui...")

        # Filtrar os dados
        if nome_filtro:
            dados_filtrados = dados[dados['Quem Recebeu'].str.contains(nome_filtro, case=False, na=False)]
            # Exibir a imagem e o áudio com autoplay
            try:
                # Imagem centralizada
                st.markdown(
                    '<img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRqQMqqLTMPHLa5ADtDcfz7XYhwYWI92SYifQ&s" class="centered-image" width="300">',
                    unsafe_allow_html=True
                )
               
                # Áudio com autoplay
                st.markdown(
                    '<audio src="https://www.myinstants.com/media/sounds/joker-laugh.mp3" autoplay>',
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.error(f"Erro ao carregar a imagem ou áudio: {e}")
        else:
            dados_filtrados = dados

        # Exibir os dados filtrados
        st.divider()
        st.subheader("Lista")
        st.dataframe(dados_filtrados)
        
    except Exception as e:
        st.error(f"Erro ao carregar os dados do arquivo Excel: {str(e)}")
        st.write("Possíveis causas:")
        st.write("- A aba 'aaa' não existe no arquivo. Verifique o nome exato da aba.")
        st.write("- O arquivo está corrompido ou não é um Excel válido.")
else:
    st.error(f"Erro: O arquivo '{file_path}' não foi encontrado no servidor!")
    st.write("Certifique-se de que o arquivo '2025.xlsx' foi enviado ao repositório no GitHub.")

# Mensagem final para depuração
st.write("Fim do carregamento do dashboard.")
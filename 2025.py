import streamlit as st
import pandas as pd

# Configurações do dashboard
st.set_page_config(layout="wide")
st.title("Gastos da Prefeitura")
st.text("Painel de gastos da Prefeitura de Lagarto/Sergipe")

# URL do CSV gerado pelo Google Sheets
csv_url = "https://docs.google.com/spreadsheets/d/1laPuYWWQD3BJRWI_bpwpGg115Ie7mLrqv_jtH7dPgLk/export?format=csv&gid=741206008"

# Tenta carregar os dados do Google Sheets
try:
    dados = pd.read_csv(csv_url)
    
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
         
            )
           
            # Áudio com autoplay (tema de Missão Impossível)
            st.markdown(
                '<audio src="https://www.myinstants.com/media/sounds/mission-impossible-theme.mp3" autoplay>',
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
    st.error(f"Erro ao carregar os dados do Google Sheets: {str(e)}")
    st.write("Possíveis causas:")
    st.write("- O link CSV está incorreto ou a planilha não está pública.")
    st.write("- A aba ou os dados não estão acessíveis.")
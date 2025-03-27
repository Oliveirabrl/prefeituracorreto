import streamlit as st
import pandas as pd

# Configurações do dashboard
st.set_page_config(layout="wide")
st.title("Gastos da Prefeitura")
st.text("Painel de gastos da Prefeitura de Lagarto/Sergipe")

# Aviso sobre a origem dos dados
st.markdown(
    """
    **Aviso:** Este dashboard utiliza dados públicos disponíveis no site oficial da Prefeitura de Lagarto/Sergipe. 
    O objetivo é promover a transparência e facilitar o acesso às informações sobre os gastos públicos.
    """
)

# URL do CSV gerado pelo Google Sheets
csv_url = "https://docs.google.com/spreadsheets/d/1laPuYWWQD3BJRWI_bpwpGg115Ie7mLrqv_jtH7dPgLk/export?format=csv&gid=741206008"

# Tenta carregar os dados do Google Sheets
try:
    dados = pd.read_csv(csv_url)
    
    # Renomeia as colunas
    dados = dados.rename(columns={"Empenhado": "Projetado"})
    dados = dados.rename(columns={"Credor": "Quem Recebeu"})
    
    # Injetar CSS personalizado para mudar a cor do texto
    st.markdown(
        """
        <style>
        /* Estiliza o texto digitado no campo de entrada */
        input[type="text"] {
            color: #FF0000 !important; /* Cor vermelha, pode mudar para outra */
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
        # Exibir o áudio com autoplay (usando arquivo local)
        try:
            # Áudio com autoplay
            st.markdown(
                '<audio src="suspense_audio.mp3" autoplay>',
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"Erro ao carregar o áudio: {e}")
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
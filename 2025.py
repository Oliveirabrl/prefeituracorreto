import streamlit as st
import pandas as pd
import plotly.express as px

# Configurações iniciais do dashboard
st.set_page_config(layout="wide")
st.title("📊 Gastos da Prefeitura - Desde 01/01/2025")
st.text("Gastos da Prefeitura de Lagarto/Sergipe, atualizados mensalmente")

# Seção 1: Sobre os Dados
with st.expander("ℹ️ Sobre os Dados"):
    st.markdown(
        """
        **Aviso:** Este dashboard utiliza dados públicos disponíveis no site oficial da Prefeitura de Lagarto/Sergipe. 
        O objetivo é promover a transparência e facilitar o acesso às informações sobre os gastos públicos (Lei de Acesso à Informação - Lei nº 12.527/2011).
        """
    )

# Função para carregar os dados com cache
@st.cache_data
def load_data(url):
    return pd.read_csv(url)

# URLs do Google Sheets
csv_gastos_url = "https://docs.google.com/spreadsheets/d/1laPuYWWQD3BJRWI_bpwpGg115Ie7mLrqv_jtH7dPgLk/export?format=csv&gid=741206008"
csv_viagens_url = "https://docs.google.com/spreadsheets/d/1laPuYWWQD3BJRWI_bpwpGg115Ie7mLrqv_jtH7dPgLk/export?format=csv&gid=839069942"

# Carregar e processar os dados
try:
    with st.spinner("Carregando dados..."):
        # Carregar e processar os dados de gastos
        dados = load_data(csv_gastos_url)
        dados = dados.rename(columns={"Empenhado": "Projetado", "Credor": "Quem Recebeu"})
        
        # Limpeza da coluna 'Projetado'
        dados['Projetado'] = dados['Projetado'].astype(str)
        dados['Projetado'] = dados['Projetado'].str.replace(r'R\$', '', regex=True).str.strip()
        dados['Projetado'] = dados['Projetado'].str.replace(r'\.', '', regex=True)
        dados['Projetado'] = dados['Projetado'].str.replace(',', '.', regex=False)
        dados['Projetado'] = pd.to_numeric(dados['Projetado'], errors='coerce')

        # Carregar e processar os dados de viagens
        dados_viagens = load_data(csv_viagens_url)
        
        # Verificar se as colunas esperadas existem
        colunas_esperadas = ['Favorecido', 'Saída', 'Chegada', 'Destino', 'Valor']
        if not all(col in dados_viagens.columns for col in colunas_esperadas):
            raise ValueError("Uma ou mais colunas esperadas ('Favorecido', 'Saída', 'Chegada', 'Destino', 'Valor') não foram encontradas na aba 'Viagens'.")

        # Converter colunas de data com formato explícito DD/MM/YYYY
        dados_viagens['Saída'] = pd.to_datetime(dados_viagens['Saída'], format='%d/%m/%Y', errors='coerce')
        dados_viagens['Chegada'] = pd.to_datetime(dados_viagens['Chegada'], format='%d/%m/%Y', errors='coerce')

        # Filtrar linhas com datas válidas
        dados_viagens = dados_viagens.dropna(subset=['Saída', 'Chegada'])

        # Calcular duração (incluindo dia inicial)
        dados_viagens['Duração'] = ((dados_viagens['Chegada'] - dados_viagens['Saída']).dt.days + 1).astype(int)

        # Filtrar durações inválidas ou improváveis
        dados_viagens = dados_viagens[(dados_viagens['Duração'] > 0) & (dados_viagens['Duração'] <= 30)]

        # Criar colunas formatadas para datas no formato D/M/AA (ex.: 2/5/25)
        dados_viagens['Saída_Formatada'] = dados_viagens['Saída'].dt.strftime('%d/%m/%y').str.replace(r'^0', '', regex=True).str.replace('/0', '/')
        dados_viagens['Chegada_Formatada'] = dados_viagens['Chegada'].dt.strftime('%d/%m/%y').str.replace(r'^0', '', regex=True).str.replace('/0', '/')

        # Limpeza da coluna 'Valor'
        dados_viagens['Valor'] = dados_viagens['Valor'].astype(str)
        dados_viagens['Valor'] = dados_viagens['Valor'].str.replace(r'R\$', '', regex=True).str.strip()
        dados_viagens['Valor'] = dados_viagens['Valor'].str.replace(r'\.', '', regex=True)
        dados_viagens['Valor'] = dados_viagens['Valor'].str.replace(',', '.', regex=False)
        dados_viagens['Valor'] = pd.to_numeric(dados_viagens['Valor'], errors='coerce')

    # Seção: Lista de Gastos
    st.subheader("Lista de Gastos")
    st.markdown("**Filtro**")
    nome_filtro = st.text_input("Quem Recebeu", placeholder="Digite nome, sobrenome ou CNPJ...")

    # Filtrar os dados
    dados_filtrados = dados
    filtro_aplicado = False
    if nome_filtro:
        dados_filtrados = dados_filtrados[dados_filtrados['Quem Recebeu'].str.contains(nome_filtro, case=False, na=False)]
        filtro_aplicado = True

    if not filtro_aplicado:
        st.write("Aplique um filtro para visualizar os dados.")
    else:
        st.dataframe(
            dados_filtrados.style.highlight_max(subset=['Projetado'], color='yellow').format({'Projetado': 'R$ {:,.2f}'}),
            use_container_width=True
        )

        # Gráfico dinâmico (filtrado)
        st.subheader("Distribuição dos Gastos (Filtrados)")
        fig = px.bar(dados_filtrados.head(10), x='Quem Recebeu', y='Projetado', title="Top 10 Gastos Filtrados")
        st.plotly_chart(fig)

        # Botão para exportar
        csv = dados_filtrados.to_csv(index=False)
        st.download_button("Baixar dados filtrados", csv, "gastos_filtrados.csv", "text/csv")

    # Seção: Gráfico de Viagens
    st.divider()
    st.subheader("Gráfico de Viagens dos Servidores Públicos")
    if dados_viagens['Duração'].isna().all() or dados_viagens['Valor'].isna().all():
        st.warning("Não foi possível calcular a duração ou os valores das viagens. Verifique os formatos das colunas 'Saída', 'Chegada' e 'Valor' na aba 'Viagens'.")
    else:
        # Filtrar linhas com dados válidos
        dados_viagens = dados_viagens.dropna(subset=['Saída', 'Chegada', 'Duração', 'Valor', 'Destino', 'Favorecido'])
        if dados_viagens.empty:
            st.warning("Nenhum dado válido encontrado para o gráfico de viagens.")
        else:
            fig_viagens = px.scatter(
                dados_viagens,
                x='Destino',
                y='Duração',
                size='Valor',
                color='Favorecido',
                hover_data=['Saída_Formatada', 'Chegada_Formatada'],
                title='Viagens dos Servidores Públicos',
                height=500
            )
            fig_viagens.update_layout(
                xaxis_title="Destino",
                yaxis_title="Duração (dias)",
                title_x=0.5,
                showlegend=True
            )
            st.plotly_chart(fig_viagens, use_container_width=True)

    # Seção: Gastos por Setor
    st.divider()
    st.subheader("Gastos por Setor")
    setores = {
        "Postos de Combustíveis": ["posto", "combustíveis", "gasolina"],
        "Farmácia": ["farmácia", "medicamentos", "pharma"],
        "Advogados Associados": ["advocacia", "associados", "jurídico"],
        "Construção": ["construção", "material", "obra"],
        "Educação": ["educação", "escola", "professor"],
        "Saúde": ["saúde", "hospital", "médico"],
        "Passagens Aéreas": ["passagem", "aérea", "viagem"]
    }
    cores_setores = {
        "Postos de Combustíveis": "#FFD700",
        "Farmácia": "#98FB98",
        "Advogados Associados": "#FFA07A",
        "Construção": "#87CEEB",
        "Educação": "#DDA0DD",
        "Saúde": "#F08080",
        "Passagens Aéreas": "#4682B4"
    }
    
    # Checkboxes para setores
    cols = st.columns(7)
    selecoes = {}
    for i, setor in enumerate(setores.keys()):
        with cols[i]:
            selecoes[setor] = st.checkbox(setor)

    # Exibir dados dos setores selecionados
    for setor, termos in setores.items():
        if selecoes[setor]:
            filtro = dados['Quem Recebeu'].str.lower().str.contains('|'.join(termos), na=False)
            dados_filtrados_setor = dados[filtro].groupby('Quem Recebeu', as_index=False)['Projetado'].sum()
            if not dados_filtrados_setor.empty:
                st.write(f"**{setor}**")
                st.dataframe(
                    dados_filtrados_setor[['Quem Recebeu', 'Projetado']].style.format({'Projetado': 'R$ {:,.2f}'}),
                    use_container_width=True,
                    hide_index=True
                )

    # Gráfico de Gastos por Setor
    st.divider()
    st.subheader("Gráfico de Gastos por Setor")
    gasto_por_setor = []
    for setor, termos in setores.items():
        filtro = dados['Quem Recebeu'].str.lower().str.contains('|'.join(termos), na=False)
        total_setor = dados[filtro]['Projetado'].sum()
        if total_setor > 0:
            gasto_por_setor.append({"Setor": setor, "Valor": total_setor})
    df_gasto_setor = pd.DataFrame(gasto_por_setor)
    fig = px.bar(
        df_gasto_setor, y="Setor", x="Valor", orientation='h', height=300,
        color="Setor", color_discrete_map=cores_setores
    )
    fig.update_layout(showlegend=False, xaxis_title="Valor (R$)", yaxis_title="", margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar os dados: {str(e)}")
    st.write("Possíveis causas:")
    st.write("- Formato inválido na coluna 'Projetado' ou 'Valor' (ex.: texto em vez de número).")
    st.write("- Formato inválido nas colunas 'Saída' ou 'Chegada' (ex.: datas fora do padrão DD/MM/YYYY).")
    st.write("- Verifique o link da planilha ou a conexão com a internet.")

# CSS personalizado
st.markdown(
    """
    <style>
    input[type="text"] { color: #FF0000 !important; }
    h2 { color: #1E90FF; font-family: 'Arial', sans-serif; margin-bottom: 20px; }
    .stCheckbox > label { color: #FFFFFF; font-weight: bold; }
    .dataframe { border: 1px solid #1E90FF; border-radius: 5px; }
    .stMarkdown, .stDataFrame { margin-bottom: 20px; }
    </style>
    """,
    unsafe_allow_html=True
)
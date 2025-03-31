# Importação das bibliotecas necessárias
import streamlit as st
import pandas as pd
import plotly.express as px

# Configurações iniciais do dashboard
st.set_page_config(layout="wide")
st.title("📊 Gastos da Prefeitura - Desde 01/01/2025")
st.text("Gastos da Prefeitura de Lagarto/Sergipe, atualizados mensalmente")

# Seção 1: Sobre os Dados (expander com informações sobre a origem dos dados)
with st.expander("ℹ️ Sobre os Dados"):
    st.markdown(
        """
        **Aviso:** Este dashboard utiliza dados públicos disponíveis no site oficial da Prefeitura de Lagarto/Sergipe. 
        O objetivo é promover a transparência e facilitar o acesso às informações sobre os gastos públicos.
        """
    )

# Função para carregar os dados com cache para melhorar a performance
@st.cache_data
def load_data(url):
    return pd.read_csv(url)

# URL do CSV com os dados
csv_url = "https://docs.google.com/spreadsheets/d/1laPuYWWQD3BJRWI_bpwpGg115Ie7mLrqv_jtH7dPgLk/export?format=csv&gid=741206008"

# Carregar e processar os dados
try:
    with st.spinner("Carregando dados..."):
        dados = load_data(csv_url)
        dados = dados.rename(columns={"Empenhado": "Projetado", "Credor": "Quem Recebeu"})
        
        # Limpeza robusta da coluna 'Projetado' para conversão em valores numéricos
        dados['Projetado'] = dados['Projetado'].astype(str)
        dados['Projetado'] = dados['Projetado'].str.replace(r'R\$', '', regex=True).str.strip()
        dados['Projetado'] = dados['Projetado'].str.replace(r'\.', '', regex=True)
        dados['Projetado'] = dados['Projetado'].str.replace(',', '.', regex=False)
        dados['Projetado'] = pd.to_numeric(dados['Projetado'], errors='coerce')

    # Seção 2: Resumo Estatístico
    st.subheader("Resumo Estatístico")
    total_gasto = dados['Projetado'].sum()
    maior_gasto = dados['Projetado'].max()
    maior_gasto_credor = dados.loc[dados['Projetado'].idxmax(), 'Quem Recebeu'] if not dados['Projetado'].isna().all() else "N/A"

    # Calcular gasto e número de registros por setor
    setores = {
        "Postos de Combustíveis": ["posto", "auto posto","Combustíveis"],
        "Farmácia": ["farmácia"],
        "Advogados Associados": ["advogados associados", "advogado", "advocacia"],
        "Construção": ["construção", "construtora", "empreendimentos"],
        "Educação": ["escola", "educacional", "educação"],
        "Saúde": ["hospital", "clínica", "saúde"],
        "Passagens Aéreas": ["passagens", "aéreas", "viagens", "turismo"]
    }
    gasto_por_setor = []
    registros_por_setor = {}
    for setor, termos in setores.items():
        filtro = dados['Quem Recebeu'].str.lower().str.contains('|'.join(termos), na=False)
        total_setor = dados[filtro]['Projetado'].sum()
        num_registros_setor = len(dados[filtro])
        gasto_por_setor.append({"Setor": setor, "Valor": total_setor})
        registros_por_setor[setor] = num_registros_setor

    # Identificar o setor com mais registros
    setor_mais_registros = max(registros_por_setor, key=registros_por_setor.get)
    num_registros_mais = registros_por_setor[setor_mais_registros]

    # Exibir resumo em colunas
    cols_resumo = st.columns(3)
    with cols_resumo[0]:
        st.metric("Total Gasto", f"R$ {total_gasto:,.2f}")
    with cols_resumo[1]:
        st.metric("Maior Gasto", f"R$ {maior_gasto:,.2f}", f"Por: {maior_gasto_credor}")
    with cols_resumo[2]:
        st.metric("Setor com Mais Registros", setor_mais_registros, f"{num_registros_mais} registros")

    # Seção 3: Filtro da Lista de Gastos
    st.subheader("Lista de Gastos")
    st.markdown("**Filtro**")
    nome_filtro = st.text_input("Quem Recebeu", placeholder="Digite nome, sobrenome ou CNPJ...")

    # Filtrar os dados (só exibe se houver filtro)
    dados_filtrados = dados
    filtro_aplicado = False
    if nome_filtro:
        dados_filtrados = dados_filtrados[dados_filtrados['Quem Recebeu'].str.contains(nome_filtro, case=False, na=False)]
        filtro_aplicado = True

    # Mensagem para aplicar filtro
    if not filtro_aplicado:
        st.write("Aplique um filtro para visualizar os dados.")

    # Seção 4: Tabela da Lista de Gastos (quando filtrado)
    if filtro_aplicado:
        st.dataframe(
            dados_filtrados.style.highlight_max(subset=['Projetado'], color='yellow').format({'Projetado': 'R$ {:,.2f}'.format}),
            use_container_width=True
        )

        # Gráfico dinâmico (filtrado, só exibe se houver filtro)
        st.subheader("Distribuição dos Gastos (Filtrados)")
        fig = px.bar(dados_filtrados.head(10), x='Quem Recebeu', y='Projetado', title="Top 10 Gastos Filtrados")
        st.plotly_chart(fig)

        # Botão para exportar (só exibe se houver filtro)
        csv = dados_filtrados.to_csv(index=False)
        st.download_button("Baixar dados filtrados", csv, "gastos_filtrados.csv", "text/csv")

    # Seção 5: Filtro de Gastos por Setor (checkboxes)
    st.divider()
    st.subheader("Gastos por Setor")
    cores_setores = {
        "Posto": "#FFD700",  # Amarelo
        "Farmácia": "#98FB98",  # Verde claro
        "Advogados Associados": "#FFA07A",  # Salmão
        "Construção": "#87CEEB",  # Azul claro
        "Educação": "#DDA0DD",  # Lilás
        "Saúde": "#F08080",  # Coral
        "Passagens Aéreas": "#4682B4"  # Azul aço
    }
    
    # Criar colunas para organizar os checkboxes horizontalmente
    cols = st.columns(7)
    selecoes = {}
    for i, setor in enumerate(setores.keys()):
        with cols[i]:
            selecoes[setor] = st.checkbox(setor)

    # Exibir dados dos setores selecionados (tabelas detalhadas)
    for setor, termos in setores.items():
        if selecoes[setor]:
            filtro = dados['Quem Recebeu'].str.lower().str.contains('|'.join(termos), na=False)
            dados_filtrados_setor = dados[filtro].groupby('Quem Recebeu', as_index=False)['Projetado'].sum()
            if not dados_filtrados_setor.empty:
                st.write(f"**{setor}**")
                # Aplicar cor de fundo à tabela
                st.markdown(
                    f"""
                    <style>
                    .dataframe-setor-{setor.replace(' ', '-')} {{
                        background-color: {cores_setores[setor]} !important;
                        border-radius: 5px;
                        padding: 10px;
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                st.dataframe(
                    dados_filtrados_setor[['Quem Recebeu', 'Projetado']].style.format({'Projetado': 'R$ {:,.2f}'.format}),
                    use_container_width=True,
                    hide_index=True,
                    column_config={"_index": None}
                )
            else:
                st.write(f"Nenhum dado encontrado para {setor}.")

    # Seção 6: Gráfico de Gastos por Setor
    st.divider()
    st.subheader("Gráfico de Gastos por Setor")
    df_gasto_setor = pd.DataFrame(gasto_por_setor)
    fig = px.bar(
        df_gasto_setor,
        y="Setor",
        x="Valor",
        orientation='h',
        height=300,
        color="Setor",
        color_discrete_map=cores_setores
    )
    fig.update_layout(
        showlegend=False,
        xaxis_title="Valor (R$)",
        yaxis_title="",
        margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar os dados: {str(e)}")
    st.write("Possíveis causas:")
    st.write("- Formato inválido na coluna 'Projetado' (ex.: texto em vez de número).")
    st.write("- Verifique o link da planilha ou a conexão com a internet.")

# CSS personalizado para estilização
st.markdown(
    """
    <style>
    /* Estilizar texto do campo de entrada */
    input[type="text"] {
        color: #FF0000 !important;
    }
    /* Estilizar os títulos */
    h2 {
        color: #1E90FF; /* Azul para os subtítulos */
        font-family: 'Arial', sans-serif;
        margin-bottom: 20px;
    }
    /* Estilizar os checkboxes */
    .stCheckbox > label {
        color: #FFFFFF; /* Texto branco para os checkboxes */
        font-weight: bold;
    }
    /* Estilizar as tabelas */
    .dataframe {
        border: 1px solid #1E90FF;
        border-radius: 5px;
    }
    /* Ajustar espaçamento entre elementos */
    .stMarkdown, .stDataFrame {
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
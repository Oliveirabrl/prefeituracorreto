# dashboard.py (Versão Final Definitiva, Completa e sem omissões)

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import glob
import re

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(layout="wide")
st.title("📈 Painel de Gastos da Prefeitura de Lagarto")
st.caption("Nota: Alguns dados, como os de pessoal, são atualizados semestralmente.")
st.caption("Fonte: Todos esses dados estão disponíveis no próprio site da Prefeitura.")

# ==============================================================================
# Funções de Processamento
# ==============================================================================

def clean_monetary_value(series):
    series = series.astype(str)
    series = series.str.replace(r'R\$', '', regex=True).str.strip()
    series = series.str.replace(r'\.', '', regex=True)
    series = series.str.replace(',', '.', regex=False)
    return pd.to_numeric(series, errors='coerce')

@st.cache_data(ttl="30m")
def load_and_process_spending_data(folder_path):
    all_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
    if not all_files: return pd.DataFrame()
    monthly_data = []
    month_map = {'janeiro': 1, 'fevereiro': 2, 'marco': 3, 'abril': 4, 'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12}
    for filepath in all_files:
        try:
            filename = os.path.basename(filepath)
            match = re.match(r'([a-z]+)_(\d{4})\.xlsx', filename.lower())
            if not match: continue
            df = pd.read_excel(filepath)
            df.columns = [str(col).strip() for col in df.columns]
            required_cols = ['Nome', 'Cargo', 'Líquido']
            if not all(col in df.columns for col in required_cols): continue
            df_processed = df[required_cols].copy()
            df_processed.rename(columns={'Nome': 'Credor', 'Líquido': 'Projetado'}, inplace=True)
            df_processed['Projetado'] = clean_monetary_value(df_processed['Projetado'])
            df_processed.dropna(subset=['Credor', 'Cargo', 'Projetado'], inplace=True)
            if df_processed.empty: continue
            month_name, year_str = match.groups()
            month, year = month_map.get(month_name), int(year_str)
            df_processed['Data'] = datetime(year, month, 1)
            monthly_data.append(df_processed)
        except Exception: continue
    if not monthly_data: return pd.DataFrame()
    return pd.concat(monthly_data, ignore_index=True)

@st.cache_data(ttl="30m")
def load_travel_data(file_path):
    if not os.path.exists(file_path): return pd.DataFrame()
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        expected_cols = ['Favorecido', 'Saída', 'Chegada', 'Destino', 'Valor']
        if not all(col in df.columns for col in expected_cols): return pd.DataFrame()
        df['Saída'] = pd.to_datetime(df['Saída'], errors='coerce')
        df['Chegada'] = pd.to_datetime(df['Chegada'], errors='coerce')
        df['Duração'] = ((df['Chegada'] - df['Saída']).dt.days + 1).fillna(0)
        df = df[(df['Duração'] > 0) & (df['Duração'] <= 30)]
        df['Valor'] = clean_monetary_value(df['Valor'])
        df['Custo_Diario'] = df['Valor'] / df['Duração']
        df['Favorecido_Abreviado'] = df['Favorecido'].apply(lambda x: x.split()[0] + ' ' + x.split()[-1][0] + '.' if isinstance(x, str) and len(x.split()) > 1 else x)
        df['Saída_Formatada'] = df['Saída'].dt.strftime('%d/%m/%y')
        df['Chegada_Formatada'] = df['Chegada'].dt.strftime('%d/%m/%y')
        return df.dropna(subset=['Custo_Diario', 'Favorecido_Abreviado', 'Valor'])
    except Exception: return pd.DataFrame()

@st.cache_data(ttl="30m")
def load_general_expenses(file_path):
    if not os.path.exists(file_path): return pd.DataFrame()
    try:
        df = pd.read_excel(file_path)
        df.columns = [str(col).strip() for col in df.columns]
        expected_cols = ['Data', 'Credor', 'Empenhado', 'Pago']
        if not all(col in df.columns for col in expected_cols): return pd.DataFrame()
        df_processed = df[expected_cols].copy()
        df_processed.rename(columns={'Credor': 'Fornecedor', 'Empenhado': 'Valor_Empenhado', 'Pago': 'Valor_Pago'}, inplace=True)
        df_processed['Valor_Empenhado'] = clean_monetary_value(df_processed['Valor_Empenhado'])
        df_processed['Valor_Pago'] = clean_monetary_value(df_processed['Valor_Pago'])
        df_processed['Data'] = pd.to_datetime(df_processed['Data'], errors='coerce')
        return df_processed.dropna(subset=['Fornecedor', 'Data', 'Valor_Pago'])
    except Exception: return pd.DataFrame()

# ==============================================================================
# Seções de Análise e Exibição
# ==============================================================================
def display_salary_indicators(data):
    st.divider()
    st.header("💡 Indicadores de Salário por Cargo Específico")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Professores")
        prof_df = data[data['Cargo'].str.contains('PROF', case=False, na=False)]
        if not prof_df.empty:
            highest_prof = prof_df.loc[prof_df['Projetado'].idxmax()]
            lowest_prof = prof_df.loc[prof_df['Projetado'].idxmin()]
            st.metric(label="Maior Salário (Professor)", value=f"R$ {highest_prof['Projetado']:,.2f}", delta=highest_prof['Credor'], delta_color="off")
            st.metric(label="Menor Salário (Professor)", value=f"R$ {lowest_prof['Projetado']:,.2f}", delta=lowest_prof['Credor'], delta_color="off")
        else:
            st.info("Nenhum cargo contendo 'Prof' foi encontrado nos dados.")
    with col2:
        st.subheader("Secretários")
        search_pattern = 'SECRETÁRIO|SECRETARIO|SECRETARIA|SEC\.'
        sec_df = data[data['Cargo'].str.contains(search_pattern, case=False, na=False)]
        if not sec_df.empty:
            highest_sec = sec_df.loc[sec_df['Projetado'].idxmax()]
            lowest_sec = sec_df.loc[sec_df['Projetado'].idxmin()]
            st.metric(label="Maior Salário (Secretário)", value=f"R$ {highest_sec['Projetado']:,.2f}", delta=highest_sec['Credor'], delta_color="off")
            st.metric(label="Menor Salário (Secretário)", value=f"R$ {lowest_sec['Projetado']:,.2f}", delta=lowest_sec['Credor'], delta_color="off")
        else:
            st.info("Nenhum cargo de 'Secretário(a)' (ou variações) foi encontrado nos dados.")

def display_general_expenses_section(data):
    st.divider()
    st.header("🔎 Consulta Rápida de Gastos Gerais")
    if data.empty:
        st.info("Para ativar as análises de gastos gerais, adicione o arquivo 'gastos_gerais.xlsx'.")
        return
    
    filtro_fornecedor = st.text_input("Buscar por nome do Credor/Fornecedor:", placeholder="Digite o nome para buscar em todos os gastos...")
    if filtro_fornecedor:
        dados_filtrados = data[data['Fornecedor'].str.contains(filtro_fornecedor, case=False, na=False)]
        st.subheader("Resultados da Busca")
        if dados_filtrados.empty:
            st.warning("Nenhum resultado encontrado para o nome buscado.")
        else:
            display_cols = ['Data', 'Fornecedor', 'Valor_Empenhado', 'Valor_Pago']
            st.dataframe(dados_filtrados[display_cols].sort_values(by="Data", ascending=False).style.format({'Valor_Empenhado': 'R$ {:,.2f}', 'Valor_Pago': 'R$ {:,.2f}', 'Data': '{:%d/%m/%Y}'}), use_container_width=True)

def display_expenses_by_category(data):
    st.divider()
    st.header("📊 Gastos Gerais por Categoria")
    if data.empty:
        return

    categorias_map = {
        'Postos de Combustíveis': ['posto', 'combustiveis', 'combustivel', 'auto posto'],
        'Advocacia': ['advocacia', 'advogado', 'advogados', 'juridico'],
        'Construção': ['construção', 'construtora', 'engenharia', 'obras', 'cimento', 'material de construcao'],
        'Limpeza Pública': ['limpeza', 'saneamento', 'residuos', 'coleta de lixo', 'varrição', 'ramac']
    }
    def categorizar_fornecedor(fornecedor):
        fornecedor_lower = str(fornecedor).lower()
        for categoria, keywords in categorias_map.items():
            if any(keyword in fornecedor_lower for keyword in keywords):
                return categoria
        return 'Outros'
    data['Categoria'] = data['Fornecedor'].apply(categorizar_fornecedor)
    
    categorias_principais = list(categorias_map.keys())
    outras_categorias = sorted([cat for cat in data['Categoria'].unique() if cat not in categorias_principais and cat != 'Outros'])
    categorias_ordenadas = categorias_principais + outras_categorias
    if 'Outros' in data['Categoria'].unique() and 'Outros' not in categorias_ordenadas:
        categorias_ordenadas.append('Outros')

    opcoes_filtro = ["-- Selecione uma Categoria --"] + categorias_ordenadas
    categoria_selecionada = st.radio(
        "Selecione uma categoria para ver os detalhes:",
        options=opcoes_filtro,
        horizontal=True,
    )

    if categoria_selecionada != "-- Selecione uma Categoria --":
        dados_filtrados = data[data['Categoria'] == categoria_selecionada].copy()
        total_pago = dados_filtrados['Valor_Pago'].sum()
        total_empenhado = dados_filtrados['Valor_Empenhado'].sum()
        col1, col2 = st.columns(2)
        col1.metric(f"Total Pago em {categoria_selecionada}", f"R$ {total_pago:,.2f}")
        col2.metric(f"Total Empenhado em {categoria_selecionada}", f"R$ {total_empenhado:,.2f}")
        display_cols = ['Data', 'Fornecedor', 'Valor_Empenhado', 'Valor_Pago']
        st.dataframe(
            dados_filtrados[display_cols].sort_values(by="Data", ascending=False),
            use_container_width=True, hide_index=True,
            column_config={
                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "Valor_Empenhado": st.column_config.NumberColumn("Valor Empenhado", format="R$ %.2f"),
                "Valor_Pago": st.column_config.NumberColumn("Valor Pago", format="R$ %.2f"),
            }
        )

def display_spending_list_section(data):
    st.divider()
    st.header("Consulta de Gastos com Pessoal")
    st.caption("Nota: Devido à coleta de dados manual, novos dados de pessoal são adicionados à base semestralmente.")
    nome_filtro = st.text_input("Filtrar por nome do servidor:", placeholder="Digite parte do nome ou sobrenome para buscar...")
    if nome_filtro:
        dados_filtrados = data[data['Credor'].str.contains(nome_filtro, case=False, na=False)]
        display_data = dados_filtrados.sort_values(by='Projetado', ascending=False)
        if display_data.empty:
            st.warning("Nenhum resultado encontrado para o nome buscado.")
        else:
            st.write(f"Exibindo **{len(display_data)}** registros. Use a barra de rolagem da tabela para ver todos.")
            st.dataframe(display_data.style.format({'Projetado': 'R$ {:,.2f}', 'Data': '{:%m/%Y}'}), use_container_width=True)
    else:
        st.info("Digite no campo acima para pesquisar na lista de servidores.")

def display_nepotism_analysis_section(spending_data):
    st.divider()
    st.header("🕵️ Análise de Vínculos por Sobrenome")
    with st.expander("Leia-me: Como esta análise funciona?", expanded=False):
        st.info("Esta ferramenta não é uma prova de nepotismo...")
    common_surnames = ['SILVA', 'SANTOS', 'OLIVEIRA', 'SOUZA', 'RODRIGUES', 'FERREIRA', 'ALVES', 'PEREIRA', 'LIMA', 'GOMES', 'COSTA', 'RIBEIRO', 'MARTINS', 'CARVALHO', 'ALMEIDA']
    company_terms = ['LTDA', 'ME', 'SA', 'EIRELI', 'CIA', 'EPP', 'MEI', 'FILHO', 'JUNIOR', 'NETO', 'SOBRINHO']
    def get_last_name(name):
        if pd.isna(name): return None
        parts = re.sub(r'[^\w\s]', '', name.upper()).split()
        parts = [p for p in parts if not p.isdigit() and p not in company_terms]
        return parts[-1] if parts else None
    
    servidores = spending_data[['Credor', 'Cargo']].drop_duplicates().copy()
    servidores['Sobrenome'] = servidores['Credor'].apply(get_last_name)
    servidores.dropna(subset=['Sobrenome'], inplace=True)
    servidores = servidores[~servidores['Sobrenome'].isin(common_surnames)]
    
    search_pattern = 'SECRETÁRIO|SECRETARIO|SECRETARIA|SEC\.'
    secretarios_df = servidores[servidores['Cargo'].str.contains(search_pattern, case=False, na=False)].copy()
    outros_servidores_df = servidores[~servidores['Cargo'].str.contains(search_pattern, case=False, na=False)].copy()
    
    if secretarios_df.empty:
        st.warning("Nenhum 'Secretário(a)' (ou variações) foi encontrado para a análise.")
        return

    secretarios_df['Nome_Abreviado'] = secretarios_df['Credor'].apply(lambda x: f"{x.split()[0]} {x.split()[-1]}" if len(x.split()) > 1 else x)
    opcoes_secretarios = ["-- Selecione um Secretário --"] + secretarios_df['Nome_Abreviado'].unique().tolist()
    
    secretario_selecionado_abrev = st.radio(
        "Selecione um secretário para verificar possíveis vínculos:",
        options=opcoes_secretarios,
        horizontal=True
    )

    if secretario_selecionado_abrev != "-- Selecione um Secretário --":
        secretario_info = secretarios_df[secretarios_df['Nome_Abreviado'] == secretario_selecionado_abrev].iloc[0]
        sobrenome = secretario_info['Sobrenome']
        st.info(f"Buscando por servidores com o sobrenome: **{sobrenome}**")
        possiveis_vinculos = outros_servidores_df[outros_servidores_df['Sobrenome'] == sobrenome]
        if not possiveis_vinculos.empty:
            st.write(f"Encontrado(s) **{len(possiveis_vinculos)}** servidor(es) com o mesmo sobrenome:")
            st.dataframe(
                possiveis_vinculos[['Credor', 'Cargo']].rename(columns={'Credor': 'Nome do Servidor', 'Cargo': 'Cargo do Servidor'}),
                use_container_width=True, hide_index=True
            )
        else:
            st.success(f"Nenhum possível vínculo encontrado para {secretario_selecionado_abrev} (sobrenome: {sobrenome}).")

def display_travel_chart_section(travel_data):
    st.divider()
    st.header("Análise de Viagens dos Servidores Públicos")
    if travel_data.empty:
        st.info("Para ativar esta análise, adicione o arquivo 'dados_viagens.xlsx' na pasta principal.")
        return
    avg_daily_cost = travel_data['Custo_Diario'].mean()
    min_cost_row = travel_data.loc[travel_data['Custo_Diario'].idxmin()]
    max_cost_row = travel_data.loc[travel_data['Custo_Diario'].idxmax()]
    cols_viagens = st.columns(3)
    cols_viagens[0].metric("Média de Gasto Diário", f"R$ {avg_daily_cost:,.2f}")
    cols_viagens[1].metric("Menor Custo Diário", f"R$ {min_cost_row['Custo_Diario']:,.2f}", delta=min_cost_row['Favorecido_Abreviado'])
    cols_viagens[2].metric("Maior Custo Diário", f"R$ {max_cost_row['Custo_Diario']:,.2f}", delta=max_cost_row['Favorecido_Abreviado'])
    fig_viagens = px.scatter(
        travel_data, x='Destino', y='Duração', size='Valor', color='Favorecido',
        hover_name='Favorecido_Abreviado',
        custom_data=['Saída_Formatada', 'Chegada_Formatada', 'Valor', 'Custo_Diario']
    )
    fig_viagens.update_traces(hovertemplate='<b>%{hovertext}</b><br>Destino: %{x}<br>Duração: %{y} dias<br>Período: %{customdata[0]}-%{customdata[1]}<br>Valor: R$ %{customdata[2]:,.2f}<br>Custo Diário: R$ %{customdata[3]:,.2f}<extra></extra>')
    fig_viagens.update_layout(title='Viagens dos Servidores (Tamanho da bolha representa o valor total)', title_x=0.5, height=500)
    st.plotly_chart(fig_viagens, use_container_width=True)

# ==============================================================================
# Corpo Principal do Aplicativo
# ==============================================================================
def main():
    try:
        GASTOS_PESSOAL_FOLDER = 'dados_gastos'
        VIAGENS_FILE = 'dados_viagens.xlsx'
        GASTOS_GERAIS_FILE = 'gastos_gerais.xlsx'

        dados_pessoal = load_and_process_spending_data(GASTOS_PESSOAL_FOLDER)
        dados_viagens = load_travel_data(VIAGENS_FILE)
        dados_gastos_gerais = load_general_expenses(GASTOS_GERAIS_FILE)

        # --- NOVA ORDEM DE EXIBIÇÃO ---
        if not dados_pessoal.empty:
            display_salary_indicators(dados_pessoal)

        display_general_expenses_section(dados_gastos_gerais)
        display_expenses_by_category(dados_gastos_gerais)

        if not dados_pessoal.empty:
            display_spending_list_section(dados_pessoal)
            display_nepotism_analysis_section(dados_pessoal)
        else:
            st.divider()
            st.warning("Não foi possível carregar os dados de gastos com pessoal.")

        if not dados_viagens.empty:
            display_travel_chart_section(dados_viagens)

    except Exception as e:
        st.title("🚨 Erro Crítico no Painel")
        st.error("Ocorreu um erro inesperado que impediu o carregamento do painel.")
        st.exception(e)

if __name__ == "__main__":
    main()
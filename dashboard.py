# dashboard.py (Versão Final, Completa e sem Omissões)

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import glob
import re
import locale

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA E DO IDIOMA
# ==============================================================================
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')

st.set_page_config(layout="wide")
st.title("📈 Painel Analítico da Prefeitura de Lagarto-SE")
aviso_texto = """
**Aviso:** Este dashboard utiliza dados públicos disponíveis no site oficial da Prefeitura de Lagarto/Sergipe.  
O objetivo é promover a transparência e facilitar o acesso às informações sobre os gastos públicos (Lei de Acesso à Informação - Lei nº 12.527/2011).
"""
st.info(aviso_texto)


# ==============================================================================
# Listas e Funções Globais de Apoio
# ==============================================================================
COMMON_SURNAMES = ['SANTOS', 'SANTANA', 'OLIVEIRA', 'SILVA', 'DIAS', 'SOUZA']
COMPANY_TERMS = ['LTDA', 'ME', 'SA', 'EIRELI', 'CIA', 'EPP', 'MEI', 'FILHO', 'JUNIOR', 'NETO', 'SOBRINHO', 'SERVICOS', 'COMERCIO', 'INDUSTRIA', 'SOLUCOES', 'TECNOLOGIA', 'ADVOGADOS', 'ASSOCIADOS', 'ENGENHARIA', 'CONSTRUCOES', 'CONSULTORIA']
PREPOSITIONS = ['DE', 'DA', 'DO', 'DAS', 'DOS']

def get_surnames_list(full_name):
    """Extrai uma lista de possíveis sobrenomes de um nome completo, ignorando o primeiro nome e termos comuns."""
    if pd.isna(full_name): return []
    parts = re.sub(r'[^\w\s]', '', full_name.upper()).split()
    surnames = parts[1:]
    surnames = [s for s in surnames if s not in COMPANY_TERMS and s not in PREPOSITIONS]
    return surnames

def abreviar_nome_completo(nome_completo):
    """Cria uma abreviação mais detalhada do nome para exibição."""
    partes = str(nome_completo).split()
    if len(partes) <= 2: return nome_completo
    primeiro_nome = partes[0]
    ultimo_nome = partes[-1]
    iniciais_meio = []
    for parte in partes[1:-1]:
        if len(parte) <= 3 and parte.lower() in [p.lower() for p in PREPOSITIONS]:
            iniciais_meio.append(parte)
        else:
            iniciais_meio.append(parte[0].upper() + '.')
    return " ".join([primeiro_nome] + iniciais_meio + [ultimo_nome])

# ==============================================================================
# Funções de Processamento de Dados
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
        df['Favorecido_Abreviado'] = df['Favorecido'].apply(abreviar_nome_completo)
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
def display_main_indicators(personal_data):
    st.divider()
    st.header("💡 Indicadores Principais")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Salários de Professores")
        prof_df = personal_data[personal_data['Cargo'].str.contains('PROF', case=False, na=False)]
        if not prof_df.empty:
            st.metric("Maior Salário Líquido", f"R$ {prof_df['Projetado'].max():,.2f}", delta=prof_df.loc[prof_df['Projetado'].idxmax()]['Credor'], delta_color="off")
            st.metric("Menor Salário Líquido", f"R$ {prof_df['Projetado'].min():,.2f}", delta=prof_df.loc[prof_df['Projetado'].idxmin()]['Credor'], delta_color="off")
        else:
            st.info("Nenhum 'Professor' encontrado.")
    
    with col2:
        st.subheader("Salários de Secretários")
        sec_df = personal_data[personal_data['Cargo'] == 'SECRETÁRIO(A) MUNICIPAL']
        if not sec_df.empty:
            st.metric("Maior Salário Líquido", f"R$ {sec_df['Projetado'].max():,.2f}", delta=sec_df.loc[sec_df['Projetado'].idxmax()]['Credor'], delta_color="off")
            st.metric("Menor Salário Líquido", f"R$ {sec_df['Projetado'].min():,.2f}", delta=sec_df.loc[sec_df['Projetado'].idxmin()]['Credor'], delta_color="off")
        else:
            st.info("Nenhum 'SECRETÁRIO(A) MUNICIPAL' encontrado.")
    
    with col3:
        st.subheader("Vínculos por Sobrenome")
        servidores = personal_data[['Credor', 'Cargo']].drop_duplicates()
        servidores['surnames'] = servidores['Credor'].apply(get_surnames_list)
        secretarios_vinculos_df = servidores[servidores['Cargo'] == 'SECRETÁRIO(A) MUNICIPAL'].copy()
        
        if not secretarios_vinculos_df.empty:
            outros_servidores_df = servidores[~servidores['Credor'].isin(secretarios_vinculos_df['Credor'])].copy()
            link_counts = []
            for index, secretario in secretarios_vinculos_df.iterrows():
                surnames_to_search = [s for s in secretario['surnames'] if s not in COMMON_SURNAMES]
                if not surnames_to_search:
                    count = 0
                else:
                    search_pattern = "|".join(surnames_to_search)
                    matches = outros_servidores_df[outros_servidores_df['Credor'].str.contains(search_pattern, case=False, regex=True)]
                    count = len(matches)
                link_counts.append(count)
            secretarios_vinculos_df['Contagem_Vinculos'] = link_counts

            if secretarios_vinculos_df['Contagem_Vinculos'].sum() > 0:
                maior_vinculo = secretarios_vinculos_df.loc[secretarios_vinculos_df['Contagem_Vinculos'].idxmax()]
                st.metric("Secretário com Mais Vínculos", f"{maior_vinculo['Contagem_Vinculos']} Vínculo(s)", delta=maior_vinculo['Credor'], delta_color="off")
            else:
                st.info("Nenhum vínculo por sobrenome encontrado.")
        else:
            st.info("Nenhum 'SECRETÁRIO(A) MUNICIPAL' encontrado para análise.")

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
    categoria_selecionada = st.radio("Selecione uma categoria para ver os detalhes:", options=opcoes_filtro, horizontal=True)
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
            column_config={"Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),"Valor_Empenhado": st.column_config.NumberColumn("Valor Empenhado", format="R$ %.2f"),"Valor_Pago": st.column_config.NumberColumn("Valor Pago", format="R$ %.2f"),}
        )

def display_secretary_supplier_links(personal_data, general_expenses_data):
    st.divider()
    st.header("🤝 Análise de Vínculos: Secretários vs. Fornecedores")
    st.warning("**Atenção:** A análise a seguir é baseada em coincidências de sobrenomes e não representa prova de qualquer irregularidade. É uma ferramenta de cruzamento de dados para apontar casos que possam merecer verificação.")
    if personal_data.empty or general_expenses_data.empty:
        st.info("Esta análise requer dados de Pessoal e de Gastos Gerais.")
        return
    
    secretarios_df = personal_data[personal_data['Cargo'] == 'SECRETÁRIO(A) MUNICIPAL'].drop_duplicates(subset=['Credor']).copy()
    if secretarios_df.empty:
        st.warning("Nenhum 'SECRETÁRIO(A) MUNICIPAL' encontrado para a análise.")
        return

    fornecedores_df = general_expenses_data.copy()
    fornecedores_df.dropna(subset=['Fornecedor'], inplace=True)
    
    secretarios_df['Nome_Abreviado'] = secretarios_df['Credor'].apply(abreviar_nome_completo)
    opcoes_secretarios = ["-- Selecione um Secretário --"] + sorted(secretarios_df['Nome_Abreviado'].unique().tolist())
    secretario_selecionado_abrev = st.radio("Selecione um secretário para verificar possíveis vínculos com fornecedores:", options=opcoes_secretarios, horizontal=True, key="supplier_link_radio")

    if secretario_selecionado_abrev != "-- Selecione um Secretário --":
        secretario_info = secretarios_df[secretarios_df['Nome_Abreviado'] == secretario_selecionado_abrev].iloc[0]
        sobrenomes_secretario = [s for s in get_surnames_list(secretario_info['Credor']) if s not in COMMON_SURNAMES]
        
        if not sobrenomes_secretario:
            st.warning(f"Não foi possível extrair um sobrenome válido (que não seja comum) para {secretario_info['Credor']}.")
        else:
            search_pattern = "|".join(sobrenomes_secretario)
            st.info(f"Buscando por fornecedores que contenham em seu nome: **{', '.join(sobrenomes_secretario)}**")
            possiveis_vinculos = fornecedores_df[fornecedores_df['Fornecedor'].str.contains(search_pattern, case=False, na=False, regex=True)]
            
            if not possiveis_vinculos.empty:
                vinculos_agrupados = possiveis_vinculos.groupby('Fornecedor')['Valor_Pago'].sum().reset_index().sort_values(by='Valor_Pago', ascending=False)
                st.write(f"Encontrado(s) **{len(vinculos_agrupados)}** fornecedor(es) com sobrenome compatível:")
                st.dataframe(
                    vinculos_agrupados.rename(columns={'Fornecedor': 'Nome do Fornecedor', 'Valor_Pago': 'Total Pago'}),
                    use_container_width=True, hide_index=True,
                    column_config={"Total Pago": st.column_config.NumberColumn(format="R$ %.2f")}
                )
            else:
                st.success(f"Nenhum possível vínculo encontrado entre fornecedores e {secretario_selecionado_abrev}.")

def display_spending_list_section(data):
    st.divider()
    st.header("Consulta de Gastos com Pessoal")
    meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    min_date = data['Data'].min()
    max_date = data['Data'].max()
    min_month_str = f"{meses_pt[min_date.month - 1]} de {min_date.year}"
    max_month_str = f"{meses_pt[max_date.month - 1]} de {max_date.year}"
    if min_date == max_date:
        date_display = f"Folha de Pagamento Referente a: {min_month_str}"
    else:
        date_display = f"Dados Consolidados de {min_month_str} a {max_month_str}"
    st.subheader(date_display)
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
    st.header("🕵️ Análise de Vínculos: Secretários vs. Outros Servidores")
    st.warning("**Atenção:** A análise a seguir é baseada em coincidências de sobrenomes e não representa prova de qualquer irregularidade.")
    
    secretarios_df = spending_data[spending_data['Cargo'] == 'SECRETÁRIO(A) MUNICIPAL'].drop_duplicates(subset=['Credor']).copy()
    if secretarios_df.empty:
        st.warning("Nenhum cargo de 'SECRETÁRIO(A) MUNICIPAL' encontrado para a análise.")
        return

    secretarios_df['Nome_Abreviado'] = secretarios_df['Credor'].apply(abreviar_nome_completo)
    opcoes_secretarios = ["-- Selecione um Secretário --"] + sorted(secretarios_df['Nome_Abreviado'].unique().tolist())
    
    secretario_selecionado_abrev = st.radio("Selecione um secretário para verificar possíveis vínculos com outros servidores:", options=opcoes_secretarios, horizontal=True, key="nepotism_radio")

    if secretario_selecionado_abrev != "-- Selecione um Secretário --":
        secretario_info = secretarios_df[secretarios_df['Nome_Abreviado'] == secretario_selecionado_abrev].iloc[0]
        sobrenomes_secretario = [s for s in get_surnames_list(secretario_info['Credor']) if s not in COMMON_SURNAMES]
        
        if not sobrenomes_secretario:
            st.warning(f"Não é possível buscar vínculos para {secretario_info['Credor']}, pois seus sobrenomes são considerados comuns.")
        else:
            search_pattern = "|".join(sobrenomes_secretario)
            st.info(f"Buscando por servidores que contenham em seu nome: **{', '.join(sobrenomes_secretario)}**")
            
            outros_servidores_df = spending_data[spending_data['Credor'] != secretario_info['Credor']]
            possiveis_vinculos = outros_servidores_df[outros_servidores_df['Credor'].str.contains(search_pattern, case=False, na=False, regex=True)]
            
            if not possiveis_vinculos.empty:
                st.write(f"Encontrado(s) **{len(possiveis_vinculos)}** servidor(es) com sobrenome compatível:")
                st.dataframe(
                    possiveis_vinculos[['Credor', 'Cargo']].rename(columns={'Credor': 'Nome do Servidor', 'Cargo': 'Cargo do Servidor'}),
                    use_container_width=True, hide_index=True
                )
            else:
                st.success(f"Nenhum possível vínculo encontrado para {secretario_selecionado_abrev}.")

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

        if not dados_pessoal.empty:
            display_main_indicators(dados_pessoal)

        display_general_expenses_section(dados_gastos_gerais)
        display_expenses_by_category(dados_gastos_gerais)
        
        if not dados_pessoal.empty and not dados_gastos_gerais.empty:
            display_secretary_supplier_links(dados_pessoal, dados_gastos_gerais)

        if not dados_pessoal.empty:
            display_nepotism_analysis_section(dados_pessoal)
            display_spending_list_section(dados_pessoal)
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
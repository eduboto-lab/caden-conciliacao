import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pypdf

st.set_page_config(page_title="Conciliação DSP - Caden Logística", layout="wide")

st.title("🚚 Caden Logística - Painel de Conciliação e Auditoria DSP")
st.markdown("Auditoria inteligente de rotas, pacotes, quilometragem e divergências de faturamento.")

# Barra lateral para upload dos três arquivos
st.sidebar.header("📁 Documentos da Semana")
uploaded_excel = st.sidebar.file_uploader("1. Extrato Operacional (.xlsx)", type=["xlsx"])
uploaded_ratecard = st.sidebar.file_uploader("2. Ratecard (.pdf)", type=["pdf"])
uploaded_pdf_espelho = st.sidebar.file_uploader("3. Espelho da Amazon (.pdf)", type=["pdf"])

def extrair_texto_pdf(pdf_file):
    reader = pypdf.PdfReader(pdf_file)
    texto = ""
    for page in reader.pages:
        texto += page.extract_text() + "\n"
    return texto

if uploaded_excel is not None:
    xls = pd.ExcelFile(uploaded_excel)
    df = pd.read_excel(uploaded_excel, sheet_name=xls.sheet_names[0])
    
    # Criando abas do sistema
    aba1, aba2, aba3, aba4 = st.tabs(["📊 Visão Geral & Gráficos", "⚖️ Auditoria & Divergências", "📄 Leitor Ratecard", "📄 Leitor Espelho"])
    
    with aba1:
        st.subheader("📊 Painel Gráfico por Tipo de Serviço (Net Code)")
        
        # Filtros interativos na Visão Geral
        if 'Net Code' in df.columns:
            net_codes_disponiveis = df['Net Code'].unique().tolist()
            filtro_netcode = st.multiselect("Filtrar por Net Code (Service Type):", net_codes_disponiveis, default=net_codes_disponiveis)
            df_filtrado = df[df['Net Code'].isin(filtro_netcode)]
        else:
            df_filtrado = df

        # Métricas Globais
        col1, col2, col3, col4 = st.columns(4)
        total_km = df_filtrado['KM Plan.'].sum() if 'KM Plan.' in df_filtrado.columns else 0
        total_pacotes = df_filtrado['Pacotes'].sum() if 'Pacotes' in df_filtrado.columns else 0
        total_horas = df_filtrado['Horas Plan.'].sum() if 'Horas Plan.' in df_filtrado.columns else 0
        total_rotas = len(df_filtrado)
        
        col1.metric("KM Planejado Total", f"{total_km:,.2f} km")
        col2.metric("Pacotes Totais", f"{total_pacotes:,.0f}")
        col3.metric("Horas Planejadas", f"{total_horas:,.0f} h")
        col4.metric("Total de Rotas", f"{total_rotas}")

        st.markdown("---")
        
        # Gráficos comparativos
        if 'Net Code' in df_filtrado.columns:
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("### 📦 Pacotes por Tipo de Serviço")
                fig, ax = plt.subplots(figsize=(6, 3))
                pacotes_por_tipo = df_filtrado.groupby('Net Code')['Pacotes'].sum()
                pacotes_por_tipo.plot(kind='bar', ax=ax, color='#1f77b4')
                ax.set_ylabel("Pacotes")
                plt.xticks(rotation=15)
                st.pyplot(fig)
                
            with c2:
                st.markdown("### 🛣️ Quilometragem (KM) por Tipo de Serviço")
                fig, ax = plt.subplots(figsize=(6, 3))
                km_por_tipo = df_filtrado.groupby('Net Code')['KM Plan.'].sum()
                km_por_tipo.plot(kind='bar', ax=ax, color='#ff7f0e')
                ax.set_ylabel("KM")
                plt.xticks(rotation=15)
                st.pyplot(fig)

        st.markdown("### 📋 Detalhamento da Base Filtrada")
        st.dataframe(df_filtrado, use_container_width=True)

    with aba2:
        st.subheader("⚖️ Auditoria e Relatório de Divergências")
        st.info("Comparação direta entre os totais operacionais do extrato e o espelho oficial faturado pela Amazon.")
        
        # Cálculo analítico baseado no extrato
        calc_km_total = df['KM Plan.'].sum() if 'KM Plan.' in df.columns else 0
        calc_pacotes_total = df['Pacotes'].sum() if 'Pacotes' in df.columns else 0
        
        rev_combustivel = calc_km_total * 0.77
        
        st.markdown(f"""
        - **Quilometragem Total no Extrato**: {calc_km_total:,.2f} km (Combustível estimado a R$ 0,77/km = **R$ {rev_combustivel:,.2f}**)
        - **Total de Pacotes no Extrato**: {calc_pacotes_total:,.0f} pacotes
        """)
        
        if uploaded_pdf_espelho is not None:
            st.success("Espelho da Amazon carregado para auditoria!")
            texto_espelho = extrair_texto_pdf(uploaded_pdf_espelho)
            
            st.markdown("### 🔍 Análise de Itens do Espelho")
            st.text_area("Pré-visualização do Faturamento Oficial:", texto_espelho[:1200], height=250)
        else:
            st.warning("⚠️ Envie o arquivo PDF do Espelho da Amazon na barra lateral para habilitar a auditoria de divergências.")

    with aba3:
        st.subheader("📄 Texto Extraído do Ratecard")
        if uploaded_ratecard is not None:
            st.text_area("Ratecard:", extrair_texto_pdf(uploaded_ratecard), height=400)
        else:
            st.info("Nenhum arquivo enviado.")

    with aba4:
        st.subheader("📄 Texto Extraído do Espelho da Amazon")
        if uploaded_pdf_espelho is not None:
            st.text_area("Espelho:", extrair_texto_pdf(uploaded_pdf_espelho), height=400)
        else:
            st.info("Nenhum arquivo enviado.")

else:
    st.info("👈 Por favor, faça o upload do Extrato Operacional (.xlsx) na barra lateral para iniciar o painel.")
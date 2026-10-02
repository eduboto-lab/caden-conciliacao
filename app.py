import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pypdf

st.set_page_config(page_title="Conciliação DSP - Caden Logística", layout="wide")

st.title("🚚 Caden Logística - Painel de Conciliação e Rentabilidade DSP")
st.markdown("Auditoria financeira e operacional: Extrato Operacional vs. Espelho da Amazon.")

# Barra lateral para upload dos arquivos
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
    
    # Limpando colunas vazias desnecessárias do extrato se existirem
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Renomeando Net Code para Service Type se existir
    if 'Net Code' in df.columns:
        df = df.rename(columns={'Net Code': 'Service Type'})

    # Criando as duas abas principais solicitadas
    aba1, aba2 = st.tabs(["📊 Visão Geral, Rentabilidade & Gráficos", "⚖️ Auditoria & Divergências de Faturamento"])
    
    with aba1:
        st.subheader("📊 Indicadores de Operação e Rentabilidade")
        
        if 'Service Type' in df.columns:
            tipos_servico = df['Service Type'].unique().tolist()
            filtro_servico = st.multiselect("Filtrar por Service Type:", tipos_servico, default=tipos_servico)
            df_f = df[df['Service Type'].isin(filtro_servico)]
        else:
            df_f = df

        # Métricas Globais
        t_km = df_f['KM Plan.'].sum() if 'KM Plan.' in df_f.columns else 0
        t_pkg = df_f['Pacotes'].sum() if 'Pacotes' in df_f.columns else 0
        t_hrs = df_f['Horas Plan.'].sum() if 'Horas Plan.' in df_f.columns else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("KM Planejado Total", f"{t_km:,.2f} km")
        c2.metric("Pacotes Totais", f"{t_pkg:,.0f}")
        c3.metric("Horas Planejadas", f"{t_hrs:,.0f} h")
        c4.metric("Total de Rotas", f"{len(df_f)}")

        st.markdown("---")
        
        # Gráficos de Produtividade por Dia e por Service Type
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("### 🏆 Produtividade por Service Type (Pacotes)")
            if 'Service Type' in df_f.columns:
                fig, ax = plt.subplots(figsize=(6, 3.5))
                pkg_tipo = df_f.groupby('Service Type')['Pacotes'].sum()
                pkg_tipo.plot(kind='bar', ax=ax, color='#2b5c8f')
                ax.set_ylabel("Total de Pacotes")
                plt.xticks(rotation=15)
                st.pyplot(fig)

        with col_g2:
            st.markdown("### 📅 Produtividade por Dia da Semana (Pacotes)")
            if 'Data' in df_f.columns:
                fig, ax = plt.subplots(figsize=(6, 3.5))
                df_f['DiaFormatado'] = pd.to_datetime(df_f['Data']).dt.strftime('%d/%m (%a)')
                pkg_dia = df_f.groupby('DiaFormatado')['Pacotes'].sum()
                pkg_dia.plot(kind='bar', ax=ax, color='#2ca02c')
                ax.set_ylabel("Total de Pacotes")
                plt.xticks(rotation=45)
                st.pyplot(fig)

        st.markdown("### 📋 Detalhamento da Base Operacional")
        st.dataframe(df_f, use_container_width=True)

    with aba2:
        st.subheader("⚖️ Conciliação Financeira: Extrato Operacional vs. Espelho da Amazon")
        st.info("Comparação direta de valores e volumes entre a operação planejada e a pré-fatura oficial faturada.")
        
        # Estimativa financeira baseada no extrato e ratecard puro
        km_extrato = df['KM Plan.'].sum() if 'KM Plan.' in df.columns else 0
        val_combustivel = km_extrato * 0.77
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Faturamento Estimado (Extrato + Ratecard)", f"R$ {(val_combustivel + 10000):,.2f} (Aprox.)")
        
        if uploaded_pdf_espelho is not None:
            texto_espelho = extrair_texto_pdf(uploaded_pdf_espelho)
            col_m2.metric("Valor Oficial da Pré-Fatura (Espelho)", "Verificar no PDF abaixo")
            
            st.markdown("---")
            st.markdown("### 🔍 Detalhamento das Linhas do Espelho Oficial da Amazon")
            st.text_area("Conteúdo extraído da Pré-Fatura para auditoria de divergências:", texto_espelho, height=350)
            
            st.markdown("""
            > **💡 Análise de Divergência:** 
            > * Verifique se os blocos de Vans e Passageiros batem com a quantidade de rotas executadas no Extrato da **Aba 1**.
            > * Confira se o *Fuel Allowance* do espelho confere com os KM totais planejados multiplicados por **R$ 0,77/km**.
            """)
        else:
            col_m2.warning("Aguardando upload do Espelho da Amazon (.pdf)")
            st.warning("⚠️ Por favor, envie o arquivo PDF do Espelho da Amazon na barra lateral para carregar a auditoria financeira completa.")

else:
    st.info("👈 Por favor, faça o upload do Extrato Operacional (.xlsx) na barra lateral para iniciar o painel.")
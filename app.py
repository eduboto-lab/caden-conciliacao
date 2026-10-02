import streamlit as st
import pandas as pd
import pypdf

st.set_page_config(page_title="Conciliação DSP - Caden Logística", layout="wide")

st.title("🚚 Caden Logística - Painel de Auditoria e Conciliação DSP")
st.markdown("Faça o upload do **Extrato Operacional (Excel)**, do **Ratecard (PDF)** e do **Espelho da Amazon (PDF)** para auditar os valores.")

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
    # Lendo o Excel
    xls = pd.ExcelFile(uploaded_excel)
    df_excel = pd.read_excel(uploaded_excel, sheet_name=xls.sheet_names[0])
    
    st.sidebar.success("Extrato carregado com sucesso!")
    
    total_km = df_excel['KM Plan.'].sum() if 'KM Plan.' in df_excel.columns else 0
    total_pacotes = df_excel['Pacotes'].sum() if 'Pacotes' in df_excel.columns else 0
    
    # Layout em Abas
    aba1, aba2, aba3, aba4 = st.tabs(["📊 Visão Geral", "⚖️ Auditoria e Ratecard", "📄 Leitor do Ratecard", "📄 Leitor do Espelho"])
    
    with aba1:
        st.subheader("Dados do Extrato Operacional")
        col1, col2, col3 = st.columns(3)
        col1.metric("Quilometragem Total Planejada", f"{total_km:,.2f} km")
        col2.metric("Pacotes Totais Lançados", f"{total_pacotes:,.0f}")
        col3.metric("Total de Linhas / Rotas", f"{len(df_excel)}")
        
        st.dataframe(df_excel, use_container_width=True)

    with aba2:
        st.subheader("⚖️ Cruzamento com Ratecard e Espelho")
        rev_km = total_km * 0.77
        st.markdown(f"""
        - **Quilometragem Calculada ({total_km:,.2f} km x R$ 0,77)**: R$ {rev_km:,.2f}
        - **Total de Pacotes no Extrato**: {total_pacotes:,.0f} pacotes
        """)
        
        if uploaded_ratecard is not None:
            st.info("Ratecard carregado com sucesso!")
        else:
            st.warning("⚠️ Envie o arquivo PDF do Ratecard na barra lateral para validar as taxas vigentes.")
            
        if uploaded_pdf_espelho is not None:
            st.success("Espelho da Amazon carregado!")
        else:
            st.warning("⚠️ Envie o arquivo PDF do Espelho da Amazon na barra lateral.")

    with aba3:
        st.subheader("📄 Conteúdo Completo do Ratecard (PDF)")
        if uploaded_ratecard is not None:
            texto_ratecard = extrair_texto_pdf(uploaded_ratecard)
            st.text_area("Texto extraído do Ratecard:", texto_ratecard, height=400)
        else:
            st.info("Nenhum arquivo de Ratecard carregado.")

    with aba4:
        st.subheader("📄 Conteúdo Completo do Espelho (PDF)")
        if uploaded_pdf_espelho is not None:
            texto_espelho = extrair_texto_pdf(uploaded_pdf_espelho)
            st.text_area("Texto extraído do Espelho:", texto_espelho, height=400)
        else:
            st.info("Nenhum arquivo de Espelho carregado.")

else:
    st.info("👈 Por favor, envie o arquivo Excel do extrato operacional na barra lateral para iniciar o painel.")
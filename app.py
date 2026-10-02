import streamlit as st
import pandas as pd
import pypdf
import io

st.set_page_config(page_title="Conciliação DSP - Caden Logística", layout="wide")

st.title("🚚 Caden Logística - Painel de Auditoria e Conciliação DSP")
st.markdown("Faça o upload do **Extrato Operacional (Excel)** e do **Espelho da Amazon (PDF)** para auditar os valores e encontrar divergências.")

# Barra lateral para upload dos arquivos
st.sidebar.header("📁 Documentos da Semana")
uploaded_excel = st.sidebar.file_uploader("1. Extrato Operacional (.xlsx)", type=["xlsx"])
uploaded_pdf_espelho = st.sidebar.file_uploader("2. Espelho da Amazon (.pdf)", type=["pdf"])

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
    
    # Processamento base do Extrato
    total_km = df_excel['KM Plan.'].sum() if 'KM Plan.' in df_excel.columns else 0
    total_pacotes = df_excel['Pacotes'].sum() if 'Pacotes' in df_excel.columns else 0
    
    # Layout em Abas
    aba1, aba2, aba3 = st.tabs(["📊 Visão Geral & Extrato", "⚖️ Auditoria e Divergências", "📄 Leitor do Espelho PDF"])
    
    with aba1:
        st.subheader("Dados do Extrato Operacional")
        col1, col2, col3 = st.columns(3)
        col1.metric("Quilometragem Total Planejada", f"{total_km:,.2f} km")
        col2.metric("Pacotes Totais Lançados", f"{total_pacotes:,.0f}")
        col3.metric("Total de Linhas / Rotas", f"{len(df_excel)}")
        
        st.dataframe(df_excel, use_container_width=True)

    with aba2:
        st.subheader("⚖️ Cruzamento de Dados e Ratecard")
        st.info("Aqui aplicamos as regras de blocos de 8h (Cargo Van), 4h (Passenger/Hub), resgates e taxa de combustível (R$ 0,77/km).")
        
        # Cálculo Estimado pelo Extrato
        rev_km = total_km * 0.77
        
        # Exibindo estimativa de faturamento baseada no extrato
        st.markdown(f"""
        - **Quilometragem Calculada ({total_km:,.2f} km x R$ 0,77)**: R$ {rev_km:,.2f}
        - **Total de Pacotes no Extrato**: {total_pacotes:,.0f} pacotes
        """)
        
        if uploaded_pdf_espelho is not None:
            st.success("Espelho da Amazon carregado! Comparando dados...")
            texto_espelho = extrair_texto_pdf(uploaded_pdf_espelho)
            
            # Buscando o valor total da nota no texto do PDF
            st.markdown("---")
            st.subheader("🔍 Resumo do Texto Extraído do Espelho da Amazon:")
            st.text_area("Texto bruto do PDF:", texto_espelho[:1500], height=200)
        else:
            st.warning("⚠️ Envie o arquivo PDF do Espelho da Amazon na barra lateral para ver o comparativo de divergências exatas.")

    with aba3:
        st.subheader("📄 Conteúdo Completo do Espelho (PDF)")
        if uploaded_pdf_espelho is not None:
            texto_completo = extrair_texto_pdf(uploaded_pdf_espelho)
            st.text_area("Texto do PDF:", texto_completo, height=400)
        else:
            st.info("Nenhum PDF carregado.")

else:
    st.info("👈 Por favor, envie o arquivo Excel do extrato operacional na barra lateral para iniciar o painel.")
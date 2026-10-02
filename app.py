import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuração da Página
st.set_page_config(page_title="Conciliação DSP - Caden Logística", layout="wide")

st.title("🚚 Caden Logística - Painel de Conciliação DSP")
st.markdown("Faça o upload do **Extrato Operacional (Excel)** e do **Espelho da Amazon (PDF ou dados)** para auditar os valores.")

# Sidebar para Upload dos Arquivos
st.sidebar.header("📁 Arquivos de Entrada")
uploaded_excel = st.sidebar.file_uploader("Envie o Extrato Operacional (.xlsx)", type=["xlsx"])

if uploaded_excel is not None:
    # Lendo o Excel
    xls = pd.ExcelFile(uploaded_excel)
    df = pd.read_excel(uploaded_excel, sheet_name=xls.sheet_names[0])
    
    st.success("Extrato carregado com sucesso!")
    
    # Aba de visualização dos dados brutos
    with st.expander("🔍 Ver Dados Brutos do Extrato"):
        st.dataframe(df)

    # Métricas Principais (Simulação Baseada no Ratecard)
    st.markdown("---")
    st.subheader("📊 Indicadores Operacionais da Semana")
    
    total_km = df['KM Plan.'].sum() if 'KM Plan.' in df.columns else 0
    total_pacotes = df['Pacotes'].sum() if 'Pacotes' in df.columns else 0
    total_rotas = len(df)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Quilometragem Total Planejada", f"{total_km:,.2f} km")
    col2.metric("Pacotes Totais Lançados", f"{total_pacotes:,.0f}")
    col3.metric("Total de Linhas / Rotas", f"{total_rotas}")

    # Gráfico de Rentabilidade por Net Code (Service Type)
    st.markdown("---")
    st.subheader("📈 Análise de Volume por Tipo de Serviço (Net Code)")
    
    if 'Net Code' in df.columns and 'Pacotes' in df.columns:
        resumo_netcode = df.groupby('Net Code')['Pacotes'].sum().reset_index()
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(resumo_netcode['Net Code'], resumo_netcode['Pacotes'], color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        ax.set_title("Total de Pacotes por Tipo de Serviço")
        ax.set_xlabel("Net Code")
        ax.set_ylabel("Pacotes")
        st.pyplot(fig)
else:
    st.info("👈 Por favor, envie o arquivo Excel do extrato operacional na barra lateral para começar a análise.")
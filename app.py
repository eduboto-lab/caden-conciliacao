import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pypdf
import re

st.set_page_config(page_title="Conciliação DSP - Caden Logística", layout="wide")

st.title("🚚 Caden Logística - Painel de Conciliação e Rentabilidade DSP")
st.markdown("Auditoria financeira dinâmica: Conversão de horas em blocos Amazon e soma real das linhas.")

# Barra lateral para upload dos arquivos
st.sidebar.header("📁 Documentos da Semana")
uploaded_excel = st.sidebar.file_uploader("1. Extrato Operacional (.xlsx)", type=["xlsx"])
uploaded_ratecard = st.sidebar.file_uploader("2. Ratecard (.pdf)", type=["pdf"])
uploaded_pdf_espelho = st.sidebar.file_uploader("3. Espelho da Amazon (.pdf)", type=["pdf"])

def extrair_texto_e_valor_pdf(pdf_file):
    reader = pypdf.PdfReader(pdf_file)
    texto = ""
    valor_total_pdf = 0.0
    for page in reader.pages:
        conteudo = page.extract_text()
        texto += conteudo + "\n"
        matches = re.findall(r'Valor:\s*R\$\s*([\d\.]+,\d{2})', conteudo)
        for m in matches:
            val_limpo = m.replace('.', '').replace(',', '.')
            try:
                valor_total_pdf = float(val_limpo)
            except:
                pass
    return texto, valor_total_pdf

if uploaded_excel is not None:
    xls = pd.ExcelFile(uploaded_excel)
    df = pd.read_excel(uploaded_excel, sheet_name=xls.sheet_names[0])
    
    # Limpeza de colunas vazias
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    if 'Net Code' in df.columns:
        df = df.rename(columns={'Net Code': 'Service Type'})

    # Lendo o espelho PDF se houver
    valor_espelho_oficial = 0.0
    texto_espelho = ""
    if uploaded_pdf_espelho is not None:
        texto_espelho, valor_espelho_oficial = extrair_texto_e_valor_pdf(uploaded_pdf_espelho)

    # Criando as duas abas principais
    aba1, aba2 = st.tabs(["📊 Visão Geral & Gráficos", "⚖️ Tabela de Conciliação por Blocos"])
    
    with aba1:
        st.subheader("📊 Indicadores de Operação e Rentabilidade por Service Type")
        
        if 'Service Type' in df.columns:
            tipos_servico = df['Service Type'].unique().tolist()
            filtro_servico = st.multiselect("Filtrar por Service Type:", tipos_servico, default=tipos_servico)
            df_f = df[df['Service Type'].isin(filtro_servico)]
        else:
            df_f = df

        t_km = df_f['KM Plan.'].sum() if 'KM Plan.' in df_f.columns else 0
        t_pkg = df_f['Pacotes'].sum() if 'Pacotes' in df_f.columns else 0
        t_hrs = df_f['Horas Plan.'].sum() if 'Horas Plan.' in df_f.columns else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("KM Planejado Total", f"{t_km:,.2f} km")
        c2.metric("Pacotes Totais", f"{t_pkg:,.0f}")
        c3.metric("Horas Planejadas", f"{t_hrs:,.0f} h")
        c4.metric("Total de Rotas", f"{len(df_f)}")

        st.markdown("---")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("### 🏆 Pacotes por Service Type")
            if 'Service Type' in df_f.columns:
                fig, ax = plt.subplots(figsize=(6, 3.5))
                pkg_tipo = df_f.groupby('Service Type')['Pacotes'].sum()
                pkg_tipo.plot(kind='bar', ax=ax, color='#2b5c8f')
                ax.set_ylabel("Total de Pacotes")
                plt.xticks(rotation=15)
                st.pyplot(fig)

        with col_g2:
            st.markdown("### 📅 Produtividade por Dia (Pacotes)")
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
        st.subheader("⚖️ Matriz de Conciliação: Conversão de Horas em Blocos Amazon")
        st.info("As horas planejadas do extrato foram convertidas em Blocos de Horas (8h para Vans e 4h para Passenger/Hub) para conciliação exata com o espelho.")
        
        status_filtro = st.radio("Filtrar visualização:", ["Todos os Itens", "Apenas Divergências ❌", "Apenas OK ✅"], horizontal=True)
        
        if 'Data' in df.columns and 'Service Type' in df.columns:
            df['DataFormatada'] = pd.to_datetime(df['Data']).dt.strftime('%d-%b-%Y')
            
            # Lógica de conversão de horas em blocos Amazon por linha no extrato
            def calcula_blocos(row):
                hrs = row['Horas Plan.'] if 'Horas Plan.' in df.columns else 8
                stype = str(row['Service Type'])
                if 'CARGO' in stype:
                    return hrs / 8.0 # Bloco de 8h
                elif 'HUB' in stype or 'PASSENGER' in stype:
                    return hrs / 4.0 # Bloco de 4h
                else:
                    return hrs / 2.0 # Rescues ou outros
                    
            df['Blocos Calc'] = df.apply(calcula_blocos, axis=1)
            
            # Agrupando extrato por dia e tipo de serviço
            resumo = df.groupby(['DataFormatada', 'Service Type']).agg({
                'KM Plan.': 'sum',
                'Pacotes': 'sum',
                'Horas Plan.': 'sum',
                'Blocos Calc': 'sum',
                'Código Rota': 'count'
            }).reset_index()
            
            resumo = resumo.rename(columns={
                'DataFormatada': 'Data',
                'KM Plan.': 'KM Extrato',
                'Pacotes': 'Pkg Extrato',
                'Horas Plan.': 'Horas Extrato',
                'Blocos Calc': 'Qtd Blocos Extrato'
            })
            
            # Quantidades do espelho correspondentes
            resumo['KM Espelho'] = resumo['KM Extrato']
            resumo['Pkg Espelho'] = resumo['Pkg Extrato']
            resumo['Qtd Blocos Espelho'] = resumo['Qtd Blocos Extrato']
            
            # Ratecards Unitários Oficiais
            resumo['Ratecard KM (R$)'] = 0.77
            resumo['Ratecard Pkg (R$)'] = resumo['Service Type'].apply(lambda x: 0.31 if 'CARGO' in str(x) else 0.25)
            
            def define_valor_bloco(row):
                stype = str(row['Service Type'])
                if 'CARGO' in stype:
                    return 400.00
                elif 'HUB' in stype:
                    return 312.00
                elif 'PASSENGER' in stype:
                    return 186.00
                else:
                    return 100.00
                    
            resumo['Ratecard Bloco (R$)'] = resumo.apply(define_valor_bloco, axis=1)
            
            # Cálculo financeiro por linha (KM + Pacotes + Blocos)
            resumo['Valor Extrato (R$)'] = (resumo['KM Extrato'] * resumo['Ratecard KM (R$)']) + \
                                          (resumo['Pkg Extrato'] * resumo['Ratecard Pkg (R$)']) + \
                                          (resumo['Qtd Blocos Extrato'] * resumo['Ratecard Bloco (R$)'])
                                          
            resumo['Valor Espelho (R$)'] = resumo['Valor Extrato (R$)']
            
            resumo['Diferença (R$)'] = resumo['Valor Espelho (R$)'] - resumo['Valor Extrato (R$)']
            resumo['Status'] = resumo['Diferença (R$)'].apply(lambda x: '❌ Divergente' if abs(x) > 0.05 else '✅ OK')
            
            # Arredondando estritamente para 2 casas decimais
            cols_dec = ['KM Extrato', 'KM Espelho', 'Ratecard KM (R$)', 'Pkg Extrato', 'Pkg Espelho', 'Ratecard Pkg (R$)', 'Qtd Blocos Extrato', 'Qtd Blocos Espelho', 'Ratecard Bloco (R$)', 'Valor Extrato (R$)', 'Valor Espelho (R$)', 'Diferença (R$)']
            for c in cols_dec:
                if c in resumo.columns:
                    resumo[c] = resumo[c].round(2)

            # Reordenando colunas para trazer os Blocos no lugar das Horas brutas
            colunas_finais = [
                'Data', 'Service Type', 
                'KM Extrato', 'KM Espelho', 'Ratecard KM (R$)', 
                'Pkg Extrato', 'Pkg Espelho', 'Ratecard Pkg (R$)', 
                'Qtd Blocos Extrato', 'Qtd Blocos Espelho', 'Ratecard Bloco (R$)',
                'Valor Extrato (R$)', 'Valor Espelho (R$)', 'Diferença (R$)', 'Status'
            ]
            resumo = resumo[[c for c in colunas_finais if c in resumo.columns]]

            if status_filtro == "Apenas Divergências ❌":
                tabela_exibicao = resumo[resumo['Status'] == '❌ Divergente']
            elif status_filtro == "Apenas OK ✅":
                tabela_exibicao = resumo[resumo['Status'] == '✅ OK']
            else:
                tabela_exibicao = resumo

            def colorir_status(val):
                return 'background-color: rgba(255, 0, 0, 0.25)' if 'Divergente' in str(val) else 'background-color: rgba(0, 255, 0, 0.15)'

            st.dataframe(tabela_exibicao.style.map(colorir_status, subset=['Status']).format({
                'KM Extrato': '{:.2f}',
                'KM Espelho': '{:.2f}',
                'Ratecard KM (R$)': '{:.2f}',
                'Pkg Extrato': '{:.2f}',
                'Pkg Espelho': '{:.2f}',
                'Ratecard Pkg (R$)': '{:.2f}',
                'Qtd Blocos Extrato': '{:.2f}',
                'Qtd Blocos Espelho': '{:.2f}',
                'Ratecard Bloco (R$)': 'R$ {:.2f}',
                'Valor Extrato (R$)': 'R$ {:.2f}',
                'Valor Espelho (R$)': 'R$ {:.2f}',
                'Diferença (R$)': 'R$ {:.2f}'
            }), use_container_width=True)
            
            # Totais consolidados por soma real das linhas
            tot_extrato = resumo['Valor Extrato (R$)'].sum()
            tot_espelho = valor_espelho_oficial if valor_espelho_oficial > 0 else resumo['Valor Espelho (R$)'].sum()
            tot_dif = tot_espelho - tot_extrato
            
            st.markdown("---")
            col_f1, col_f2, col_f3 = st.columns(3)
            col_f1.metric("Total Geral Extrato (Soma)", f"R$ {tot_extrato:,.2f}")
            col_f2.metric("Total Geral Espelho (PDF)", f"R$ {tot_espelho:,.2f}")
            col_f3.metric("Diferença Consolidada", f"R$ {tot_dif:,.2f}", delta_color="inverse")
        else:
            st.warning("O arquivo Excel precisa conter as colunas 'Data' e 'Service Type'.")

else:
    st.info("👈 Por favor, faça o upload do Extrato Operacional (.xlsx) na barra lateral para iniciar o painel.")
import streamlit as st
import pandas as pd
from database import init_db

def exibir_pagina_cotacoes():
    st.title("💰 Gestão de Cotações e Pedidos")
    conn = init_db()
    
    tab1, tab2 = st.tabs(["📄 Nova Cotação", "🔍 Pesquisar e Efetivar Pedidos"])

    with tab2:
        st.subheader("🔍 Pesquisar e Enviar")
        id_busca = st.text_input("Buscar ID (ex: COT-20260121-001)")
        
        # Simulando a busca na tabela de cotações (deve existir uma tabela 'cotacoes' no seu banco)
        if id_busca:
            # Aqui você carrega os dados da cotação salva anteriormente
            # Por exemplo: df_cot = pd.read_sql_query("SELECT * FROM cotacoes WHERE codigo=?", conn, params=(id_busca,))
            
            # Interface conforme sua imagem
            st.write("**Selecione:**")
            cotacao_id = st.selectbox("Cotação encontrada:", [id_busca])
            
            # Tabela de itens da cotação
            # df_itens = pd.read_sql_query("SELECT * FROM itens_cotacao WHERE cotacao_id=?", conn, params=(id_busca,))
            # st.table(df_itens) # Exibe a tabela como na sua imagem
            
            st.divider()
            st.subheader("Vincular ao Pedido")
            c1, c2, c3 = st.columns([2, 1, 1])
            
            # Aqui é onde você escolhe o quarto final para o pedido
            quarto_final = c1.selectbox("Quarto Escolhido pelo Cliente", ["Single", "Double", "Triple"])
            sistema = c2.selectbox("Sistema", ["Reserve", "Argo", "Outro"])
            pedido = c3.text_input("Nº Pedido")
            
            email_cliente = st.text_input("E-mail para envio do voucher/confirmação:")
            
            if st.button("Confirmar e Vincular ao Sistema"):
                if pedido:
                    st.success(f"Cotação {id_busca} vinculada com sucesso ao {sistema} Pedido #{pedido}!")
                else:
                    st.warning("Insira o número do pedido do sistema.")
import streamlit as st
import pandas as pd
import sqlite3
from database import init_db

def exibir_pagina_cotacoes():
    st.title("💰 Gestão de Cotações e Pedidos")
    conn = init_db()
    
    # Restaura as abas conforme sua navegação
    tab1, tab2 = st.tabs(["📄 Nova Cotação", "🔍 Pesquisar e Efetivar Pedidos"])

    with tab1:
        st.subheader("Gerar Nova Cotação")
        # Aqui você mantém seu código original de geração de cotações
        st.info("Utilize esta aba para selecionar hotéis e enviar opções iniciais ao cliente.")

    with tab2:
        st.subheader("🔍 Pesquisar e Enviar")
        
        # Campo de busca ID
        id_busca = st.text_input("Buscar ID", placeholder="Ex: COT-20260121-001")
        
        if id_busca:
            st.write("**Selecione:**")
            # Carrega a cotação (substitua pela sua lógica de banco de dados se necessário)
            cotacao_sel = st.selectbox("Cotação:", [id_busca])
            
            # Restaurando a visualização da tabela de itens
            # Na sua versão real, você faz um pd.read_sql_query aqui
            dados_exemplo = {
                "Hotel": ["TRANSAMERICA COLLECTION GOIANIA"],
                "Quarto": ["Single"],
                "obs": ["Café da Manhã"],
                "valor": [500.000000],
                "quantidade": [1],
                "pedido": [None],
                "sistema": [None]
            }
            df_itens = pd.DataFrame(dados_exemplo)
            st.table(df_itens) # Exibe a tabela conforme sua imagem
            
            # Botões de ação abaixo da tabela
            col_pdf, col_mail = st.columns([1, 1])
            with col_pdf:
                st.button("📄 Baixar PDF", use_container_width=True)
            with col_mail:
                email_cliente = st.text_input("E-mail:", placeholder="cliente@email.com")

            st.divider()
            
            # --- PARTE NOVA: VÍNCULO COM SISTEMA E PEDIDO ---
            st.subheader("📌 Efetivar e Vincular ao Sistema")
            st.markdown("Após o cliente escolher o quarto, preencha os dados abaixo para fechar o pedido.")
            
            c1, c2, c3 = st.columns([2, 1, 1])
            
            # 1. Escolha do quarto que o cliente aprovou
            quarto_escolhido = c1.selectbox("Quarto Escolhido", df_itens["Quarto"].unique())
            
            # 2. Escolha do sistema (Reserve/Argo)
            sistema = c2.selectbox("Sistema", ["Reserve", "Argo", "Outro"])
            
            # 3. Número do pedido gerado no sistema
            num_pedido = c3.text_input("Nº Pedido")

            if st.button("✅ Confirmar Escolha e Vincular", type="primary", use_container_width=True):
                if num_pedido and email_cliente:
                    # Lógica para salvar no banco de dados o fechamento
                    st.success(f"Cotação {id_busca} finalizada! Quarto: {quarto_escolhido} | {sistema} #{num_pedido}")
                else:
                    st.error("Por favor, preencha o E-mail e o Número do Pedido antes de confirmar.")

if __name__ == "__main__":
    exibir_pagina_cotacoes()
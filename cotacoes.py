import streamlit as st
import pandas as pd
import sqlite3
from database import init_db

def exibir_pagina_cotacoes():
    st.title("💰 Gestão de Cotações e Pedidos")
    conn = init_db()
    
    # Abas conforme a sua imagem
    tab1, tab2 = st.tabs(["📄 Nova Cotação", "🔍 Pesquisar e Efetivar Pedidos"])

    # --- ABA 1: NOVA COTAÇÃO ---
    with tab1:
        st.subheader("Gerar Nova Cotação")
        # Aqui deve ficar a sua lógica existente de criação de novas cotações
        st.info("Utilize esta aba para selecionar hotéis e enviar opções iniciais ao cliente.")

    # --- ABA 2: PESQUISAR E EFETIVAR (SISTEMA E PEDIDO) ---
    with tab2:
        st.subheader("🔍 Pesquisar e Enviar")
        
        # Campo de busca por ID
        id_busca = st.text_input("Buscar ID", placeholder="Ex: COT-20260121-001")
        
        # Simulação de carregamento de dados do banco de dados
        # Na prática, aqui você faria um SELECT na sua tabela de cotações salvas
        if id_busca:
            st.write("**Selecione:**")
            # Seletor da cotação encontrada
            cotacao_sel = st.selectbox("Cotação:", [id_busca])
            
            # Tabela de itens da cotação
            # Estes dados viriam do seu banco de dados baseado no id_busca
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
            st.table(df_itens)
            
            # Botão de PDF e Campo de E-mail
            col_pdf, col_mail = st.columns([1, 1])
            col_pdf.button("📄 Baixar PDF", use_container_width=True)
            email_cliente = col_mail.text_input("E-mail:")

            st.divider()
            
            # SEÇÃO DE VÍNCULO (Onde você efetiva o pedido)
            st.subheader("📌 Efetivar e Vincular ao Sistema")
            c1, c2, c3 = st.columns([2, 1, 1])
            
            # Campos para vincular a escolha do cliente ao pedido oficial
            quarto_final = c1.selectbox("Confirmar Quarto Escolhido", ["Single", "Double", "Triple", "Standard"])
            sistema_origem = c2.selectbox("Sistema", ["Reserve", "Argo", "Outro"])
            numero_pedido = c3.text_input("Nº Pedido")

            if st.button("✅ Confirmar Vínculo e Finalizar", type="primary", use_container_width=True):
                if numero_pedido and email_cliente:
                    # Aqui você faria o UPDATE no banco de dados para salvar o sistema e o número do pedido
                    st.success(f"Sucesso! Cotação {id_busca} vinculada ao {sistema_origem} (Pedido #{numero_pedido}).")
                else:
                    st.warning("Por favor, preencha o número do pedido e o e-mail para finalizar.")

# Execução principal
if __name__ == "__main__":
    exibir_pagina_cotacoes()
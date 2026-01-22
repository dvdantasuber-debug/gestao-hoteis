import streamlit as st
import pandas as pd
from database import init_db

def exibir_pagina_clientes():
    st.title("👥 Gestão de Clientes")
    conn = init_db()
    if not conn: return

    tab1, tab2 = st.tabs(["🏢 Grupos Econômicos", "🏢 Empresas Clientes"])

    with tab1:
        st.subheader("Cadastrar Novo Grupo")
        with st.form("form_grupo", clear_on_submit=True):
            nome_grupo = st.text_input("Nome do Grupo Econômico")
            if st.form_submit_button("Salvar Grupo"):
                if nome_grupo:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO grupos_economicos (nome) VALUES (%s)", (nome_grupo,))
                        conn.commit()
                        st.success("Grupo cadastrado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("Digite o nome do grupo.")

    with tab2:
        st.subheader("Cadastrar Nova Empresa")
        # Busca grupos para o selectbox
        df_grupos = pd.read_sql_query("SELECT id, nome FROM grupos_economicos ORDER BY nome", conn)
        
        with st.form("form_empresa", clear_on_submit=True):
            grupo_nome = st.selectbox("Selecione o Grupo", [""] + df_grupos['nome'].tolist())
            nome_empresa = st.text_input("Nome da Empresa")
            email_contato = st.text_input("E-mail para Cotações")
            
            if st.form_submit_button("Salvar Empresa"):
                if grupo_nome and nome_empresa:
                    g_id = df_grupos[df_grupos['nome'] == grupo_nome]['id'].values[0]
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO empresas_clientes (grupo_id, nome, email) VALUES (%s, %s, %s)", 
                                 (int(g_id), nome_empresa, email_contato))
                    conn.commit()
                    st.success("Empresa cadastrada!")
                    st.rerun()

        st.divider()
        st.subheader("Lista de Clientes")
        query = """
            SELECT e.nome as "Empresa", g.nome as "Grupo", e.email as "Email"
            FROM empresas_clientes e
            JOIN grupos_economicos g ON e.grupo_id = g.id
            ORDER BY g.nome, e.nome
        """
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma empresa cadastrada ainda.")
    
    conn.close()
import streamlit as st
import pandas as pd
from database import init_db

def exibir_pagina_clientes():
    st.title("👥 Gestão de Clientes")
    conn = init_db()
    
    if 'edit_id' not in st.session_state: st.session_state.edit_id = None
    
    tab1, tab2 = st.tabs(["🏢 Empresas", "📂 Grupos Econômicos"])

    with tab1:
        c_form, c_lista = st.columns([1, 2])
        
        with c_form:
            st.subheader("Cadastro")
            dados = {"n": "", "g": 0, "e": "", "c": ""}
            if st.session_state.edit_id:
                res = conn.execute("SELECT * FROM empresas_clientes WHERE id=?", (st.session_state.edit_id,)).fetchone()
                if res: dados = {"n": res[1], "g": res[2], "e": res[3], "c": res[4]}

            nome = st.text_input("Empresa", value=dados["n"])
            grupos = pd.read_sql_query("SELECT id, nome FROM grupos_economicos", conn)
            g_list = [""] + grupos['nome'].tolist()
            g_idx = g_list.index(grupos[grupos['id']==dados['g']]['nome'].iloc[0]) if dados['g'] else 0
            grupo_sel = st.selectbox("Grupo", g_list, index=g_idx)
            email = st.text_input("E-mail", value=dados["e"])
            cnpj = st.text_input("CNPJ", value=dados["c"])

            if st.button("Salvar", type="primary", use_container_width=True):
                g_id = grupos[grupos['nome'] == grupo_sel]['id'].values[0]
                if st.session_state.edit_id:
                    conn.execute("UPDATE empresas_clientes SET nome=?, grupo_id=?, email=?, cnpj=? WHERE id=?", (nome, int(g_id), email, cnpj, st.session_state.edit_id))
                else:
                    conn.execute("INSERT INTO empresas_clientes (nome, grupo_id, email, cnpj) VALUES (?,?,?,?)", (nome, int(g_id), email, cnpj))
                conn.commit(); st.session_state.edit_id = None; st.rerun()
            if st.session_state.edit_id and st.button("Cancelar"):
                st.session_state.edit_id = None; st.rerun()

        with c_lista:
            st.subheader("Empresas Cadastradas")
            df = pd.read_sql_query("SELECT e.id, e.nome as Empresa, g.nome as Grupo, e.email as Email FROM empresas_clientes e JOIN grupos_economicos g ON e.grupo_id = g.id", conn)
            st.dataframe(df[["Empresa", "Grupo", "Email"]], use_container_width=True, hide_index=True)
            
            sel_e = st.selectbox("Gerenciar:", [""] + df['Empresa'].tolist())
            if sel_e:
                row = df[df['Empresa'] == sel_e].iloc[0]
                col_e, col_d = st.columns(2)
                if col_e.button("✏️ Editar", use_container_width=True):
                    st.session_state.edit_id = row['id']; st.rerun()
                if col_d.button("🗑️ Excluir", use_container_width=True):
                    conn.execute("DELETE FROM empresas_clientes WHERE id=?", (int(row['id']),))
                    conn.commit(); st.rerun()

    with tab2:
        st.subheader("📂 Grupos")
        novo_g = st.text_input("Nome do Grupo")
        if st.button("Adicionar Grupo"):
            conn.execute("INSERT INTO grupos_economicos (nome) VALUES (?)", (novo_g,))
            conn.commit(); st.rerun()
        df_g = pd.read_sql_query("SELECT nome FROM grupos_economicos", conn)
        st.dataframe(df_g, use_container_width=True)
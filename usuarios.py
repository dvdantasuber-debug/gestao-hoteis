import streamlit as st
import pandas as pd
from database import init_db
from seguranca import hash_senha, registrar_log

def exibir_usuarios():
    st.title("👥 Gestão de Usuários")
    conn = init_db()
    
    with st.expander("➕ Cadastrar Novo Usuário"):
        with st.form("form_user"):
            n = st.text_input("Nome Completo")
            l = st.text_input("Login")
            s = st.text_input("Senha", type="password")
            nv = st.selectbox("Nível", ["Operador", "Admin"])
            if st.form_submit_button("Gravar Usuário"):
                if n and l and s:
                    try:
                        conn.execute("INSERT INTO usuarios (nome, login, senha, nivel) VALUES (?,?,?,?)", 
                                     (n, l, hash_senha(s), nv))
                        conn.commit()
                        registrar_log("INSERÇÃO", "usuarios", 0, f"Usuário {l} criado")
                        st.success("Usuário cadastrado!")
                    except: st.error("Login já em uso.")
                else: st.warning("Preencha todos os campos.")

    st.subheader("Lista de Acesso")
    users = pd.read_sql_query("SELECT id, nome, login, nivel FROM usuarios", conn)
    st.dataframe(users, use_container_width=True, hide_index=True)
    
    if st.button("🗑️ Limpar logs antigos"):
        conn.execute("DELETE FROM logs WHERE data_hora < date('now', '-30 days')")
        conn.commit()
        st.toast("Logs com mais de 30 dias removidos.")
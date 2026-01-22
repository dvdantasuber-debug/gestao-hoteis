import streamlit as st
import pandas as pd
import hashlib
from database import init_db

def gerar_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def exibir_usuarios():
    st.subheader("👥 Gestão de Usuários")
    conn = init_db()
    if not conn:
        st.error("Não foi possível conectar ao banco de dados.")
        return

    try:
        tab1, tab2 = st.tabs(["➕ Novo Usuário", "🗑️ Remover Usuário"])

        with tab1:
            with st.form("form_novo_user", clear_on_submit=True):
                novo_login = st.text_input("Login")
                nova_senha = st.text_input("Senha", type="password")
                if st.form_submit_button("Cadastrar"):
                    if novo_login and nova_senha:
                        cursor = conn.cursor()
                        # PostgreSQL usa %s em vez de ?
                        cursor.execute("INSERT INTO usuarios (login, senha) VALUES (%s, %s)", 
                                     (novo_login, gerar_hash(nova_senha)))
                        conn.commit()
                        st.success(f"Usuário {novo_login} cadastrado!")
                        st.rerun()
                    else:
                        st.warning("Preencha todos os campos.")

        with tab2:
            # PostgreSQL exige %s e não aceita ?
            users_df = pd.read_sql_query("SELECT login FROM usuarios", conn)
            users_list = users_df['login'].tolist()
            
            if users_list:
                user_para_remover = st.selectbox("Selecione o usuário para remover", users_list)
                if st.button("Remover Usuário", type="secondary"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM usuarios WHERE login = %s", (user_para_remover,))
                    conn.commit()
                    st.success(f"Usuário {user_para_remover} removido!")
                    st.rerun()
            else:
                st.info("Nenhum usuário cadastrado.")
                
    except Exception as e:
        st.error(f"Erro ao processar usuários: {e}")
    finally:
        # Importante: fechar a conexão com o Pooler
        conn.close()
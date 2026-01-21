import streamlit as st
import pandas as pd
from database import init_db
from seguranca import hash_senha, registrar_log

def exibir_usuarios():
    st.title("👥 Gestão de Usuários")
    conn = init_db()
    
    # 1. ABA DE CADASTRO
    with st.expander("➕ Cadastrar Novo Usuário"):
        with st.form("form_user"):
            n = st.text_input("Nome Completo")
            l = st.text_input("Login")
            s = st.text_input("Senha", type="password")
            nv = st.selectbox("Nível", ["Operador", "Admin"])
            if st.form_submit_button("Gravar Usuário"):
                if n and l and s:
                    try:
                        senha_crip = hash_senha(s)
                        conn.execute("INSERT INTO usuarios (nome, login, senha, nivel) VALUES (?,?,?,?)", 
                                     (n, l, senha_crip, nv))
                        conn.commit()
                        registrar_log("INSERÇÃO", f"Usuário {l} criado")
                        st.success(f"Usuário {l} cadastrado com sucesso!")
                    except Exception as e: 
                        st.error(f"Erro: O login '{l}' já pode estar em uso.")
                else: 
                    st.warning("Preencha todos os campos.")

    # 2. ABA DE ALTERAÇÃO DE SENHA
    with st.expander("🔑 Alterar Senha de Usuário Existente"):
        # Busca usuários para o selectbox
        users_list = pd.read_sql_query("SELECT login FROM usuarios", conn)['login'].tolist()
        
        with st.form("form_change_pass"):
            u_sel = st.selectbox("Selecione o Usuário", users_list)
            nova_s = st.text_input("Nova Senha", type="password")
            conf_s = st.text_input("Confirme a Nova Senha", type="password")
            
            if st.form_submit_button("Atualizar Senha"):
                if nova_s == conf_s and nova_s != "":
                    nova_s_hash = hash_senha(nova_s)
                    conn.execute("UPDATE usuarios SET senha = ? WHERE login = ?", (nova_s_hash, u_sel))
                    conn.commit()
                    registrar_log("ALTERAÇÃO", f"Senha do usuário {u_sel} alterada")
                    st.success(f"Senha de '{u_sel}' atualizada!")
                elif nova_s != conf_s:
                    st.error("As senhas não coincidem.")
                else:
                    st.warning("A senha não pode estar vazia.")

    # 3. LISTA DE USUÁRIOS E EXCLUSÃO
    st.subheader("Lista de Acesso")
    users = pd.read_sql_query("SELECT id, nome, login, nivel FROM usuarios", conn)
    
    # Exibe a tabela
    st.dataframe(users, use_container_width=True, hide_index=True)
    
    # Opção de exclusão
    st.divider()
    col1, col2 = st.columns([2, 1])
    with col1:
        u_del = st.selectbox("Selecionar usuário para remover", [""] + users['login'].tolist())
    with col2:
        st.write("") # Alinhamento
        if st.button("🗑️ Excluir Usuário", use_container_width=True):
            if u_del != "" and u_del != "admin": # Proteção para não apagar o admin principal
                conn.execute("DELETE FROM usuarios WHERE login = ?", (u_del,))
                conn.commit()
                registrar_log("EXCLUSÃO", f"Usuário {u_del} removido")
                st.success(f"Usuário {u_del} removido.")
                st.rerun()
            elif u_del == "admin":
                st.error("O utilizador 'admin' não pode ser removido por segurança.")
            else:
                st.warning("Selecione um usuário.")
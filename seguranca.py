import sqlite3
import hashlib
import streamlit as st
from datetime import datetime

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def registrar_log(acao, detalhe):
    try:
        usuario = st.session_state.get('usuario_nome', 'Sistema')
        conn = sqlite3.connect('gestao_hoteis.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS logs 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, data_hora TEXT, usuario TEXT, acao TEXT, detalhe TEXT)''')
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        cursor.execute("INSERT INTO logs (data_hora, usuario, acao, detalhe) VALUES (?, ?, ?, ?)",
                       (agora, usuario, acao, detalhe))
        conn.commit()
        conn.close()
    except: pass

def login_usuario(usuario, senha):
    conn = sqlite3.connect('gestao_hoteis.db')
    senha_hash = hash_senha(senha)
    cursor = conn.cursor()
    cursor.execute("SELECT nome, nivel FROM usuarios WHERE login = ? AND senha = ?", (usuario, senha_hash))
    user = cursor.fetchone()
    conn.close()

    if user:
        st.session_state.usuario_nome = user[0]
        st.session_state.usuario_nivel = user[1]
        st.session_state.autenticado = True
        registrar_log("Login", f"Utilizador {usuario} entrou")
        return True
    return False

def logout_usuario():
    st.session_state.autenticado = False
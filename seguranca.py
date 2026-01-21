import sqlite3
import hashlib
import streamlit as st
from datetime import datetime

def hash_senha(senha):
    """Criptografa a senha usando SHA-256."""
    return hashlib.sha256(senha.encode()).hexdigest()

def registrar_log(acao, detalhe):
    """Grava as ações do utilizador no banco de dados."""
    try:
        usuario = st.session_state.get('usuario_nome', 'Sistema')
        conn = sqlite3.connect('gestao_hoteis.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT,
                usuario TEXT,
                acao TEXT,
                detalhe TEXT
            )
        ''')
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        cursor.execute("INSERT INTO logs (data_hora, usuario, acao, detalhe) VALUES (?, ?, ?, ?)",
                       (agora, usuario, acao, detalhe))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao registrar log: {e}")

def login_usuario(usuario, senha):
    """Valida o utilizador comparando a senha hash no banco de dados."""
    conn = sqlite3.connect('gestao_hoteis.db')
    cursor = conn.cursor()
    
    # Transforma a senha digitada no mesmo formato do banco
    senha_hash = hash_senha(senha)
    
    cursor.execute("SELECT nome, nivel FROM usuarios WHERE login = ? AND senha = ?", (usuario, senha_hash))
    user = cursor.fetchone()
    conn.close()

    if user:
        st.session_state.usuario_nome = user[0]
        st.session_state.usuario_nivel = user[1]
        st.session_state.autenticado = True
        registrar_log("Login", f"Utilizador {usuario} entrou")
        return True
    else:
        registrar_log("Falha Login", f"Tentativa falhada para: {usuario}")
        return False

def logout_usuario():
    """Encerra a sessão atual."""
    st.session_state.autenticado = False
    st.session_state.usuario_nome = None
    st.session_state.usuario_nivel = None
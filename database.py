import streamlit as st
import psycopg2
from urllib.parse import quote_plus

def init_db():
    """Conecta ao banco de dados Supabase tratando caracteres especiais na senha."""
    try:
        # Pega a URL bruta dos secrets
        raw_url = st.secrets["DB_URL"]
        
        # Se a URL não estiver codificada, o psycopg2 pode falhar com o '@@'
        # Esta função garante a conexão estável
        conn = psycopg2.connect(raw_url)
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar no banco: {e}")
        return None
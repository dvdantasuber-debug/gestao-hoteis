import streamlit as st
import psycopg2
from psycopg2.extras import DictCursor

def init_db():
    try:
        # Conecta usando a URL dos Secrets
        conn = psycopg2.connect(st.secrets["DB_URL"])
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar no banco: {e}")
        return None

def criar_tabelas():
    conn = init_db()
    cursor = conn.cursor()
    
    # Criar tabela de hotéis (Exemplo de sintaxe Postgres)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hoteis (
            id SERIAL PRIMARY KEY,
            nome_comercial TEXT NOT NULL,
            razao_social TEXT,
            cnpj TEXT,
            cidade TEXT,
            estado TEXT,
            pais TEXT,
            cep TEXT,
            logradouro TEXT,
            numero TEXT,
            latitude TEXT,
            longitude TEXT
        )
    """)
    
    # Tabela de Cotações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cotacoes (
            id SERIAL PRIMARY KEY,
            identificador TEXT UNIQUE,
            grupo TEXT,
            empresa TEXT,
            evento TEXT,
            checkin DATE,
            checkout DATE,
            cidade TEXT,
            estado TEXT
        )
    """)
    
    # Tabela de Itens da Cotação (Onde salvamos o Pedido e Sistema)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cotacao_hoteis (
            id SERIAL PRIMARY KEY,
            cotacao_id INTEGER REFERENCES cotacoes(id),
            hotel_id INTEGER REFERENCES hoteis(id),
            quarto_tipo TEXT,
            valor DECIMAL,
            quantidade INTEGER,
            pedido TEXT,
            sistema TEXT
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
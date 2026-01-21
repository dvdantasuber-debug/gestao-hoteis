import sqlite3
import hashlib

def init_db():
    """Inicializa o banco de dados e cria todas as tabelas necessárias."""
    conn = sqlite3.connect('gestao_hoteis.db', check_same_thread=False)
    cursor = conn.cursor()

    # 1. Tabela de Grupos Económicos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grupos_economicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    ''')

    # 2. Tabela de Empresas Clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empresas_clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            grupo_id INTEGER,
            email TEXT,
            cnpj TEXT,
            FOREIGN KEY (grupo_id) REFERENCES grupos_economicos (id)
        )
    ''')

    # 3. Tabela de Hotéis
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hoteis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_comercial TEXT NOT NULL,
            razao_social TEXT,
            cnpj TEXT,
            cidade TEXT,
            estado TEXT,
            pais TEXT,
            latitude TEXT,
            longitude TEXT,
            cep TEXT,
            tipo_logradouro TEXT,
            logradouro TEXT,
            numero TEXT,
            bairro TEXT,
            complemento TEXT
        )
    ''')

    # 4. Tabela de Acomodações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS acomodacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_id INTEGER,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            obs TEXT,
            FOREIGN KEY (hotel_id) REFERENCES hoteis (id)
        )
    ''')

    # 5. Tabela de Cotações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cotacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identificador TEXT NOT NULL UNIQUE,
            grupo TEXT,
            empresa TEXT,
            evento TEXT,
            checkin TEXT,
            checkout TEXT,
            cidade TEXT,
            estado TEXT
        )
    ''')

    # 6. Tabela de Itens da Cotação
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cotacao_hoteis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cotacao_id INTEGER,
            hotel_id INTEGER,
            quarto_tipo TEXT,
            valor REAL,
            quantidade INTEGER,
            pedido TEXT,
            sistema TEXT,
            FOREIGN KEY (cotacao_id) REFERENCES cotacoes (id),
            FOREIGN KEY (hotel_id) REFERENCES hoteis (id)
        )
    ''')

    # 7. Tabela de Usuários (Segurança)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            nivel TEXT NOT NULL
        )
    ''')

    # Criar Admin padrão (Login: admin / Senha: 123) se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        # Senha "123" convertida para SHA-256
        senha_hash = hashlib.sha256('123'.encode()).hexdigest()
        cursor.execute("INSERT INTO usuarios (nome, login, senha, nivel) VALUES (?, ?, ?, ?)",
                       ('Administrador', 'admin', senha_hash, 'Admin'))

    conn.commit()
    return conn
import sqlite3

def atualizar_tabela():
    conn = sqlite3.connect('gestao_hoteis.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE empresas_clientes ADD COLUMN email TEXT")
        conn.commit()
        print("Coluna 'email' adicionada com sucesso!")
    except sqlite3.OperationalError:
        print("A coluna 'email' já existe ou a tabela não foi encontrada.")
    finally:
        conn.close()

if __name__ == "__main__":
    atualizar_tabela()
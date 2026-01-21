import sqlite3

def consertar_banco():
    conn = sqlite3.connect('gestao_hoteis.db')
    cursor = conn.cursor()
    
    # Lista de colunas que devem existir na tabela empresas_clientes
    colunas_necessarias = [
        ("email", "TEXT"),
        ("cnpj", "TEXT")
    ]
    
    for nome_coluna, tipo_coluna in colunas_necessarias:
        try:
            cursor.execute(f"ALTER TABLE empresas_clientes ADD COLUMN {nome_coluna} {tipo_coluna}")
            print(f"Coluna '{nome_coluna}' adicionada com sucesso!")
        except sqlite3.OperationalError:
            print(f"Coluna '{nome_coluna}' já existe, pulando...")

    conn.commit()
    conn.close()
    print("--- Manutenção concluída! ---")

if __name__ == "__main__":
    consertar_banco()
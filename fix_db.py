import sqlite3

def migrar_completo():
    conn = sqlite3.connect('gestao_hoteis.db')
    cursor = conn.cursor()
    
    # Colunas faltantes em Hoteis
    try:
        cursor.execute("ALTER TABLE hoteis ADD COLUMN estado TEXT")
    except: pass
    
    # Colunas faltantes em Cotacoes
    colunas_cot = [("pais", "TEXT"), ("estado", "TEXT"), ("cidade", "TEXT"), 
                   ("checkin", "TEXT"), ("checkout", "TEXT")]
    
    for nome, tipo in colunas_cot:
        try:
            cursor.execute(f"ALTER TABLE cotacoes ADD COLUMN {nome} {tipo}")
        except: pass
            
    conn.commit()
    conn.close()
    print("Banco de dados pronto!")

if __name__ == "__main__":
    migrar_completo()
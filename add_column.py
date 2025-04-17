import sqlite3

def add_column():
    conn = sqlite3.connect('abordagens.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('ALTER TABLE abordagem ADD COLUMN endereco_residencia VARCHAR(200)')
        conn.commit()
        print("Coluna endereco_residencia adicionada com sucesso!")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("A coluna endereco_residencia já existe.")
        else:
            print(f"Erro ao adicionar coluna: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_column() 
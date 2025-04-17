import sqlite3
import os

# Caminho para o banco de dados
db_path = 'abordagens.db'

# Verificar se o arquivo existe
if not os.path.exists(db_path):
    print(f"O arquivo {db_path} não existe!")
    exit(1)

# Conectar ao banco de dados
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Obter informações sobre a tabela de usuários
cursor.execute("PRAGMA table_info(user)")
columns = cursor.fetchall()

print("Estrutura da tabela 'user':")
print("-" * 50)
print(f"{'ID':<5} {'Nome':<20} {'Tipo':<15} {'Nullable':<10} {'Default':<10} {'PK':<5}")
print("-" * 50)

for col in columns:
    cid, name, type_, notnull, default, pk = col
    print(f"{cid:<5} {name:<20} {type_:<15} {'No' if notnull else 'Yes':<10} {str(default):<10} {'Yes' if pk else 'No':<5}")

# Verificar se existem usuários no banco
cursor.execute("SELECT COUNT(*) FROM user")
count = cursor.fetchone()[0]
print(f"\nTotal de usuários no banco: {count}")

# Fechar a conexão
conn.close() 
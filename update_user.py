from app import app, db, User
from datetime import datetime

with app.app_context():
    # Buscar o usuário existente
    user = User.query.first()
    
    if user:
        # Atualizar os campos
        user.is_active = True
        user.nivel_acesso = 'admin'
        user.data_criacao = datetime.utcnow()
        user.is_admin = True
        
        # Salvar as alterações
        db.session.commit()
        print("Usuário atualizado com sucesso!")
        print(f"ID: {user.id}")
        print(f"Nome: {user.nome}")
        print(f"Email: {user.email}")
        print(f"Cargo: {user.cargo}")
        print(f"Nível de Acesso: {user.nivel_acesso}")
        print(f"Status: {'Ativo' if user.is_active else 'Inativo'}")
        print(f"Admin: {'Sim' if user.is_admin else 'Não'}")
        print(f"Data de Criação: {user.data_criacao}")
    else:
        print("Nenhum usuário encontrado no banco de dados.") 
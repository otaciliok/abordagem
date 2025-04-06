import os
import shutil
from datetime import datetime
import subprocess
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_backup():
    try:
        # Criar diretório de backup com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f'backup_{timestamp}'
        os.makedirs(backup_dir, exist_ok=True)
        logging.info(f'Diretório de backup criado: {backup_dir}')
        
        # Arquivos e diretórios para backup
        items_to_backup = [
            'app.py',
            'requirements.txt',
            'README.md',
            'templates',
            'static',
            'instance'
        ]
        
        # Copiar arquivos e diretórios
        for item in items_to_backup:
            if os.path.exists(item):
                if os.path.isdir(item):
                    shutil.copytree(item, os.path.join(backup_dir, item))
                    logging.info(f'Diretório copiado: {item}')
                else:
                    shutil.copy2(item, backup_dir)
                    logging.info(f'Arquivo copiado: {item}')
            else:
                logging.warning(f'Item não encontrado: {item}')
        
        # Salvar versões das dependências
        pip_freeze_path = os.path.join(backup_dir, 'pip_freeze.txt')
        with open(pip_freeze_path, 'w') as f:
            subprocess.run(['pip', 'freeze'], stdout=f)
        logging.info('Dependências salvas em pip_freeze.txt')
        
        print(f'Backup criado com sucesso em: {backup_dir}')
        return backup_dir
    except Exception as e:
        logging.error(f'Erro ao criar backup: {str(e)}')
        raise

if __name__ == '__main__':
    try:
        backup_dir = create_backup()
        print(f'Backup concluído com sucesso em: {backup_dir}')
    except Exception as e:
        print(f'Erro ao executar backup: {str(e)}') 
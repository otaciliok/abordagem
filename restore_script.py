import os
import shutil
import subprocess
import sys

def restore_backup(backup_dir):
    if not os.path.exists(backup_dir):
        print(f'Diretório de backup não encontrado: {backup_dir}')
        return False
    
    # Restaurar arquivos e diretórios
    items_to_restore = [
        'app.py',
        'requirements.txt',
        'README.md',
        'templates',
        'static',
        'instance'
    ]
    
    for item in items_to_restore:
        backup_path = os.path.join(backup_dir, item)
        if os.path.exists(backup_path):
            if os.path.isdir(backup_path):
                if os.path.exists(item):
                    shutil.rmtree(item)
                shutil.copytree(backup_path, item)
            else:
                shutil.copy2(backup_path, item)
    
    # Restaurar dependências
    pip_freeze_path = os.path.join(backup_dir, 'pip_freeze.txt')
    if os.path.exists(pip_freeze_path):
        print('Restaurando dependências...')
        subprocess.run(['pip', 'install', '-r', pip_freeze_path])
    
    print('Backup restaurado com sucesso!')
    return True

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Uso: python restore_script.py <diretório_de_backup>')
        sys.exit(1)
    
    backup_dir = sys.argv[1]
    restore_backup(backup_dir) 
# Sistema de Registro de Abordagens Policiais

Sistema web para registro e gerenciamento de abordagens policiais, desenvolvido com Flask.

## Funcionalidades

- Cadastro de abordagens com dados do indivíduo
- Upload de imagens
- Busca por nome, vulgo ou CPF
- Filtro por data
- Visualização detalhada
- Edição e exclusão de registros
- Interface responsiva e moderna
- Geração de relatórios em PDF

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone o repositório:
```bash
git clone [url-do-repositorio]
cd sistema-abordagens
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Configuração

1. Altere a chave secreta no arquivo `app.py`:
```python
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'  # Altere para uma chave secreta segura
```

2. O banco de dados SQLite será criado automaticamente na primeira execução.

## Executando o Sistema

1. Com o ambiente virtual ativado, execute:
```bash
python app.py
```

2. Acesse o sistema no navegador:
```
http://localhost:8080
```

## Estrutura do Projeto

```
sistema-abordagens/
├── app.py                 # Aplicação principal
├── requirements.txt       # Dependências
├── static/               # Arquivos estáticos
│   └── uploads/          # Pasta para imagens
├── templates/            # Templates HTML
│   ├── base.html         # Template base
│   ├── index.html        # Lista de abordagens
│   ├── nova_abordagem.html    # Formulário de cadastro
│   ├── editar_abordagem.html  # Formulário de edição
│   └── visualizar_abordagem.html  # Detalhes da abordagem
└── abordagens.db         # Banco de dados SQLite
```

## Segurança

- Todas as imagens são validadas antes do upload
- Proteção contra CSRF em todos os formulários
- Validação de dados nos formulários
- Sanitização de nomes de arquivos
- Limite de tamanho para uploads

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes. 
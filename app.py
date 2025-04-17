import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DateField, TextAreaField, SubmitField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired, Optional, Length, ValidationError, Email
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import tempfile
from dotenv import load_dotenv
from functools import wraps
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'dkj83qihx'),
    api_key=os.getenv('CLOUDINARY_API_KEY', '695527639461583'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', 'p5MJmNhADIqnLm7z5GPzbesRNeM')
)

# Inicialização do SQLAlchemy antes do app
db = SQLAlchemy()

app = Flask(__name__)

# Configuração do banco de dados
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'uma-chave-secreta-padrao'),
    SQLALCHEMY_DATABASE_URI=database_url or 'sqlite:///abordagens.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max-limit
    ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif'},
    WTF_CSRF_ENABLED=True
)

# Configuração da pasta de uploads para o Render
if os.getenv('RENDER'):
    app.config['UPLOAD_FOLDER'] = '/opt/render/project/src/static/uploads'
else:
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

# Garantir que a pasta de uploads existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicialização das extensões
csrf = CSRFProtect(app)
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Criar todas as tabelas do banco de dados
with app.app_context():
    try:
        db.create_all()
        # Executar migrações
        from flask_migrate import upgrade as _upgrade
        _upgrade()
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    nome = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acesso = db.Column(db.DateTime)
    nivel_acesso = db.Column(db.String(20), default='usuario')  # 'admin', 'supervisor', 'usuario'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Criar usuário administrador se não existir
with app.app_context():
    try:
        admin_email = "otaciliolobo@gmail.com"
        admin = User.query.filter_by(email=admin_email).first()
        
        if admin:
            # Atualizar usuário existente para administrador
            admin.is_admin = True
            admin.nivel_acesso = 'admin'
            db.session.commit()
            print("Usuário atualizado para administrador com sucesso!")
        else:
            # Criar novo usuário administrador
            admin = User(
                email=admin_email,
                nome="Otacilio Lobo",
                cargo="Administrador",
                is_admin=True,
                is_active=True,
                data_criacao=datetime.utcnow(),
                nivel_acesso='admin'
            )
            admin.set_password("Mikuafxb153")
            db.session.add(admin)
            db.session.commit()
            print("Usuário administrador criado com sucesso!")
    except Exception as e:
        print(f"Erro ao atualizar/criar usuário administrador: {e}")

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    nome = StringField('Nome Completo', validators=[DataRequired()])
    cargo = StringField('Cargo', validators=[DataRequired()])
    submit = SubmitField('Registrar')

class UserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    nome = StringField('Nome Completo', validators=[DataRequired()])
    cargo = StringField('Cargo', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[Optional()])
    nivel_acesso = SelectField('Nível de Acesso', 
                              choices=[('usuario', 'Usuário'), 
                                     ('supervisor', 'Supervisor'), 
                                     ('admin', 'Administrador')],
                              validators=[DataRequired()])
    is_active = BooleanField('Conta Ativa')
    submit = SubmitField('Salvar')

# Modelo para a tabela de abordagens
class Abordagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(100), nullable=False)
    nome_mae = db.Column(db.String(100), nullable=False)
    vulgo = db.Column(db.String(50))
    cpf = db.Column(db.String(14))
    data_nascimento = db.Column(db.Date)
    endereco_abordagem = db.Column(db.String(200), nullable=False)
    endereco_residencia = db.Column(db.String(200))
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    observacoes = db.Column(db.Text)
    imagem = db.Column(db.String(500))  # Aumentado para acomodar URLs do Cloudinary
    historico_pca = db.Column(db.String(500))  # Aumentado para acomodar URLs do Cloudinary
    alerta = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Abordagem {self.nome_completo}>'

# Formulário para cadastro de abordagem
class AbordagemForm(FlaskForm):
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=100)])
    nome_mae = StringField('Nome da Mãe', validators=[DataRequired(), Length(max=100)])
    vulgo = StringField('Vulgo', validators=[Optional(), Length(max=50)])
    cpf = StringField('CPF', validators=[Optional(), Length(max=14)])
    data_nascimento = DateField('Data de Nascimento', validators=[Optional()])
    endereco_abordagem = StringField('Endereço da Abordagem', validators=[DataRequired(), Length(max=200)])
    endereco_residencia = StringField('Endereço da Residência', validators=[Optional(), Length(max=200)])
    observacoes = TextAreaField('Observações', validators=[Optional()])
    alerta = BooleanField('Sinal de Alerta', description='Marque se este indivíduo requer atenção especial')
    imagem = FileField('Imagem', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens são permitidas!')
    ])
    historico_pca = FileField('Histórico do PCA', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens são permitidas!')
    ])
    submit = SubmitField('Salvar')
    
    def validate_cpf(self, cpf):
        # Remove caracteres não numéricos
        cpf_limpo = re.sub(r'[^0-9]', '', cpf.data)
        
        # Verifica se tem 11 dígitos
        if len(cpf_limpo) != 11:
            raise ValidationError('CPF deve conter 11 dígitos')
        
        # Verifica se todos os dígitos são iguais
        if cpf_limpo == cpf_limpo[0] * 11:
            raise ValidationError('CPF inválido')
        
        # Validação do primeiro dígito verificador
        soma = 0
        for i in range(9):
            soma += int(cpf_limpo[i]) * (10 - i)
        resto = soma % 11
        if resto < 2:
            digito1 = 0
        else:
            digito1 = 11 - resto
        
        if digito1 != int(cpf_limpo[9]):
            raise ValidationError('CPF inválido')
        
        # Validação do segundo dígito verificador
        soma = 0
        for i in range(10):
            soma += int(cpf_limpo[i]) * (11 - i)
        resto = soma % 11
        if resto < 2:
            digito2 = 0
        else:
            digito2 = 11 - resto
        
        if digito2 != int(cpf_limpo[10]):
            raise ValidationError('CPF inválido')

def allowed_file(filename):
    return True  # Temporariamente permitindo todos os arquivos

def save_image(file, prefix=''):
    if file and hasattr(file, 'filename') and file.filename:
        try:
            # Upload para o Cloudinary
            result = cloudinary.uploader.upload(
                file,
                folder="abordagens",
                public_id=f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                resource_type="auto"
            )
            # Retorna a URL da imagem
            return result.get('secure_url')
        except Exception as e:
            print(f"Erro ao fazer upload para o Cloudinary: {e}")
            return None
    return None

@app.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Filtros de busca
    search = request.args.get('search', '')
    nome_mae = request.args.get('nome_mae', '')
    abordagem_date = request.args.get('abordagem_date', '')
    
    query = Abordagem.query
    
    if search:
        query = query.filter(
            db.or_(
                Abordagem.nome_completo.ilike(f'%{search}%'),
                Abordagem.vulgo.ilike(f'%{search}%'),
                Abordagem.cpf.ilike(f'%{search}%')
            )
        )
    
    if nome_mae:
        query = query.filter(Abordagem.nome_mae.ilike(f'%{nome_mae}%'))
    
    if abordagem_date:
        try:
            abordagem_date = datetime.strptime(abordagem_date, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Abordagem.data_hora) == abordagem_date)
        except ValueError:
            pass
    
    # Ordena por data/hora mais recente
    query = query.order_by(Abordagem.data_hora.desc())
    
    # Paginação
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    abordagens = pagination.items
    
    return render_template('index.html', abordagens=abordagens, pagination=pagination)

@app.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_abordagem():
    form = AbordagemForm()
    if form.validate_on_submit():
        imagem_url = save_image(form.imagem.data, 'img')
        historico_pca_url = save_image(form.historico_pca.data, 'pca')
        
        abordagem = Abordagem(
            nome_completo=form.nome_completo.data,
            nome_mae=form.nome_mae.data,
            vulgo=form.vulgo.data,
            cpf=form.cpf.data,
            data_nascimento=form.data_nascimento.data,
            endereco_abordagem=form.endereco_abordagem.data,
            endereco_residencia=form.endereco_residencia.data,
            observacoes=form.observacoes.data,
            imagem=imagem_url,
            historico_pca=historico_pca_url
        )
        
        db.session.add(abordagem)
        db.session.commit()
        
        flash('Abordagem registrada com sucesso!', 'success')
        return redirect(url_for('index'))
    
    return render_template('nova_abordagem.html', form=form)

def supervisor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.nivel_acesso == 'usuario':
            flash('Acesso negado. Apenas supervisores e administradores podem realizar esta ação.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@supervisor_required
def editar_abordagem(id):
    abordagem = Abordagem.query.get_or_404(id)
    form = AbordagemForm(obj=abordagem)
    
    if form.validate_on_submit():
        # Preserva os valores existentes
        nome_completo = form.nome_completo.data
        nome_mae = form.nome_mae.data
        vulgo = form.vulgo.data
        cpf = form.cpf.data
        data_nascimento = form.data_nascimento.data
        endereco_abordagem = form.endereco_abordagem.data
        endereco_residencia = form.endereco_residencia.data
        observacoes = form.observacoes.data
        alerta = form.alerta.data
        
        # Processa a imagem apenas se uma nova for enviada
        if form.imagem.data and hasattr(form.imagem.data, 'filename') and form.imagem.data.filename:
            # Salva a nova imagem no Cloudinary
            imagem_url = save_image(form.imagem.data, 'img')
            if imagem_url:
                abordagem.imagem = imagem_url
        else:
            # Mantém a imagem existente
            imagem_url = abordagem.imagem
        
        # Atualiza os outros campos
        abordagem.nome_completo = nome_completo
        abordagem.nome_mae = nome_mae
        abordagem.vulgo = vulgo
        abordagem.cpf = cpf
        abordagem.data_nascimento = data_nascimento
        abordagem.endereco_abordagem = endereco_abordagem
        abordagem.endereco_residencia = endereco_residencia
        abordagem.observacoes = observacoes
        abordagem.alerta = alerta
        
        db.session.commit()
        flash('Abordagem atualizada com sucesso!', 'success')
        return redirect(url_for('visualizar_abordagem', id=id))
    
    return render_template('editar_abordagem.html', form=form, abordagem=abordagem)

@app.route('/visualizar/<int:id>')
@login_required
def visualizar_abordagem(id):
    abordagem = Abordagem.query.get_or_404(id)
    return render_template('visualizar_abordagem.html', abordagem=abordagem)

@app.route('/excluir/<int:id>', methods=['POST'])
@login_required
@supervisor_required
def excluir_abordagem(id):
    abordagem = Abordagem.query.get_or_404(id)
    
    # Remove a imagem se existir
    if abordagem.imagem:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], abordagem.imagem)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    # Remove o histórico do PCA se existir
    if abordagem.historico_pca:
        historico_path = os.path.join(app.config['UPLOAD_FOLDER'], abordagem.historico_pca)
        if os.path.exists(historico_path):
            os.remove(historico_path)
    
    db.session.delete(abordagem)
    db.session.commit()
    
    flash('Abordagem excluída com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/relatorio', methods=['GET', 'POST'])
def gerar_relatorio():
    if request.method == 'POST':
        # Obter parâmetros do formulário
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')
        nome = request.form.get('nome')
        tipo_relatorio = request.form.get('tipo_relatorio', 'simples')
        
        # Construir a consulta
        query = Abordagem.query
        
        if data_inicio and data_fim:
            try:
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
                query = query.filter(db.func.date(Abordagem.data_hora) >= data_inicio, 
                                   db.func.date(Abordagem.data_hora) <= data_fim)
            except ValueError:
                flash('Formato de data inválido', 'danger')
                return redirect(url_for('gerar_relatorio'))
        
        if nome:
            query = query.filter(Abordagem.nome_completo.ilike(f'%{nome}%'))
        
        # Ordenar por data/hora mais recente
        abordagens = query.order_by(Abordagem.data_hora.desc()).all()
        
        if not abordagens:
            flash('Nenhuma abordagem encontrada com os critérios especificados', 'warning')
            return redirect(url_for('gerar_relatorio'))
        
        # Gerar o PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centralizado
        )
        elements.append(Paragraph("Relatório de Abordagens", title_style))
        
        # Informações do relatório
        info_style = styles['Normal']
        if data_inicio and data_fim:
            elements.append(Paragraph(f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}", info_style))
        if nome:
            elements.append(Paragraph(f"Filtro por nome: {nome}", info_style))
        elements.append(Paragraph(f"Total de abordagens: {len(abordagens)}", info_style))
        elements.append(Paragraph(f"Tipo de relatório: {'Completo' if tipo_relatorio == 'completo' else 'Simples'}", info_style))
        elements.append(Spacer(1, 12))
        
        if tipo_relatorio == 'simples':
            # Relatório simples - apenas tabela com dados básicos
            # Cabeçalho da tabela
            data = [['Nome Completo', 'Nome da Mãe', 'Vulgo', 'CPF', 'Data/Hora', 'Endereço Residência', 'Endereço Abordagem']]
            
            # Dados da tabela
            for abordagem in abordagens:
                data.append([
                    abordagem.nome_completo,
                    abordagem.nome_mae,
                    abordagem.vulgo or '-',
                    abordagem.cpf or '-',
                    abordagem.data_hora.strftime('%d/%m/%Y %H:%M'),
                    abordagem.endereco_residencia or '-',
                    abordagem.endereco_abordagem
                ])
            
            # Criar e estilizar a tabela
            table = Table(data, colWidths=[1.2*inch, 1.2*inch, 0.8*inch, 0.8*inch, 1*inch, 1.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(table)
        else:
            # Relatório completo - inclui fotos e todas as informações
            for abordagem in abordagens:
                # Adiciona um separador entre abordagens
                elements.append(Spacer(1, 20))
                
                # Título da abordagem
                abordagem_title = ParagraphStyle(
                    'AbordagemTitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    spaceAfter=10,
                    textColor=colors.darkblue
                )
                elements.append(Paragraph(f"Abordagem: {abordagem.nome_completo}", abordagem_title))
                
                # Imagem principal (agora logo após o nome)
                if abordagem.imagem:
                    img_path = os.path.join(app.config['UPLOAD_FOLDER'], abordagem.imagem)
                    if os.path.exists(img_path):
                        elements.append(Spacer(1, 5))
                        elements.append(Image(img_path, width=3*inch, height=3*inch))
                        elements.append(Spacer(1, 10))
                
                # Informações básicas em uma tabela
                info_data = [
                    ['Nome Completo:', abordagem.nome_completo],
                    ['Nome da Mãe:', abordagem.nome_mae],
                    ['Vulgo:', abordagem.vulgo or '-'],
                    ['CPF:', abordagem.cpf or '-'],
                    ['Data/Hora:', abordagem.data_hora.strftime('%d/%m/%Y %H:%M')],
                    ['Endereço da Residência:', abordagem.endereco_residencia or '-'],
                    ['Endereço da Abordagem:', abordagem.endereco_abordagem]
                ]
                
                if abordagem.data_nascimento:
                    info_data.append(['Data de Nascimento:', abordagem.data_nascimento.strftime('%d/%m/%Y')])
                
                if abordagem.alerta:
                    info_data.append(['Sinal de Alerta:', 'Sim'])
                
                info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
                info_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                elements.append(info_table)
                
                # Observações
                if abordagem.observacoes:
                    elements.append(Spacer(1, 10))
                    elements.append(Paragraph("Observações:", styles['Heading3']))
                    elements.append(Paragraph(abordagem.observacoes, styles['Normal']))
                
                # Imagem do histórico do PCA
                if abordagem.historico_pca:
                    elements.append(Spacer(1, 10))
                    elements.append(Paragraph("Histórico do PCA:", styles['Heading3']))
                    pca_path = os.path.join(app.config['UPLOAD_FOLDER'], abordagem.historico_pca)
                    if os.path.exists(pca_path):
                        elements.append(Image(pca_path, width=3*inch, height=3*inch))
                    else:
                        elements.append(Paragraph("Imagem não encontrada", styles['Normal']))
                else:
                    elements.append(Spacer(1, 10))
                    elements.append(Paragraph("Histórico do PCA:", styles['Heading3']))
                    elements.append(Paragraph("Não disponível", styles['Normal']))
                
                # Adiciona uma linha divisória
                elements.append(Paragraph("<hr/>", styles['Normal']))
        
        # Construir o PDF
        doc.build(elements)
        
        # Preparar o arquivo para download
        buffer.seek(0)
        
        # Gerar nome do arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        tipo = "completo" if tipo_relatorio == "completo" else "simples"
        filename = f"relatorio_abordagens_{tipo}_{timestamp}.pdf"
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    
    return render_template('gerar_relatorio.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        flash('Email ou senha inválidos', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acesso negado. Apenas administradores podem acessar esta página.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/usuarios')
@login_required
@admin_required
def listar_usuarios():
    usuarios = User.query.order_by(User.nome).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@app.route('/admin/usuarios/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_usuario():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Este email já está registrado.', 'error')
            return render_template('admin/usuario_form.html', form=form, titulo='Novo Usuário')
        
        user = User(
            email=form.email.data,
            nome=form.nome.data,
            cargo=form.cargo.data,
            nivel_acesso=form.nivel_acesso.data,
            is_active=form.is_active.data
        )
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('listar_usuarios'))
    
    return render_template('admin/usuario_form.html', form=form, titulo='Novo Usuário')

@app.route('/admin/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        user.email = form.email.data
        user.nome = form.nome.data
        user.cargo = form.cargo.data
        user.nivel_acesso = form.nivel_acesso.data
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('listar_usuarios'))
    
    return render_template('admin/usuario_form.html', form=form, titulo='Editar Usuário')

@app.route('/admin/usuarios/excluir/<int:id>', methods=['POST'])
@login_required
@admin_required
def excluir_usuario(id):
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('Você não pode excluir sua própria conta.', 'error')
        return redirect(url_for('listar_usuarios'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('listar_usuarios'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 
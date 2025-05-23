import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, ValidationError
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'  # Altere para uma chave secreta segura
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///abordagens.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
app.config['WTF_CSRF_ENABLED'] = True

csrf = CSRFProtect(app)

# Garantir que a pasta de uploads existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Modelo para a tabela de abordagens
class Abordagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(100), nullable=False)
    vulgo = db.Column(db.String(50))
    cpf = db.Column(db.String(14))
    data_nascimento = db.Column(db.Date)
    endereco_abordagem = db.Column(db.String(200), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    observacoes = db.Column(db.Text)
    imagem = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Abordagem {self.nome_completo}>'

# Formulário para cadastro de abordagem
class AbordagemForm(FlaskForm):
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=100)])
    vulgo = StringField('Vulgo', validators=[Optional(), Length(max=50)])
    cpf = StringField('CPF', validators=[Optional(), Length(max=14)])
    data_nascimento = DateField('Data de Nascimento', validators=[Optional()])
    endereco_abordagem = StringField('Endereço da Abordagem', validators=[DataRequired(), Length(max=200)])
    observacoes = TextAreaField('Observações', validators=[Optional()])
    imagem = FileField('Imagem', validators=[
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

def save_image(file):
    if file:
        filename = secure_filename(file.filename)
        # Adiciona timestamp ao nome do arquivo para evitar conflitos
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    return None

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Filtros de busca
    search = request.args.get('search', '')
    date_start = request.args.get('date_start', '')
    date_end = request.args.get('date_end', '')
    
    query = Abordagem.query
    
    if search:
        query = query.filter(
            db.or_(
                Abordagem.nome_completo.ilike(f'%{search}%'),
                Abordagem.vulgo.ilike(f'%{search}%'),
                Abordagem.cpf.ilike(f'%{search}%')
            )
        )
    
    if date_start:
        try:
            date_start = datetime.strptime(date_start, '%Y-%m-%d')
            query = query.filter(Abordagem.data_hora >= date_start)
        except ValueError:
            pass
    
    if date_end:
        try:
            date_end = datetime.strptime(date_end, '%Y-%m-%d')
            # Adiciona um dia para incluir o dia inteiro
            date_end = date_end.replace(hour=23, minute=59, second=59)
            query = query.filter(Abordagem.data_hora <= date_end)
        except ValueError:
            pass
    
    # Ordena por data/hora mais recente
    query = query.order_by(Abordagem.data_hora.desc())
    
    # Paginação
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    abordagens = pagination.items
    
    return render_template('index.html', abordagens=abordagens, pagination=pagination)

@app.route('/nova', methods=['GET', 'POST'])
def nova_abordagem():
    form = AbordagemForm()
    if form.validate_on_submit():
        imagem_filename = save_image(form.imagem.data)
        
        abordagem = Abordagem(
            nome_completo=form.nome_completo.data,
            vulgo=form.vulgo.data,
            cpf=form.cpf.data,
            data_nascimento=form.data_nascimento.data,
            endereco_abordagem=form.endereco_abordagem.data,
            observacoes=form.observacoes.data,
            imagem=imagem_filename
        )
        
        db.session.add(abordagem)
        db.session.commit()
        
        flash('Abordagem registrada com sucesso!', 'success')
        return redirect(url_for('index'))
    
    return render_template('nova_abordagem.html', form=form)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_abordagem(id):
    abordagem = Abordagem.query.get_or_404(id)
    form = AbordagemForm(obj=abordagem)
    
    if form.validate_on_submit():
        if form.imagem.data:
            # Remove a imagem antiga se existir
            if abordagem.imagem:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], abordagem.imagem)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Salva a nova imagem
            abordagem.imagem = save_image(form.imagem.data)
        
        abordagem.nome_completo = form.nome_completo.data
        abordagem.vulgo = form.vulgo.data
        abordagem.cpf = form.cpf.data
        abordagem.data_nascimento = form.data_nascimento.data
        abordagem.endereco_abordagem = form.endereco_abordagem.data
        abordagem.observacoes = form.observacoes.data
        
        db.session.commit()
        flash('Abordagem atualizada com sucesso!', 'success')
        return redirect(url_for('visualizar_abordagem', id=id))
    
    return render_template('editar_abordagem.html', form=form, abordagem=abordagem)

@app.route('/visualizar/<int:id>')
def visualizar_abordagem(id):
    abordagem = Abordagem.query.get_or_404(id)
    return render_template('visualizar_abordagem.html', abordagem=abordagem)

@app.route('/excluir/<int:id>', methods=['POST'])
def excluir_abordagem(id):
    abordagem = Abordagem.query.get_or_404(id)
    
    # Remove a imagem se existir
    if abordagem.imagem:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], abordagem.imagem)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(abordagem)
    db.session.commit()
    
    flash('Abordagem excluída com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8080) 
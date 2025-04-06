import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, ValidationError
from werkzeug.utils import secure_filename
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import tempfile
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'  # Altere para uma chave secreta segura
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///abordagens.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
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
    nome_mae = db.Column(db.String(100), nullable=False)
    vulgo = db.Column(db.String(50))
    cpf = db.Column(db.String(14))
    data_nascimento = db.Column(db.Date)
    endereco_abordagem = db.Column(db.String(200), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    observacoes = db.Column(db.Text)
    imagem = db.Column(db.String(255))
    historico_pca = db.Column(db.String(255))
    
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
    observacoes = TextAreaField('Observações', validators=[Optional()])
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
        filename = secure_filename(file.filename)
        # Adiciona prefixo e timestamp ao nome do arquivo para evitar conflitos
        name, ext = os.path.splitext(filename)
        filename = f"{prefix}_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    return None

@app.route('/')
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
def nova_abordagem():
    form = AbordagemForm()
    if form.validate_on_submit():
        imagem_filename = save_image(form.imagem.data, 'img')
        historico_pca_filename = save_image(form.historico_pca.data, 'pca')
        
        abordagem = Abordagem(
            nome_completo=form.nome_completo.data,
            nome_mae=form.nome_mae.data,
            vulgo=form.vulgo.data,
            cpf=form.cpf.data,
            data_nascimento=form.data_nascimento.data,
            endereco_abordagem=form.endereco_abordagem.data,
            observacoes=form.observacoes.data,
            imagem=imagem_filename,
            historico_pca=historico_pca_filename
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
        # Preserva os valores existentes
        nome_completo = form.nome_completo.data
        nome_mae = form.nome_mae.data
        vulgo = form.vulgo.data
        cpf = form.cpf.data
        data_nascimento = form.data_nascimento.data
        endereco_abordagem = form.endereco_abordagem.data
        observacoes = form.observacoes.data
        
        # Processa a imagem apenas se uma nova for enviada
        if form.imagem.data and hasattr(form.imagem.data, 'filename') and form.imagem.data.filename:
            # Remove a imagem antiga se existir
            if abordagem.imagem:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], abordagem.imagem)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Salva a nova imagem
            imagem_filename = save_image(form.imagem.data, 'img')
        else:
            # Mantém a imagem existente
            imagem_filename = abordagem.imagem
        
        # Processa o histórico do PCA apenas se um novo for enviado
        if form.historico_pca.data and hasattr(form.historico_pca.data, 'filename') and form.historico_pca.data.filename:
            # Remove o histórico do PCA antigo se existir
            if abordagem.historico_pca:
                old_historico_path = os.path.join(app.config['UPLOAD_FOLDER'], abordagem.historico_pca)
                if os.path.exists(old_historico_path):
                    os.remove(old_historico_path)
            
            # Salva o novo histórico do PCA
            historico_pca_filename = save_image(form.historico_pca.data, 'pca')
        else:
            # Mantém o histórico do PCA existente
            historico_pca_filename = abordagem.historico_pca
        
        # Atualiza a abordagem com os novos valores
        abordagem.nome_completo = nome_completo
        abordagem.nome_mae = nome_mae
        abordagem.vulgo = vulgo
        abordagem.cpf = cpf
        abordagem.data_nascimento = data_nascimento
        abordagem.endereco_abordagem = endereco_abordagem
        abordagem.observacoes = observacoes
        abordagem.imagem = imagem_filename
        abordagem.historico_pca = historico_pca_filename
        
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
    
    # Remove o histórico do PCA se existir
    if abordagem.historico_pca:
        historico_path = os.path.join(app.config['UPLOAD_FOLDER'], abordagem.historico_pca)
        if os.path.exists(historico_path):
            os.remove(historico_path)
    
    db.session.delete(abordagem)
    db.session.commit()
    
    flash('Abordagem excluída com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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
            data = [['Nome Completo', 'Nome da Mãe', 'Vulgo', 'CPF', 'Data/Hora', 'Endereço']]
            
            # Dados da tabela
            for abordagem in abordagens:
                data.append([
                    abordagem.nome_completo,
                    abordagem.nome_mae,
                    abordagem.vulgo or '-',
                    abordagem.cpf or '-',
                    abordagem.data_hora.strftime('%d/%m/%Y %H:%M'),
                    abordagem.endereco_abordagem
                ])
            
            # Criar e estilizar a tabela
            table = Table(data, colWidths=[1.2*inch, 1.2*inch, 0.8*inch, 0.8*inch, 1*inch, 1.5*inch])
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
                
                # Informações básicas em uma tabela
                info_data = [
                    ['Nome Completo:', abordagem.nome_completo],
                    ['Nome da Mãe:', abordagem.nome_mae],
                    ['Vulgo:', abordagem.vulgo or '-'],
                    ['CPF:', abordagem.cpf or '-'],
                    ['Data/Hora:', abordagem.data_hora.strftime('%d/%m/%Y %H:%M')],
                    ['Endereço:', abordagem.endereco_abordagem]
                ]
                
                if abordagem.data_nascimento:
                    info_data.append(['Data de Nascimento:', abordagem.data_nascimento.strftime('%d/%m/%Y')])
                
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
                
                # Imagens
                elements.append(Spacer(1, 10))
                elements.append(Paragraph("Imagens:", styles['Heading3']))
                
                # Criar uma tabela para as imagens
                img_data = []
                
                # Imagem principal
                if abordagem.imagem:
                    img_path = os.path.join(app.config['UPLOAD_FOLDER'], abordagem.imagem)
                    if os.path.exists(img_path):
                        img_data.append(['Imagem Principal:', Image(img_path, width=2*inch, height=2*inch)])
                    else:
                        img_data.append(['Imagem Principal:', 'Imagem não encontrada'])
                else:
                    img_data.append(['Imagem Principal:', 'Não disponível'])
                
                # Imagem do histórico do PCA
                if abordagem.historico_pca:
                    pca_path = os.path.join(app.config['UPLOAD_FOLDER'], abordagem.historico_pca)
                    if os.path.exists(pca_path):
                        img_data.append(['Histórico do PCA:', Image(pca_path, width=2*inch, height=2*inch)])
                    else:
                        img_data.append(['Histórico do PCA:', 'Imagem não encontrada'])
                else:
                    img_data.append(['Histórico do PCA:', 'Não disponível'])
                
                img_table = Table(img_data, colWidths=[1.5*inch, 4*inch])
                img_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                elements.append(img_table)
                
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='127.0.0.1', port=8080) 
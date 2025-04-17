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




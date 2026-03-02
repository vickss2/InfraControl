from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    ordens = db.relationship('OrdemServico', backref='cliente', lazy=True)

class OrdemServico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipamento = db.Column(db.String(100), nullable=False)
    descricao_problema = db.Column(db.Text, nullable=False)
    diagnostico_ia = db.Column(db.Text)
    valor = db.Column(db.Float)
    status = db.Column(db.String(50), default='Aberto')
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    foto_antes = db.Column(db.String(255))
    
    # NOVO CAMPO: Guarda a data exata em que a garantia vai acabar
    data_garantia = db.Column(db.DateTime, nullable=True)
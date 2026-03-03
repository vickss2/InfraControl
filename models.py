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
    marca = db.Column(db.String(50), nullable=True)
    tipo_manutencao = db.Column(db.String(50), nullable=True)
    descricao_problema = db.Column(db.Text, nullable=False)
    diagnostico_ia = db.Column(db.Text)
    
    # FINANCEIRO DA OS
    valor = db.Column(db.Float) # Valor Mão de Obra
    desconto = db.Column(db.Float, default=0.0)
    data_abertura = db.Column(db.DateTime, default=datetime.now)
    
    status = db.Column(db.String(50), default='Aberto')
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    foto_antes = db.Column(db.String(255))
    data_garantia = db.Column(db.DateTime, nullable=True)
    nota_cliente = db.Column(db.Integer, nullable=True)
    comentario_cliente = db.Column(db.Text, nullable=True)
    itens = db.relationship('ItemOS', backref='ordem', cascade="all, delete-orphan", lazy=True)

class Peca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    marca = db.Column(db.String(100), nullable=True)
    numero_serie = db.Column(db.String(100), nullable=True)
    valor_custo = db.Column(db.Float, nullable=False)
    valor_venda = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=0, nullable=False)
    data_adicao = db.Column(db.DateTime, default=datetime.now)

class ItemOS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id'), nullable=False)
    peca_id = db.Column(db.Integer, db.ForeignKey('peca.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    nome_peca = db.Column(db.String(150))
    peca = db.relationship('Peca')
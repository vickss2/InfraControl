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
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    telefone = db.Column(db.String(20), nullable=False)
    ordens = db.relationship('OrdemServico', backref='cliente', lazy=True)

class Peca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    marca = db.Column(db.String(100))
    numero_serie = db.Column(db.String(100))
    valor_custo = db.Column(db.Float, default=0.0)
    valor_venda = db.Column(db.Float, default=0.0)
    quantidade = db.Column(db.Integer, default=0)

# --- NOVO: CATÁLOGO DE SERVIÇOS FIXOS ---
class Servico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    valor = db.Column(db.Float, default=0.0)

class OrdemServico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipamento = db.Column(db.String(150), nullable=False)
    marca = db.Column(db.String(100))
    tipo_manutencao = db.Column(db.String(50))
    descricao_problema = db.Column(db.Text)
    diagnostico_ia = db.Column(db.Text)
    
    valor = db.Column(db.Float, default=0.0) 
    desconto = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='Aberto')
    data_abertura = db.Column(db.DateTime, default=datetime.utcnow)
    data_garantia = db.Column(db.DateTime)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    foto_antes = db.Column(db.String(255))
    nota_cliente = db.Column(db.Integer)
    comentario_cliente = db.Column(db.Text)
    
    itens = db.relationship('ItemOS', backref='ordem', lazy=True, cascade="all, delete-orphan")
    # --- NOVO: Serviços adicionados nesta OS ---
    servicos_feitos = db.relationship('ItemServicoOS', backref='ordem', lazy=True, cascade="all, delete-orphan")

class ItemOS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id'), nullable=False)
    peca_id = db.Column(db.Integer, db.ForeignKey('peca.id'))
    nome_peca = db.Column(db.String(150))
    quantidade = db.Column(db.Integer, default=1)
    valor_unitario = db.Column(db.Float, default=0.0)
    valor_total = db.Column(db.Float, default=0.0)
    peca = db.relationship('Peca')

# --- NOVO: SERVIÇOS QUE FORAM FEITOS NA OS ---
class ItemServicoOS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id'), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servico.id'))
    nome_servico = db.Column(db.String(150))
    valor_cobrado = db.Column(db.Float, default=0.0)
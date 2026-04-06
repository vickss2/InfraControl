from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='tecnico') # A MÁGICA DOS DOIS CRACHÁS ESTÁ AQUI

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    ordens = db.relationship('OrdemServico', backref='cliente', lazy=True)

class OrdemServico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    equipamento = db.Column(db.String(100), nullable=False)
    marca = db.Column(db.String(50))
    tipo_manutencao = db.Column(db.String(50))
    descricao_problema = db.Column(db.Text)
    diagnostico_ia = db.Column(db.Text)
    valor = db.Column(db.Float, default=0.0)
    desconto = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='Aberto')
    data_abertura = db.Column(db.DateTime, default=db.func.current_timestamp())
    data_garantia = db.Column(db.DateTime)
    foto_antes = db.Column(db.String(255))
    nota_cliente = db.Column(db.Integer)
    comentario_cliente = db.Column(db.Text)
    itens = db.relationship('ItemOS', backref='ordem', lazy=True, cascade="all, delete-orphan")
    servicos_feitos = db.relationship('ItemServicoOS', backref='ordem', lazy=True, cascade="all, delete-orphan")

class Peca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    marca = db.Column(db.String(50))
    numero_serie = db.Column(db.String(50))
    valor_custo = db.Column(db.Float, nullable=False)
    valor_venda = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, default=0)

class ItemOS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id'), nullable=False)
    peca_id = db.Column(db.Integer, db.ForeignKey('peca.id'), nullable=False)
    nome_peca = db.Column(db.String(100))
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    peca = db.relationship('Peca')

class Servico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Float, nullable=False)

class ItemServicoOS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id'), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servico.id'), nullable=False)
    nome_servico = db.Column(db.String(100))
    valor_cobrado = db.Column(db.Float, nullable=False)
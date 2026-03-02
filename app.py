import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Cliente, OrdemServico
from ia_engine import simular_ia
from fpdf import FPDF
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'infra_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///infracontrol.db'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id): return User.query.get(int(user_id))

# --- DASHBOARD ---
@app.route('/')
@login_required
def dashboard():
    ordens = OrdemServico.query.all()
    categorias = {'Tela Azul / Hardware': 0, 'Lentidão / SSD': 0, 'Energia / Placa-mãe': 0, 'Vírus / Malwares': 0, 'Rede / Internet': 0, 'Outros': 0}
    for o in ordens:
        desc = o.descricao_problema.lower() if o.descricao_problema else ""
        if "tela azul" in desc or "bsod" in desc: categorias['Tela Azul / Hardware'] += 1
        elif "lento" in desc or "travando" in desc: categorias['Lentidão / SSD'] += 1
        elif "não liga" in desc or "energia" in desc: categorias['Energia / Placa-mãe'] += 1
        elif "vírus" in desc or "propaganda" in desc or "virus" in desc: categorias['Vírus / Malwares'] += 1
        elif "internet" in desc or "rede" in desc or "wifi" in desc: categorias['Rede / Internet'] += 1
        else: categorias['Outros'] += 1
            
    categorias_filtradas = {k: v for k, v in categorias.items() if v > 0}
    stats = {'c': Cliente.query.count(), 'oa': OrdemServico.query.filter(OrdemServico.status != 'Finalizado').count(), 'f': sum(o.valor for o in ordens)}
    return render_template('dashboard.html', stats=stats, labels=list(categorias_filtradas.keys()), values=list(categorias_filtradas.values()))

# --- PORTAL DE RASTREAMENTO ---
@app.route('/rastreio', methods=['GET', 'POST'])
def rastreio():
    os_data, erro = None, None
    if request.method == 'POST':
        busca = request.form.get('busca', '').strip()
        if busca.isdigit() and len(busca) < 6: os_data = OrdemServico.query.filter_by(id=int(busca)).first()
        if not os_data: os_data = OrdemServico.query.join(Cliente).filter(Cliente.telefone.ilike(f'%{busca}%')).order_by(OrdemServico.id.desc()).first()
        if os_data:
            p_map, c_map = {'Aberto': 15, 'Em Análise': 40, 'Aguardando Peça': 65, 'Pronto para Retirada': 95, 'Finalizado': 100}, {'Aberto': 'info', 'Em Análise': 'warning', 'Aguardando Peça': 'danger', 'Pronto para Retirada': 'primary', 'Finalizado': 'success'}
            os_data.nivel, os_data.estilo = p_map.get(os_data.status, 10), c_map.get(os_data.status, 'secondary')
        else: erro = "Ordem não encontrada."
    return render_template('rastreio.html', os_data=os_data, erro=erro)

# --- CLIENTES ---
@app.route('/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    if request.method == 'POST':
        novo = Cliente(nome=request.form['nome'], email=request.form['email'], telefone=request.form['telefone'])
        db.session.add(novo); db.session.commit(); flash('Cliente cadastrado!', 'success')
        return redirect(url_for('clientes'))
    search = request.args.get('search')
    lista = Cliente.query.filter(Cliente.nome.ilike(f'%{search}%')).all() if search else Cliente.query.all()
    return render_template('clientes.html', clientes=lista, search=search)

@app.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        cliente.nome, cliente.email, cliente.telefone = request.form['nome'], request.form['email'], request.form['telefone']
        db.session.commit(); flash('Atualizado!', 'success')
        return redirect(url_for('clientes'))
    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/excluir_cliente/<int:id>')
@login_required
def excluir_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if OrdemServico.query.filter_by(cliente_id=id).first(): flash('Possui ordens vinculadas!', 'danger')
    else: db.session.delete(cliente); db.session.commit(); flash('Removido!', 'success')
    return redirect(url_for('clientes'))

# --- ORDENS E UPLOAD ---
@app.route('/os', methods=['GET', 'POST'])
@login_required
def ordens():
    if request.method == 'POST':
        desc = request.form.get('descricao', '')
        diag, preco = simular_ia(desc)
        nome_arquivo = None
        if 'foto_antes' in request.files:
            foto = request.files['foto_antes']
            if foto.filename != '':
                nome_arquivo = secure_filename(foto.filename)
                caminho = os.path.join(app.root_path, 'static', 'uploads')
                os.makedirs(caminho, exist_ok=True)
                foto.save(os.path.join(caminho, nome_arquivo))
        
        nova_os = OrdemServico(equipamento=request.form.get('equipamento'), descricao_problema=desc, diagnostico_ia=diag, valor=preco, cliente_id=request.form.get('cliente_id'), foto_antes=nome_arquivo, status='Aberto')
        db.session.add(nova_os); db.session.commit(); flash('Ordem gerada!', 'success')
        return redirect(url_for('ordens'))
    
    search = request.args.get('search')
    query = OrdemServico.query.filter(OrdemServico.status != 'Finalizado')
    if search: query = query.filter(OrdemServico.equipamento.ilike(f'%{search}%') | OrdemServico.cliente.has(Cliente.nome.ilike(f'%{search}%')))
    ativas = query.all()
    
    p_map, c_map = {'Aberto': 15, 'Em Análise': 40, 'Aguardando Peça': 65, 'Pronto para Retirada': 95}, {'Aberto': 'info', 'Em Análise': 'warning', 'Aguardando Peça': 'danger', 'Pronto para Retirada': 'primary'}
    for o in ativas: o.nivel, o.estilo = p_map.get(o.status, 10), c_map.get(o.status, 'secondary')
    return render_template('os.html', ordens=ativas, clientes=Cliente.query.all(), search=search)

@app.route('/atualizar_status/<int:id>', methods=['POST'])
@login_required
def atualizar_status(id):
    ordem = OrdemServico.query.get_or_404(id); ordem.status = request.form.get('status'); db.session.commit(); flash('Status atualizado!', 'info')
    return redirect(url_for('ordens'))

# AQUI ESTÁ A MÁGICA DA GARANTIA
@app.route('/finalizar_os/<int:os_id>')
@login_required
def finalizar_os(os_id):
    os_data = OrdemServico.query.get_or_404(os_id)
    os_data.status = 'Finalizado'
    # Calcula 90 dias a partir de agora e salva
    os_data.data_garantia = datetime.now() + timedelta(days=90)
    db.session.commit()
    flash('Serviço entregue! Garantia de 90 dias ativada.', 'success')
    return redirect(url_for('ordens'))

@app.route('/excluir_os/<int:id>')
@login_required
def excluir_os(id):
    db.session.delete(OrdemServico.query.get_or_404(id)); db.session.commit(); flash('Excluída!', 'success')
    return redirect(url_for('ordens'))

# --- HISTÓRICO COM CONTROLE DE GARANTIA ---
@app.route('/historico')
@login_required
def historico():
    concluidas = OrdemServico.query.filter_by(status='Finalizado').order_by(OrdemServico.id.desc()).all()
    hoje = datetime.now() # Enviamos o dia de hoje para o HTML comparar
    return render_template('historico.html', ordens=concluidas, hoje=hoje)

# --- PDF E LOGIN ---
@app.route('/gerar_pdf/<int:os_id>')
@login_required
def gerar_pdf(os_id):
    os_data = OrdemServico.query.get_or_404(os_id)
    pdf = FPDF(); pdf.add_page(); pdf.set_fill_color(255, 133, 161); pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("helvetica", 'B', 20); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, "InfraControl - Relatorio Tecnico", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, f"Protocolo: #{os_data.id} | Status: {os_data.status}", new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(190, 10, f"Cliente: {os_data.cliente.nome}\nEquipamento: {os_data.equipamento}\nDiagnostico: {os_data.diagnostico_ia}", border=1)
    
    # Se tiver garantia, mostra no PDF!
    if os_data.data_garantia:
        pdf.ln(5)
        pdf.set_text_color(0, 128, 0) # Verde
        pdf.cell(0, 10, f"Garantia Valida ate: {os_data.data_garantia.strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    pdf.ln(5); pdf.cell(0, 10, f"Valor Total: R$ {os_data.valor:.2f}", align='R', new_x="LMARGIN", new_y="NEXT")
    buf = io.BytesIO(pdf.output()); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"OS_{os_id}.pdf", mimetype='application/pdf')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user); return redirect(url_for('dashboard'))
        flash('Erro de login.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout(): logout_user(); return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='123')); db.session.commit()
    app.run(debug=True)
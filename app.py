import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# IMPORTANDO AS NOVAS TABELAS DE SERVIÇOS
from models import db, User, Cliente, OrdemServico, Peca, ItemOS, Servico, ItemServicoOS
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

@app.template_filter('moeda')
def format_moeda(valor):
    try:
        v = float(valor)
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "0,00"

def converter_dinheiro(valor_str):
    if not valor_str: return 0.0
    v = str(valor_str).upper().replace('R', '').replace('$', '').strip()
    v = ''.join(c for c in v if c.isdigit() or c in '.,')
    if not v: return 0.0
    if ',' in v and '.' in v:
        if v.rfind(',') > v.rfind('.'): v = v.replace('.', '').replace(',', '.')
        else: v = v.replace(',', '')
    elif '.' in v:
        partes = v.split('.')
        if len(partes) > 2: v = ''.join(partes[:-1]) + '.' + partes[-1]
        else:
            if len(partes[1]) == 3: v = v.replace('.', '')
    elif ',' in v: v = v.replace(',', '.')
    try: return float(v)
    except ValueError: return 0.0

@app.route('/')
@login_required
def dashboard():
    ordens = OrdemServico.query.all()
    categorias = {'Armazenamento': 0, 'Memória/Vídeo': 0, 'Placa/Fonte': 0, 'Tela/Periféricos': 0, 'Redes': 0, 'Impressoras': 0, 'Sistema/Vírus': 0, 'Preventiva': 0, 'Outros': 0}
    avaliacoes = [o.nota_cliente for o in ordens if o.nota_cliente is not None]
    media_estrelas = round(sum(avaliacoes) / len(avaliacoes), 1) if avaliacoes else 0

    faturamento_bruto = 0
    for o in ordens:
        desc = o.descricao_problema.lower() if o.descricao_problema else ""
        if any(p in desc for p in ["ssd", "hd", "armazenamento", "disco"]): categorias['Armazenamento'] += 1
        elif any(p in desc for p in ["ram", "vídeo", "tela azul", "bsod"]): categorias['Memória/Vídeo'] += 1
        elif any(p in desc for p in ["fonte", "não liga", "placa-mãe", "curto"]): categorias['Placa/Fonte'] += 1
        elif any(p in desc for p in ["tela", "monitor", "teclado", "carcaça"]): categorias['Tela/Periféricos'] += 1
        elif any(p in desc for p in ["rede", "internet", "wi-fi", "roteador", "switch"]): categorias['Redes'] += 1
        elif any(p in desc for p in ["impressora", "papel", "tinta"]): categorias['Impressoras'] += 1
        elif any(p in desc for p in ["vírus", "windows", "formatar"]): categorias['Sistema/Vírus'] += 1
        elif any(p in desc for p in ["limpeza", "pasta térmica", "esquentando"]): categorias['Preventiva'] += 1
        else: categorias['Outros'] += 1
        
        # Agora soma também os Serviços de Catálogo!
        faturamento_bruto += (o.valor + sum(s.valor_cobrado for s in o.servicos_feitos) + sum(i.valor_total for i in o.itens)) - (o.desconto or 0)
            
    categorias_filtradas = {k: v for k, v in categorias.items() if v > 0}
    stats = {'c': Cliente.query.count(), 'oa': OrdemServico.query.filter(OrdemServico.status != 'Finalizado').count(), 'f': faturamento_bruto}
    return render_template('dashboard.html', stats=stats, media_estrelas=media_estrelas, labels=list(categorias_filtradas.keys()), values=list(categorias_filtradas.values()))

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

@app.route('/avaliar/<int:os_id>', methods=['GET', 'POST'])
def avaliar(os_id):
    os_data = OrdemServico.query.get_or_404(os_id)
    sucesso = False
    if request.method == 'POST':
        os_data.nota_cliente = int(request.form.get('nota')); os_data.comentario_cliente = request.form.get('comentario'); db.session.commit(); sucesso = True
    return render_template('avaliar.html', os_data=os_data, sucesso=sucesso)

@app.route('/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    if request.method == 'POST':
        db.session.add(Cliente(nome=request.form['nome'], email=request.form['email'], telefone=request.form['telefone'])); db.session.commit(); flash('Cadastrado!', 'success'); return redirect(url_for('clientes'))
    search = request.args.get('search')
    lista = Cliente.query.filter(Cliente.nome.ilike(f'%{search}%')).all() if search else Cliente.query.all()
    return render_template('clientes.html', clientes=lista, search=search)

@app.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST': cliente.nome, cliente.email, cliente.telefone = request.form['nome'], request.form['email'], request.form['telefone']; db.session.commit(); flash('Atualizado!', 'success'); return redirect(url_for('clientes'))
    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/excluir_cliente/<int:id>')
@login_required
def excluir_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if OrdemServico.query.filter_by(cliente_id=id).first(): flash('Possui ordens!', 'danger')
    else: db.session.delete(cliente); db.session.commit(); flash('Removido!', 'success')
    return redirect(url_for('clientes'))

# --- NOVO: ROTAS DO CATÁLOGO DE SERVIÇOS ---
@app.route('/servicos', methods=['GET', 'POST'])
@login_required
def servicos():
    if request.method == 'POST':
        valor = converter_dinheiro(request.form['valor'])
        db.session.add(Servico(nome=request.form['nome'], valor=valor))
        db.session.commit(); flash('Serviço cadastrado!', 'success'); return redirect(url_for('servicos'))
    lista = Servico.query.all()
    return render_template('servicos.html', servicos=lista)

@app.route('/excluir_servico/<int:id>')
@login_required
def excluir_servico(id): 
    db.session.delete(Servico.query.get_or_404(id))
    db.session.commit(); flash('Serviço Removido do Catálogo!', 'success')
    return redirect(url_for('servicos'))

@app.route('/estoque', methods=['GET', 'POST'])
@login_required
def estoque():
    if request.method == 'POST':
        custo = converter_dinheiro(request.form['valor_custo'])
        venda = converter_dinheiro(request.form['valor_venda'])
        db.session.add(Peca(nome=request.form['nome'], marca=request.form.get('marca', ''), numero_serie=request.form.get('numero_serie', ''), valor_custo=custo, valor_venda=venda, quantidade=int(request.form['quantidade'])))
        db.session.commit(); flash('Peça cadastrada!', 'success'); return redirect(url_for('estoque'))
    search = request.args.get('search')
    lista = Peca.query.filter(Peca.nome.ilike(f'%{search}%') | Peca.numero_serie.ilike(f'%{search}%') | Peca.marca.ilike(f'%{search}%')).all() if search else Peca.query.all()
    return render_template('estoque.html', pecas=lista, search=search)

@app.route('/editar_peca/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_peca(id):
    peca = Peca.query.get_or_404(id)
    if request.method == 'POST':
        peca.nome = request.form['nome']
        peca.marca = request.form.get('marca', '')
        peca.numero_serie = request.form.get('numero_serie', '')
        peca.valor_custo = converter_dinheiro(request.form['valor_custo'])
        peca.valor_venda = converter_dinheiro(request.form['valor_venda'])
        peca.quantidade = int(request.form['quantidade'])
        db.session.commit(); flash('Peça atualizada com sucesso!', 'success'); return redirect(url_for('estoque'))
    return render_template('editar_peca.html', peca=peca)

@app.route('/excluir_peca/<int:id>')
@login_required
def excluir_peca(id): db.session.delete(Peca.query.get_or_404(id)); db.session.commit(); flash('Removida!', 'success'); return redirect(url_for('estoque'))

@app.route('/api/checar_equipamento')
@login_required
def checar_equipamento():
    cliente_id, equipamento = request.args.get('cliente_id'), request.args.get('equipamento', '').strip()
    if not cliente_id or len(equipamento) < 3: return jsonify({'encontrado': False})
    historico = OrdemServico.query.filter(OrdemServico.cliente_id == cliente_id, OrdemServico.equipamento.ilike(f'%{equipamento}%')).order_by(OrdemServico.id.desc()).first()
    if historico: return jsonify({'encontrado': True, 'id_anterior': historico.id, 'problema': historico.descricao_problema, 'status': historico.status})
    return jsonify({'encontrado': False})

@app.route('/os', methods=['GET', 'POST'])
@login_required
def ordens():
    if request.method == 'POST':
        desc = request.form.get('descricao', '')
        diag, preco = simular_ia(desc)
        nome_arq = None
        if 'foto_antes' in request.files and request.files['foto_antes'].filename != '':
            nome_arq = secure_filename(request.files['foto_antes'].filename); request.files['foto_antes'].save(os.path.join(app.root_path, 'static', 'uploads', nome_arq))
        # O preço da IA entra como um valor de "Mão de Obra Manual/Extra"
        db.session.add(OrdemServico(equipamento=request.form.get('equipamento'), marca=request.form.get('marca'), tipo_manutencao=request.form.get('tipo_manutencao'), descricao_problema=desc, diagnostico_ia=diag, valor=preco, cliente_id=request.form.get('cliente_id'), foto_antes=nome_arq, status='Aberto'))
        db.session.commit(); flash('Ordem gerada!', 'success'); return redirect(url_for('ordens'))
    search = request.args.get('search')
    query = OrdemServico.query.filter(OrdemServico.status != 'Finalizado')
    if search: query = query.filter(OrdemServico.equipamento.ilike(f'%{search}%') | OrdemServico.cliente.has(Cliente.nome.ilike(f'%{search}%')))
    ativas = query.all()
    p_map, c_map = {'Aberto': 15, 'Em Análise': 40, 'Aguardando Peça': 65, 'Pronto para Retirada': 95}, {'Aberto': 'info', 'Em Análise': 'warning', 'Aguardando Peça': 'danger', 'Pronto para Retirada': 'primary'}
    for o in ativas: o.nivel, o.estilo = p_map.get(o.status, 10), c_map.get(o.status, 'secondary')
    return render_template('os.html', ordens=ativas, clientes=Cliente.query.all(), search=search)

@app.route('/gerenciar_os/<int:id>', methods=['GET', 'POST'])
@login_required
def gerenciar_os(id):
    os_data = OrdemServico.query.get_or_404(id)
    
    if request.method == 'POST': # Atualizar o valor de mão de obra extra manualmente
        os_data.valor = converter_dinheiro(request.form.get('valor_extra', '0'))
        db.session.commit()
        flash('Mão de obra avulsa atualizada!', 'success')
        return redirect(url_for('gerenciar_os', id=os_data.id))

    total_pecas = sum(i.valor_total for i in os_data.itens)
    total_servicos = sum(s.valor_cobrado for s in os_data.servicos_feitos)
    total_geral = (os_data.valor + total_servicos + total_pecas) - (os_data.desconto or 0.0)
    
    # Enviando o Catálogo de Serviços para a tela!
    catalogo = Servico.query.all()
    
    return render_template('gerenciar_os.html', os_data=os_data, pecas=Peca.query.filter(Peca.quantidade > 0).all(), catalogo=catalogo, total_pecas=total_pecas, total_servicos=total_servicos, total_geral=total_geral)

# --- ADICIONAR E REMOVER SERVIÇOS DA OS ---
@app.route('/add_servico_os/<int:os_id>', methods=['POST'])
@login_required
def add_servico_os(os_id):
    servico = Servico.query.get_or_404(request.form.get('servico_id'))
    db.session.add(ItemServicoOS(os_id=os_id, servico_id=servico.id, nome_servico=servico.nome, valor_cobrado=servico.valor))
    db.session.commit(); flash('Serviço adicionado ao orçamento!', 'success')
    return redirect(url_for('gerenciar_os', id=os_id))

@app.route('/remover_servico_os/<int:item_id>')
@login_required
def remover_servico_os(item_id):
    item = ItemServicoOS.query.get_or_404(item_id)
    os_id = item.os_id
    db.session.delete(item); db.session.commit(); flash('Serviço removido.', 'info')
    return redirect(url_for('gerenciar_os', id=os_id))

@app.route('/add_item_os/<int:os_id>', methods=['POST'])
@login_required
def add_item_os(os_id):
    peca = Peca.query.get_or_404(request.form.get('peca_id'))
    qtd = int(request.form.get('quantidade', 1))
    if peca.quantidade < qtd: flash('Estoque insuficiente!', 'danger'); return redirect(url_for('gerenciar_os', id=os_id))
    peca.quantidade -= qtd
    db.session.add(ItemOS(os_id=os_id, peca_id=peca.id, quantidade=qtd, valor_unitario=peca.valor_venda, valor_total=(peca.valor_venda * qtd), nome_peca=peca.nome))
    db.session.commit(); flash('Peça adicionada!', 'success'); return redirect(url_for('gerenciar_os', id=os_id))

@app.route('/remover_item_os/<int:item_id>')
@login_required
def remover_item_os(item_id):
    item = ItemOS.query.get_or_404(item_id)
    if item.peca: item.peca.quantidade += item.quantidade
    db.session.delete(item); db.session.commit(); flash('Peça removida e devolvida.', 'info'); return redirect(url_for('gerenciar_os', id=item.os_id))

@app.route('/aplicar_desconto/<int:os_id>', methods=['POST'])
@login_required
def aplicar_desconto(os_id):
    os_data = OrdemServico.query.get_or_404(os_id)
    os_data.desconto = converter_dinheiro(request.form.get('desconto', '0'))
    db.session.commit(); flash('Desconto aplicado com sucesso!', 'success'); return redirect(url_for('gerenciar_os', id=os_id))

@app.route('/atualizar_status/<int:id>', methods=['POST'])
@login_required
def atualizar_status(id): ordem = OrdemServico.query.get_or_404(id); ordem.status = request.form.get('status'); db.session.commit(); flash('Atualizado!', 'info'); return redirect(url_for('ordens'))

@app.route('/finalizar_os/<int:os_id>')
@login_required
def finalizar_os(os_id): os_data = OrdemServico.query.get_or_404(os_id); os_data.status = 'Finalizado'; os_data.data_garantia = datetime.now() + timedelta(days=90); db.session.commit(); flash('Entregue!', 'success'); return redirect(url_for('ordens'))

@app.route('/excluir_os/<int:id>')
@login_required
def excluir_os(id): db.session.delete(OrdemServico.query.get_or_404(id)); db.session.commit(); flash('Excluída!', 'success'); return redirect(url_for('ordens'))

@app.route('/historico')
@login_required
def historico(): return render_template('historico.html', ordens=OrdemServico.query.filter_by(status='Finalizado').order_by(OrdemServico.id.desc()).all(), hoje=datetime.now())

@app.route('/relatorios', methods=['GET'])
@login_required
def relatorios():
    mes_atual = datetime.now().strftime('%Y-%m')
    filtro_mes = request.args.get('mes', mes_atual)
    
    ordens = OrdemServico.query.filter(OrdemServico.status == 'Finalizado', OrdemServico.data_abertura.like(f'{filtro_mes}%')).all()
    
    # Soma de Mão de Obra Avulsa + Serviços do Catálogo
    receita_servicos = sum((o.valor + sum(s.valor_cobrado for s in o.servicos_feitos)) for o in ordens)
    receita_pecas = sum(item.valor_total for o in ordens for item in o.itens)
    custo_pecas = sum((item.peca.valor_custo * item.quantidade) for o in ordens for item in o.itens if item.peca)
    descontos = sum(o.desconto or 0 for o in ordens)

    faturamento_bruto = receita_servicos + receita_pecas - descontos
    lucro_liquido = faturamento_bruto - custo_pecas

    financeiro = {
        'servicos': receita_servicos, 'venda_pecas': receita_pecas, 'descontos': descontos,
        'faturamento': faturamento_bruto, 'custo_pecas': custo_pecas, 'lucro': lucro_liquido
    }
    
    return render_template('relatorios.html', ordens=ordens, financeiro=financeiro, mes_selecionado=filtro_mes)

@app.route('/relatorio_pdf')
@login_required
def relatorio_pdf():
    filtro_mes = request.args.get('mes', datetime.now().strftime('%Y-%m'))
    ordens = OrdemServico.query.filter(OrdemServico.status == 'Finalizado', OrdemServico.data_abertura.like(f'{filtro_mes}%')).all()
    
    receita_servicos = sum((o.valor + sum(s.valor_cobrado for s in o.servicos_feitos)) for o in ordens)
    receita_pecas = sum(item.valor_total for o in ordens for item in o.itens)
    custo_pecas = sum((item.peca.valor_custo * item.quantidade) for o in ordens for item in o.itens if item.peca)
    descontos = sum(o.desconto or 0 for o in ordens)
    faturamento_bruto = receita_servicos + receita_pecas - descontos
    lucro_liquido = faturamento_bruto - custo_pecas

    pdf = FPDF(); pdf.add_page(); pdf.set_fill_color(43, 45, 66); pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_font("helvetica", 'B', 18); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, f"Relatorio Financeiro - {filtro_mes}", align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(15); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 8, "RESUMO DO MES:", new_x="LMARGIN", new_y="NEXT"); pdf.set_font("helvetica", '', 11)
    
    pdf.cell(0, 6, f"Total de Servicos (Mao de Obra): R$ {format_moeda(receita_servicos)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Total de Pecas Vendidas: R$ {format_moeda(receita_pecas)}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(255, 0, 0); pdf.cell(0, 6, f"Descontos Concedidos: - R$ {format_moeda(descontos)}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0); pdf.cell(0, 6, f"Custo das Pecas (Reposicao): - R$ {format_moeda(custo_pecas)}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5); pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 8, f"FATURAMENTO BRUTO: R$ {format_moeda(faturamento_bruto)}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 128, 0)
    pdf.cell(0, 8, f"LUCRO LIQUIDO REAL: R$ {format_moeda(lucro_liquido)}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(10); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", 'B', 10)
    pdf.cell(0, 8, "LISTA DE EQUIPAMENTOS ENTREGUES:", new_x="LMARGIN", new_y="NEXT"); pdf.set_font("helvetica", '', 9)
    for o in ordens:
        total_os = (o.valor + sum(s.valor_cobrado for s in o.servicos_feitos) + sum(i.valor_total for i in o.itens)) - (o.desconto or 0)
        pdf.cell(0, 6, f"OS #{o.id} | {o.cliente.nome} | {o.equipamento} | Total: R$ {format_moeda(total_os)}", border=1, new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO(pdf.output()); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"Financeiro_{filtro_mes}.pdf", mimetype='application/pdf')

@app.route('/gerar_pdf/<int:os_id>')
@login_required
def gerar_pdf(os_id):
    os_data = OrdemServico.query.get_or_404(os_id)
    pdf = FPDF(); pdf.add_page(); pdf.set_fill_color(255, 133, 161); pdf.rect(0, 0, 210, 40, 'F'); pdf.set_font("helvetica", 'B', 20); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, "InfraControl - Relatorio Tecnico", align='C', new_x="LMARGIN", new_y="NEXT"); pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, f"Protocolo: #{os_data.id} | Status: {os_data.status}", new_x="LMARGIN", new_y="NEXT")
    
    marca_t = os_data.marca if os_data.marca else "N/A"
    tipo_t = os_data.tipo_manutencao if os_data.tipo_manutencao else "N/A"
    pdf.multi_cell(190, 10, f"Cliente: {os_data.cliente.nome}\nEquipamento: {os_data.equipamento} ({marca_t})\nTipo: {tipo_t}\nDiagnostico: {os_data.diagnostico_ia}", border=1)
    
    pdf.ln(5); pdf.set_font("helvetica", 'B', 10)
    
    # Lista de Serviços Feitos
    if os_data.servicos_feitos or os_data.valor > 0:
        pdf.cell(0, 8, "Servicos Executados:", new_x="LMARGIN", new_y="NEXT"); pdf.set_font("helvetica", '', 10)
        for s in os_data.servicos_feitos:
            pdf.cell(0, 6, f"- {s.nome_servico} | R$ {format_moeda(s.valor_cobrado)}", new_x="LMARGIN", new_y="NEXT")
        if os_data.valor > 0:
            pdf.cell(0, 6, f"- Mao de Obra Avulsa | R$ {format_moeda(os_data.valor)}", new_x="LMARGIN", new_y="NEXT")

    total_pecas = 0
    if os_data.itens:
        pdf.ln(3); pdf.set_font("helvetica", 'B', 10)
        pdf.cell(0, 8, "Pecas Usadas (Estoque):", new_x="LMARGIN", new_y="NEXT"); pdf.set_font("helvetica", '', 10)
        for item in os_data.itens:
            pdf.cell(0, 6, f"- {item.quantidade}x {item.nome_peca} | R$ {format_moeda(item.valor_total)}", new_x="LMARGIN", new_y="NEXT")
            total_pecas += item.valor_total

    if os_data.desconto and os_data.desconto > 0:
        pdf.ln(3); pdf.set_text_color(255, 0, 0); pdf.cell(0, 8, f"Desconto Aplicado: - R$ {format_moeda(os_data.desconto)}", new_x="LMARGIN", new_y="NEXT"); pdf.set_text_color(0, 0, 0)

    total_servicos = sum(s.valor_cobrado for s in os_data.servicos_feitos)
    total_geral = (os_data.valor + total_servicos + total_pecas) - (os_data.desconto or 0)

    pdf.ln(5); pdf.set_font("helvetica", 'B', 14); pdf.cell(0, 10, f"TOTAL A PAGAR: R$ {format_moeda(total_geral)}", align='R', new_x="LMARGIN", new_y="NEXT")
    buf = io.BytesIO(pdf.output()); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"OS_{os_id}.pdf", mimetype='application/pdf')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']): login_user(user); return redirect(url_for('dashboard'))
        flash('Inválido.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout(): logout_user(); return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Essa linha mágica cria as tabelas de Serviços sem apagar as antigas!
        if not User.query.filter_by(username='admin').first(): db.session.add(User(username='admin', password=generate_password_hash('123'))); db.session.commit()
    app.run(debug=True)
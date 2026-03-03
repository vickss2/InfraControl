def simular_ia(descricao):
    desc = descricao.lower()
    print("\n" + "="*30)
    print(f"IA LENDO O PROBLEMA: {desc}")
    
    # 1. NOVO: IMPRESSORAS
    if any(p in desc for p in ["impressora", "papel", "atolado", "tinta", "cartucho", "toner", "cabeça de impressão", "cabeçote", "manchando", "epson", "brother"]):
        print("-> IA DECIDIU: Impressora")
        return "Falha no sistema de impressão. Recomendado desobstrução, limpeza de cabeçote, reset de almofadas ou troca de toner/cartucho.", 180.00
    
    # 2. Armazenamento e Performance
    elif any(p in desc for p in ["ssd", "hd", "armazenamento", "lento", "travando", "disco", "corrompido", "demora"]):
        print("-> IA DECIDIU: Armazenamento")
        return "Falha ou lentidão no disco rígido/SSD. Recomendado teste de saúde, formatação e possível substituição.", 280.00
    
    # 3. Tela e Estrutura Física
    elif any(p in desc for p in ["tela", "display", "quebrado", "quebrou", "caiu", "dobradiça", "carcaça", "touch", "vidro"]):
        print("-> IA DECIDIU: Tela/Estrutura")
        return "Dano físico detectado no monitor/carcaça. Necessária desmontagem completa e substituição da peça.", 450.00
        
    # 4. Energia, Fonte e Placa-mãe
    elif any(p in desc for p in ["não liga", "desligou", "fonte", "queimou", "curto", "bateria", "energia", "placa-mãe", "placa mãe", "choque"]):
        print("-> IA DECIDIU: Energia/Placa")
        return "Problema de alimentação ou curto-circuito na placa-mãe. Necessário reparo elétrico ou troca de componente.", 350.00
        
    # 5. Infraestrutura de Redes
    elif any(p in desc for p in ["rede", "internet", "wi-fi", "wifi", "roteador", "cabo", "switch", "crimpagem", "servidor", "conexão"]):
        print("-> IA DECIDIU: Infraestrutura/Redes")
        return "Falha de conectividade ou infraestrutura. Inclui teste de cabos, configuração de roteador/switch.", 180.00
        
    # 6. Memória RAM e Vídeo
    elif any(p in desc for p in ["ram", "memória", "bipa", "apita", "vídeo", "artefato", "tela azul", "bsod"]):
        print("-> IA DECIDIU: RAM/Vídeo")
        return "Erro de processamento gráfico ou memória. Requer limpeza de contatos ou substituição.", 250.00
        
    # 7. Manutenção Preventiva e Aquecimento
    elif any(p in desc for p in ["limpeza", "pasta térmica", "esquentando", "temperatura", "cooler", "preventiva", "poeira", "barulho", "quente"]):
        print("-> IA DECIDIU: Manutenção Preventiva")
        return "Superaquecimento detectado. Necessária manutenção preventiva: limpeza interna e troca de pasta térmica.", 150.00
        
    # 8. Software e Segurança
    elif any(p in desc for p in ["vírus", "malware", "windows", "formatação", "formatar", "propaganda", "office", "pacote", "hacker"]):
        print("-> IA DECIDIU: Software/Vírus")
        return "Problema de software/infecção viral. Necessário backup de dados e reinstalação limpa do sistema operacional.", 120.00
        
    print("-> IA DECIDIU: Genérico")
    return "Sintomas não específicos. Necessário diagnóstico de bancada completo para elaboração de orçamento final.", 100.00
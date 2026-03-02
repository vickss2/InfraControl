def simular_ia(descricao):
    desc = descricao.lower()
    
    # Base de conhecimento com Diagnóstico e Preço Sugerido
    if "tela azul" in desc or "bsod" in desc:
        return "Falha crítica de sistema ou hardware. Recomenda-se teste de memória e restauração de kernel.", 250.00
    elif "lento" in desc or "travando" in desc:
        return "Sobrecarga de processos ou desgaste de disco. Sugestão: Upgrade para SSD e limpeza técnica.", 180.00
    elif "não liga" in desc:
        return "Falha no circuito de alimentação. Verificar fonte ATX e capacitores da placa-mãe.", 350.00
    elif "vírus" in desc or "propaganda" in desc:
        return "Infecção por malwares detectada. Necessário varredura profunda e otimização.", 120.00
    elif "internet" in desc or "rede" in desc:
        return "Instabilidade na placa de rede ou drivers. Verificar conectores e DNS.", 100.00
    
    # Valor padrão caso não identifique a palavra
    return "Sintomas genéricos. Necessário checklist completo de hardware e software.", 150.00
import random

def simular_ia(descricao):
    if not descricao:
        return "Nenhum sintoma relatado. Necessária análise técnica presencial.", 0.0

    desc = descricao.lower()
    
    # 1. Problemas de Tela / Display
    if any(palavra in desc for palavra in ["tela", "display", "quebrado", "rachado", "monitor", "risco"]):
        return "Possível dano físico no display ou cabo flat. Necessária a substituição da tela.", 350.00
        
    # 2. Problemas de Lentidão / Sistema / Formatação
    elif any(palavra in desc for palavra in ["lento", "travando", "formatar", "windows", "ssd", "hd", "sistema"]):
        return "Falha no sistema operacional ou disco rígido fadigado. Recomendada formatação e/ou upgrade para SSD.", 120.00
        
    # 3. Problemas de Energia / Placa Mãe / Fonte
    elif any(palavra in desc for palavra in ["liga", "energia", "fonte", "placa", "curto", "queimou", "bateria"]):
        return "Falha de alimentação detectada. Possível curto na placa-mãe ou falha na fonte. Requer análise em bancada.", 250.00
        
    # 4. Vírus e Segurança
    elif any(palavra in desc for palavra in ["vírus", "virus", "malware", "hacker", "propaganda", "pop-up"]):
        return "Sistema comprometido por software malicioso. Necessária remoção de vírus e otimização de segurança.", 90.00
        
    # 5. Superaquecimento / Preventiva
    elif any(palavra in desc for palavra in ["esquentando", "quente", "desligando", "sujo", "limpeza", "pasta térmica", "barulho", "cooler"]):
        return "Sintomas de superaquecimento crítico. Urgente realização de Limpeza Preventiva e troca de pasta térmica.", 150.00
        
    # 6. Impressoras
    elif any(palavra in desc for palavra in ["impressora", "papel", "tinta", "cartucho", "toner", "atolado", "manchando"]):
        return "Falha no mecanismo de impressão. Necessária revisão na tracionadora de papel ou desentupimento da cabeça de impressão.", 100.00
        
    # 7. Redes / Internet
    elif any(palavra in desc for palavra in ["rede", "internet", "wi-fi", "wifi", "roteador", "cabo", "conecta"]):
        return "Falha de conectividade. Necessária reconfiguração de rede, testes no roteador ou climpagem de cabos.", 80.00
        
    # 8. Padrão (Se não reconhecer nada específico)
    else:
        return "Sintomas inconclusivos ou defeito complexo. Necessário diagnóstico técnico presencial completo na bancada.", 100.00
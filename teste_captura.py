#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste final para ajustar captura de nomes completos
"""

import re

def testar_captura_completa():
    textos = [
        "A advogada Maria Costa Lima não cumpriu o prazo.",
        "Educador físico Pedro Henrique supervisionou mal o treino.",
        "O médico Antonio José não atendeu bem."
    ]
    
    # Padrão atual (muito lazy)
    padrao_adv_atual = r'\b(?:Adv\.?|Adva\.?|Advogado|Advogada)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,})*?)(?=\s*\(|$|,|\.|;|\s+[a-z])'
    
    # Padrão melhorado (capturar mais)
    padrao_adv_novo = r'\b(?:Adv\.?|Adva\.?|Advogado|Advogada)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,})*)(?=\s+[a-z]|$|,|\.|;)'
    
    for texto in textos:
        print(f"\nTexto: {texto}")
        
        print("Padrão atual (lazy):")
        matches = re.finditer(padrao_adv_atual, texto, re.IGNORECASE)
        for match in matches:
            print(f"  '{match.group(1)}' - Contexto: '{match.group(0)}'")
        
        print("Padrão novo (greedy limitado):")
        matches = re.finditer(padrao_adv_novo, texto, re.IGNORECASE)
        for match in matches:
            print(f"  '{match.group(1)}' - Contexto: '{match.group(0)}'")

if __name__ == "__main__":
    testar_captura_completa()
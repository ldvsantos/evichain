#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug dos padrões regex específicos
"""

import re

def debug_padroes():
    texto1 = "O Dr. João Silva (CRM 12345) foi negligente no atendimento."
    texto3 = "A advogada Maria Costa Lima não cumpriu o prazo."
    
    # Padrão Dr
    padrao_dr = r'\b(?:Dr\.?|Dra\.?|Doutor|Doutora)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,})*?)(?=\s*\(|$|,|\.|;)'
    
    # Padrão Advogada
    padrao_adv = r'\b(?:Adv\.?|Adva\.?|Advogado|Advogada)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,})*?)(?=\s*\(|$|,|\.|;)'
    
    print("=== TESTE DR ===")
    print(f"Texto: {texto1}")
    print(f"Padrão: {padrao_dr}")
    matches = re.finditer(padrao_dr, texto1, re.IGNORECASE)
    for match in matches:
        print(f"Match: '{match.group(1)}' - Contexto: '{match.group(0)}'")
    
    print("\n=== TESTE ADVOGADA ===")
    print(f"Texto: {texto3}")
    print(f"Padrão: {padrao_adv}")
    matches = re.finditer(padrao_adv, texto3, re.IGNORECASE)
    for match in matches:
        print(f"Match: '{match.group(1)}' - Contexto: '{match.group(0)}'")

if __name__ == "__main__":
    debug_padroes()
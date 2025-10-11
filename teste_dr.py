#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste mais específico para ajustar o Dr. João Silva
"""

import re

def testar_dr_joao():
    texto = "O Dr. João Silva (CRM 12345) foi negligente no atendimento."
    
    # Padrão melhorado para capturar João Silva, não apenas João
    padrao_dr = r'\b(?:Dr\.?|Dra\.?|Doutor|Doutora)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,})*?)(?=\s*\(|$|,|\.|;)'
    
    print(f"Texto: {texto}")
    print(f"Padrão: {padrao_dr}")
    
    matches = re.finditer(padrao_dr, texto, re.IGNORECASE)
    for match in matches:
        print(f"Match: '{match.group(1)}' - Contexto: '{match.group(0)}'")

if __name__ == "__main__":
    testar_dr_joao()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico de padrões regex para depuração
"""

import re

def testar_padroes():
    print("=" * 60)
    print("TESTE DE PADRÕES REGEX")
    print("=" * 60)
    
    texto = "Educador físico Pedro Henrique supervisionou mal o treino."
    
    # Padrão atual problemático
    padrao_atual = r'\b(?:Educador\s+físico|Educadora\s+física)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}){0,2})(?=\s+[a-z]|$)'
    
    # Padrão melhorado
    padrao_novo = r'\b(?:Educador\s+físico|Educadora\s+física)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,})*?)(?=\s+[a-z]|$)'
    
    print(f"Texto: {texto}")
    print(f"Padrão atual: {padrao_atual}")
    
    matches_atual = re.finditer(padrao_atual, texto, re.IGNORECASE)
    for match in matches_atual:
        print(f"Match atual: '{match.group(1)}' - Contexto: '{match.group(0)}'")
    
    print(f"\nPadrão novo: {padrao_novo}")
    matches_novo = re.finditer(padrao_novo, texto, re.IGNORECASE)
    for match in matches_novo:
        print(f"Match novo: '{match.group(1)}' - Contexto: '{match.group(0)}'")
    
    # Teste com Dr.
    texto2 = "O Dr. João Silva (CRM 12345) foi negligente no atendimento."
    padrao_dr = r'\b(?:Dr\.?|Dra\.?|Doutor|Doutora)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,})*?)(?=\s|\(|$)'
    
    print(f"\nTeste Dr:")
    print(f"Texto: {texto2}")
    print(f"Padrão: {padrao_dr}")
    
    matches_dr = re.finditer(padrao_dr, texto2, re.IGNORECASE)
    for match in matches_dr:
        print(f"Match Dr: '{match.group(1)}' - Contexto: '{match.group(0)}'")

if __name__ == "__main__":
    testar_padroes()
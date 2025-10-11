#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug completo do detector de nomes
"""

from detector_nomes import DetectorNomes
import re

def debug_completo():
    print("=" * 60)
    print("DEBUG COMPLETO DO DETECTOR")
    print("=" * 60)
    
    detector = DetectorNomes()
    
    texto = "O Dr. João Silva (CRM 12345) foi negligente no atendimento."
    
    print(f"Texto: {texto}")
    print("\n--- TESTE MANUAL DOS PADRÕES ---")
    
    # Teste manual de cada padrão
    for i, padrao in enumerate(detector.padroes_nomes):
        print(f"\nPadrão {i+1}: {padrao}")
        matches = re.finditer(padrao, texto, re.IGNORECASE | re.UNICODE)
        
        for match in matches:
            nome = match.group(1) if match.groups() else match.group(0)
            print(f"  Match bruto: '{nome}' - Contexto: '{match.group(0)}'")
            
            # Testar limpeza
            nome_limpo = detector._limpar_nome(nome)
            print(f"  Nome limpo: '{nome_limpo}'")
            
            # Testar validação
            valido = detector._validar_nome(nome_limpo)
            print(f"  Válido: {valido}")
    
    print("\n--- TESTE MÉTODO COMPLETO ---")
    resultado = detector.detectar_nomes_e_registros(texto)
    print(f"Resultado final: {resultado}")

if __name__ == "__main__":
    debug_completo()
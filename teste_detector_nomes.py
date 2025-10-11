#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para o detector de nomes
"""

from detector_nomes import DetectorNomes
import json

def testar_deteccao():
    print("=" * 60)
    print("TESTE ESPECÍFICO DO DETECTOR DE NOMES")
    print("=" * 60)
    
    detector = DetectorNomes()
    
    casos_teste = [
        "O Dr. João Silva (CRM 12345) foi negligente no atendimento.",
        "Personal trainer Carlos Santos CREF 123456 causou lesão durante treino.",
        "A advogada Maria Costa Lima não cumpriu o prazo.",
        "Educador físico Pedro Henrique supervisionou mal o treino.",
        "O médico Antonio José não atendeu bem."
    ]
    
    for i, texto in enumerate(casos_teste, 1):
        print(f"\n--- CASO {i} ---")
        print(f"Texto: {texto}")
        
        resultado = detector.detectar_nomes_e_registros(texto)
        
        print(f"Nomes detectados: {len(resultado['nomes_detectados'])}")
        for nome in resultado['nomes_detectados']:
            print(f"  - '{nome['nome_detectado']}' (confiabilidade: {nome['confiabilidade']}%)")
            print(f"    Contexto: '{nome['contexto_encontrado']}'")
            print(f"    Padrão: {nome['padrao_usado']}")
        
        print(f"Registros: {len(resultado['registros_detectados'])}")
        for reg in resultado['registros_detectados']:
            print(f"  - {reg['conselho']} {reg['numero_registro']}")
        
        print(f"Confiabilidade geral: {resultado['confiabilidade_deteccao']}%")
        print(f"Recomenda investigação: {resultado['recomendacao_investigacao']}")

if __name__ == "__main__":
    testar_deteccao()
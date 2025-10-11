#!/usr/bin/env python3
"""
Teste da investigação automática - Debug
"""

import sys
import os

# Adicionar o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from detector_nomes import DetectorNomes
from consultor_registros import ConsultorRegistrosProfissionais
from investigador_digital import InvestigadorDigital

def teste_deteccao_nomes():
    """Testa a detecção de nomes"""
    print("=" * 60)
    print("TESTE DE DETECÇÃO DE NOMES")
    print("=" * 60)
    
    detector = DetectorNomes()
    
    # Casos de teste
    casos_teste = [
        "O Dr. João Silva (CRM 12345) foi negligente no atendimento.",
        "Personal trainer Carlos Santos CREF 123456 causou lesão durante treino.",
        "Educador físico Maria Oliveira (CREF 654321) não supervisionou adequadamente.",
        "O advogado Paulo Roberto OAB 98765 cometeu má conduta.",
        "Dentista Ana Costa CRO 11111 não seguiu protocolo de higiene."
    ]
    
    for i, caso in enumerate(casos_teste, 1):
        print(f"\n--- CASO {i} ---")
        print(f"Texto: {caso}")
        
        resultado = detector.detectar_nomes_e_registros(caso)
        
        print(f"Nomes detectados: {len(resultado['nomes_detectados'])}")
        print(f"Registros detectados: {len(resultado['registros_detectados'])}")
        print(f"Contexto profissional: {resultado['contexto_profissional']}")
        print(f"Confiabilidade: {resultado['confiabilidade_deteccao']}%")
        print(f"Recomenda investigação: {resultado['recomendacao_investigacao']}")
        
        if resultado['nomes_detectados']:
            for nome in resultado['nomes_detectados']:
                print(f"  - Nome: {nome['nome_detectado']} (confiabilidade: {nome['confiabilidade']}%)")
        
        if resultado['registros_detectados']:
            for registro in resultado['registros_detectados']:
                print(f"  - Registro: {registro['conselho']} {registro['numero_registro']}")

def teste_investigacao_completa():
    """Testa a investigação completa"""
    print("\n" + "=" * 60)
    print("TESTE DE INVESTIGAÇÃO COMPLETA")
    print("=" * 60)
    
    try:
        investigador = InvestigadorDigital()
        
        # Teste com CREF
        print("\n--- TESTE CREF ---")
        resultado = investigador.investigar_completo(
            nome="Carlos Santos",
            registro_profissional="123456",
            conselho="CREF"
        )
        
        print(f"Investigação concluída: {resultado is not None}")
        if resultado:
            print(f"Registros oficiais: {resultado['registros_oficiais'].get('registro_encontrado', False)}")
            print(f"Redes sociais: {len(resultado.get('redes_sociais', {}))}")
            
    except Exception as e:
        print(f"Erro na investigação: {e}")

if __name__ == "__main__":
    teste_deteccao_nomes()
    teste_investigacao_completa()
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
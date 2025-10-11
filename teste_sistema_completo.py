#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste completo do sistema de análise com investigação automática
"""

from ia_engine_openai_padrao import IAEngineOpenAIPadrao
import json

def testar_sistema_completo():
    print("=" * 60)
    print("TESTE SISTEMA COMPLETO DE ANÁLISE + INVESTIGAÇÃO")
    print("=" * 60)
    
    # Criar instância da IA
    ia_engine = IAEngineOpenAIPadrao()
    
    # Casos de teste
    casos_teste = [
        {
            "denuncia": "O Dr. João Silva (CRM 12345) foi negligente no atendimento e não seguiu protocolos médicos adequados.",
            "categoria": "Negligência Médica"
        },
        {
            "denuncia": "Personal trainer Carlos Santos CREF 123456 causou lesão durante treino por não supervisionar adequadamente os exercícios.",
            "categoria": "Educação Física"
        }
    ]
    
    for i, caso in enumerate(casos_teste, 1):
        print(f"\n--- CASO {i}: {caso['categoria']} ---")
        print(f"Denúncia: {caso['denuncia']}")
        
        try:
            # Preparar dados da transação
            transaction_data = {
                "texto_denuncia": caso['denuncia'],
                "categoria_selecionada": caso['categoria'],
                "timestamp": "2025-10-10T10:00:00",
                "denunciante": "Sistema de Teste"
            }
            
            # Analisar com investigação automática
            resultado = ia_engine.analisar_denuncia_completa(
                transaction_data=transaction_data,
                trace_id=f"teste_{i}"
            )
            
            print(f"\nGravidade: {resultado.get('gravidade', 'N/A')}")
            print(f"Urgência: {resultado.get('urgencia', 'N/A')}")
            print(f"Confiabilidade: {resultado.get('confiabilidade', 'N/A')}%")
            
            # Verificar se investigação foi executada
            investigacoes = resultado.get('investigacoes_automaticas', {})
            if investigacoes:
                print(f"\n✅ Investigações realizadas: {len(investigacoes)}")
                for nome, dados in investigacoes.items():
                    print(f"  - {nome}: {'Concluída' if dados.get('concluida') else 'Pendente'}")
            else:
                print("❌ Nenhuma investigação automática realizada")
            
            print(f"\nRecomendação: {resultado.get('recomendacao', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Erro na análise: {e}")
        
        print("-" * 60)

if __name__ == "__main__":
    testar_sistema_completo()
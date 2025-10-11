#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificação das denúncias no sistema
"""

import requests
import json

def verificar_denuncias():
    print("=" * 60)
    print("VERIFICAÇÃO DAS DENÚNCIAS NO SISTEMA")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:5000/api/complaints")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Response type: {type(response_data)}")
            
            # A resposta tem a estrutura {"complaints": [...]}
            complaints = response_data.get("complaints", [])
            
            print(f"✅ Total de denúncias: {len(complaints)}")
            print(f"Tipo do primeiro item: {type(complaints[0]) if complaints else 'N/A'}")
            
            
            # Mostrar as denúncias
            for i, complaint in enumerate(complaints):
                if i >= len(complaints) - 2:  # Últimas 2
                    print(f"\n--- DENÚNCIA {i+1} ---")
                    print(f"ID: {complaint.get('id', 'N/A')}")
                    print(f"Título: {complaint.get('titulo', 'N/A')}")
                    print(f"Descrição: {complaint.get('descricao', 'N/A')[:100]}...")
                    
                    # Verificar análise IA
                    ia_analysis = complaint.get('ia_analysis')
                    if ia_analysis:
                        print(f"✅ Análise IA presente")
                        
                        # Verificar detecção de nomes
                        deteccao = ia_analysis.get('deteccao_nomes', {})
                        nomes = deteccao.get('nomes_detectados', [])
                        print(f"   Nomes detectados: {len(nomes)}")
                        for nome in nomes[:3]:
                            if isinstance(nome, dict):
                                print(f"     - {nome.get('nome', 'N/A')} ({nome.get('confiabilidade', 0)}%)")
                            else:
                                print(f"     - {nome}")
                        
                        # Verificar investigação
                        investigacao = ia_analysis.get('investigacao_digital', {})
                        if investigacao:
                            consultas = investigacao.get('consultas_registros', [])
                            print(f"   Consultas registros: {len(consultas)}")
                            
                            registros_encontrados = 0
                            for consulta in consultas:
                                if isinstance(consulta, dict) and consulta.get('registro_encontrado'):
                                    registros_encontrados += 1
                                    print(f"     ✅ {consulta.get('nome', 'N/A')} - {consulta.get('dados_profissional', {}).get('registro_cref_completo', 'N/A')}")
                            
                            print(f"   Registros válidos encontrados: {registros_encontrados}")
                        else:
                            print(f"   ❌ Investigação digital não realizada")
                    else:
                        print(f"❌ Análise IA não presente")
                    
                    # Mostrar estrutura completa para debug
                    print(f"\n--- ESTRUTURA COMPLETA (DEBUG) ---")
                    print(json.dumps(complaint, indent=2, ensure_ascii=False)[:1000] + "...")
        
        else:
            print(f"❌ Erro ao buscar denúncias: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    verificar_denuncias()
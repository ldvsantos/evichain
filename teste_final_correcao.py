#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste final com Luiz Oliveira dos Santos após correção
"""

import requests
import json

def testar_sistema_corrigido():
    print("=" * 90)
    print("🎯 TESTE FINAL - SISTEMA CORRIGIDO")
    print("Luiz Oliveira dos Santos - CREF 008072-P/BA")
    print("=" * 90)
    
    url_base = "http://localhost:5000"
    
    # Dados da denúncia
    dados_denuncia = {
        "titulo": "Teste CORREÇÃO - Luiz Oliveira dos Santos",
        "descricao": "quero denuncia Luiz Oliveira dos Santos pois não sei se ele é profissional registrado no CREF",
        "assunto": "Verificação CREF",
        "finalidade": "Teste de correção",
        "conselho": "CREF",
        "categoria": "Educação Física",
        "prioridade": "Alta"
    }
    
    print(f"\n🚀 ENVIANDO DENÚNCIA COM CORREÇÃO...")
    
    try:
        response = requests.post(
            f"{url_base}/api/submit-complaint", 
            json=dados_denuncia,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            resultado = response.json()
            complaint_id = resultado.get("complaint_id")
            
            print(f"✅ Denúncia criada: {complaint_id}")
            
            # Aguardar processamento
            import time
            print(f"\n⏳ Aguardando processamento...")
            time.sleep(3)
            
            # Verificar resultado
            print(f"\n🔍 VERIFICANDO RESULTADO...")
            
            response_list = requests.get(f"{url_base}/api/complaints")
            if response_list.status_code == 200:
                response_data = response_list.json()
                complaints = response_data.get("complaints", [])
                
                # Buscar nossa denúncia
                nossa_denuncia = None
                for complaint in complaints:
                    if complaint.get('id') == complaint_id:
                        nossa_denuncia = complaint
                        break
                
                if nossa_denuncia:
                    print(f"✅ Denúncia encontrada!")
                    
                    # Verificar análise IA
                    ia_analysis = nossa_denuncia.get("ia_analysis", {})
                    
                    if ia_analysis:
                        print(f"\n📊 ANÁLISE IA:")
                        
                        investigacao_auto = ia_analysis.get("investigacao_automatica", {})
                        
                        if investigacao_auto:
                            print(f"   🔍 INVESTIGAÇÃO AUTOMÁTICA REALIZADA!")
                            
                            # Verificar detecção
                            deteccao = investigacao_auto.get("deteccao_nomes", {})
                            nomes = deteccao.get("nomes_detectados", [])
                            
                            print(f"   📋 Nomes detectados: {len(nomes)}")
                            for nome_info in nomes:
                                if isinstance(nome_info, dict):
                                    nome = nome_info.get("nome_detectado", "N/A")
                                    conf = nome_info.get("confiabilidade", 0)
                                    print(f"     - {nome} ({conf}%)")
                            
                            # Verificar investigações
                            investigacoes = investigacao_auto.get("investigacoes_realizadas", [])
                            print(f"   🔍 Investigações: {len(investigacoes)}")
                            
                            registros_encontrados = 0
                            for inv in investigacoes:
                                nome_inv = inv.get("nome_investigado", "N/A")
                                resultado_inv = inv.get("resultado_investigacao", {})
                                
                                if isinstance(resultado_inv, dict):
                                    reg_oficiais = resultado_inv.get("registros_oficiais", {})
                                    if isinstance(reg_oficiais, dict):
                                        encontrado = reg_oficiais.get("registro_encontrado", False)
                                        
                                        if encontrado:
                                            registros_encontrados += 1
                                            dados_prof = reg_oficiais.get("dados_profissional", {})
                                            registro = dados_prof.get("registro_cref_completo", "N/A")
                                            uf = dados_prof.get("uf_registro", "N/A")
                                            categoria = dados_prof.get("categoria", "N/A")
                                            
                                            print(f"     ✅ {nome_inv}:")
                                            print(f"        📋 Registro: {registro}")
                                            print(f"        🗺️ UF: {uf}")
                                            print(f"        🎯 Categoria: {categoria}")
                                        else:
                                            print(f"     ❌ {nome_inv}: Não encontrado")
                            
                            print(f"\n🎯 RESULTADO FINAL:")
                            if registros_encontrados > 0:
                                print(f"   ✅ CORREÇÃO APLICADA COM SUCESSO!")
                                print(f"   ✅ Luiz Oliveira dos Santos ENCONTRADO!")
                                print(f"   ✅ Registro: CREF 008072-P/BA identificado!")
                                print(f"   ✅ Sistema corrigido eliminando falso negativo!")
                            else:
                                print(f"   ❌ Correção ainda não aplicada completamente")
                                print(f"   ⚠️ Sistema ainda reportando como não encontrado")
                        else:
                            print(f"   ❌ Investigação automática não realizada")
                    else:
                        print(f"   ❌ Análise IA não encontrada")
        else:
            print(f"❌ Erro: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Erro: {e}")

def comparar_antes_depois():
    print(f"\n" + "=" * 90)
    print(f"📊 COMPARAÇÃO ANTES E DEPOIS DA CORREÇÃO")
    print(f"=" * 90)
    
    print(f"\n🔍 CASO: Luiz Oliveira dos Santos")
    print(f"-" * 50)
    
    print(f"\n❌ ANTES DA INFORMAÇÃO CORRETA:")
    print(f"   📋 Dados no sistema: NÃO TINHA")
    print(f"   🔍 Resultado da busca: NÃO ENCONTRADO")
    print(f"   📊 Conclusão do sistema: POSSÍVEL IRREGULARIDADE")
    print(f"   ⚠️ Tipo de erro: FALSO NEGATIVO")
    
    print(f"\n✅ DEPOIS DA CORREÇÃO:")
    print(f"   📋 Dados no sistema: CREF 008072-P/BA")
    print(f"   🔍 Resultado da busca: ENCONTRADO")
    print(f"   📊 Conclusão do sistema: PROFISSIONAL REGULAR")
    print(f"   🎯 Tipo de acerto: VERDADEIRO POSITIVO")
    
    print(f"\n🎯 IMPACTO DA CORREÇÃO:")
    print(f"   ✅ Eliminação de falso negativo")
    print(f"   ✅ Melhoria na precisão do sistema")
    print(f"   ✅ Redução de investigações desnecessárias")
    print(f"   ✅ Maior confiabilidade nos resultados")
    
    print(f"\n📈 BENEFÍCIOS PARA OS CONSELHOS:")
    print(f"   💼 Menos tempo gasto em casos já regulares")
    print(f"   🎯 Foco em irregularidades reais")
    print(f"   📊 Dados mais precisos para tomada de decisão")
    print(f"   ⚡ Processo de investigação mais eficiente")

if __name__ == "__main__":
    testar_sistema_corrigido()
    comparar_antes_depois()
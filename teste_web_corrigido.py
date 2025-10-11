#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste final do sistema web com correção CONFEF
"""

import requests
import json

def testar_sistema_web_corrigido():
    print("=" * 70)
    print("TESTE FINAL DO SISTEMA WEB COM CORREÇÃO CONFEF")
    print("=" * 70)
    
    # URL do sistema
    url_base = "http://localhost:5000"
    
    # Texto da denúncia original
    denuncia_texto = "quero denuncia Luiz Diego Vidal pois não sei se ele é profissional registrado no CREF"
    
    print(f"\n📝 TEXTO DA DENÚNCIA:")
    print(f"'{denuncia_texto}'")
    
    print(f"\n🚀 ENVIANDO DENÚNCIA PARA O SISTEMA...")
    
    try:
        # Dados da denúncia
        dados_denuncia = {
            "titulo": "Denúncia CREF Teste",
            "descricao": denuncia_texto,
            "assunto": "Registro Profissional",
            "finalidade": "Verificação de regularidade",
            "conselho": "CREF",
            "categoria": "Educação Física",
            "prioridade": "Média"
        }
        
        # Enviar denúncia
        response = requests.post(
            f"{url_base}/api/submit-complaint", 
            json=dados_denuncia,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            resultado = response.json()
            complaint_id = resultado.get("complaint_id")
            
            print(f"✅ Denúncia criada com sucesso!")
            print(f"   ID: {complaint_id}")
            print(f"   Sucesso: {resultado.get('success', False)}")
            
            # A análise IA é feita automaticamente no servidor
            # Vamos buscar as denúncias para ver os resultados
            try:
                response_list = requests.get(f"{url_base}/api/complaints")
                if response_list.status_code == 200:
                    complaints = response_list.json()
                    
                    # Buscar nossa denúncia na lista
                    nossa_denuncia = None
                    for complaint in complaints:
                        if complaint.get('id') == complaint_id:
                            nossa_denuncia = complaint
                            break
                    
                    if nossa_denuncia:
                        print(f"\n🔍 ANÁLISE IA ENCONTRADA:")
                        
                        ia_analysis = nossa_denuncia.get("ia_analysis", {})
                        
                        if ia_analysis:
                            # Verificar detecção de nomes
                            deteccao = ia_analysis.get("deteccao_nomes", {})
                            nomes_detectados = deteccao.get("nomes_detectados", [])
                            
                            print(f"   📋 Nomes detectados: {len(nomes_detectados)}")
                            for nome_info in nomes_detectados[:3]:
                                if isinstance(nome_info, dict):
                                    nome = nome_info.get("nome", "N/A")
                                    confiabilidade = nome_info.get("confiabilidade", 0)
                                    print(f"     - {nome} (confiabilidade: {confiabilidade}%)")
                                else:
                                    print(f"     - {nome_info}")
                            
                            # Verificar investigação
                            investigacao = ia_analysis.get("investigacao_digital", {})
                            
                            if investigacao:
                                consultas = investigacao.get("consultas_registros", [])
                                print(f"   🔍 Consultas realizadas: {len(consultas)}")
                                
                                registros_encontrados = 0
                                for consulta in consultas:
                                    if isinstance(consulta, dict):
                                        nome_consultado = consulta.get("nome", "N/A") 
                                        conselho = consulta.get("conselho", "N/A")
                                        encontrado = consulta.get("registro_encontrado", False)
                                        
                                        if encontrado:
                                            registros_encontrados += 1
                                        
                                        status = "✅ ENCONTRADO" if encontrado else "❌ NÃO ENCONTRADO"
                                        print(f"     - {nome_consultado} no {conselho}: {status}")
                                        
                                        if encontrado:
                                            dados_prof = consulta.get("dados_profissional", {})
                                            registro = dados_prof.get("registro_cref_completo", "N/A")
                                            situacao = dados_prof.get("situacao_registro", "N/A")
                                            print(f"       Registro: {registro}")
                                            print(f"       Situação: {situacao}")
                                
                                print(f"\n📊 CONCLUSÃO DA INVESTIGAÇÃO:")
                                print(f"   ✅ Registros válidos encontrados: {registros_encontrados}")
                                
                                if registros_encontrados > 0:
                                    print(f"\n🎯 RESULTADO FINAL:")
                                    print(f"   ✅ CORREÇÃO APLICADA COM SUCESSO!")
                                    print(f"   ✅ Sistema agora detecta profissionais registrados")
                                    print(f"   ✅ Investigação automática funciona corretamente")
                                    print(f"   ✅ Luiz Diego Vidal foi encontrado no CREF")
                                else:
                                    print(f"\n⚠️ PROBLEMA:")
                                    print(f"   ❌ Nenhum registro válido encontrado")
                                    print(f"   ❌ Sistema ainda não está funcionando corretamente")
                            else:
                                print(f"   ❌ Investigação digital não foi realizada")
                        else:
                            print(f"   ❌ Análise IA não foi encontrada")
                    else:
                        print(f"   ❌ Denúncia não encontrada na lista")
                else:
                    print(f"   ❌ Erro ao buscar denúncias: {response_list.status_code}")
            except Exception as e:
                print(f"   ❌ Erro ao verificar resultado: {e}")
            
            # Verificar se investigação automática foi realizada
            if resultado.get("investigacao_automatica"):
                print(f"\n🔍 INVESTIGAÇÃO AUTOMÁTICA REALIZADA:")
                
                investigacao = resultado.get("investigacao_automatica", {})
                
                # Verificar nomes detectados
                nomes_detectados = investigacao.get("nomes_detectados", [])
                print(f"   📋 Nomes detectados: {len(nomes_detectados)}")
                
                for nome_info in nomes_detectados[:3]:  # Mostrar até 3 nomes
                    nome = nome_info.get("nome", "N/A")
                    confiabilidade = nome_info.get("confiabilidade", 0)
                    print(f"     - {nome} (confiabilidade: {confiabilidade}%)")
                
                # Verificar consultas realizadas
                consultas = investigacao.get("consultas_realizadas", [])
                print(f"   🔍 Consultas realizadas: {len(consultas)}")
                
                for consulta in consultas:
                    nome_consultado = consulta.get("nome", "N/A")
                    conselho = consulta.get("conselho", "N/A")
                    encontrado = consulta.get("registro_encontrado", False)
                    
                    status = "✅ ENCONTRADO" if encontrado else "❌ NÃO ENCONTRADO"
                    print(f"     - {nome_consultado} no {conselho}: {status}")
                    
                    if encontrado:
                        dados_prof = consulta.get("dados_profissional", {})
                        registro = dados_prof.get("registro_cref_completo", "N/A")
                        situacao = dados_prof.get("situacao_registro", "N/A")
                        print(f"       Registro: {registro}")
                        print(f"       Situação: {situacao}")
                
                # Verificar conclusão
                conclusao = investigacao.get("conclusao", {})
                alertas_encontrados = conclusao.get("alertas_encontrados", False)
                registros_encontrados = conclusao.get("registros_validos_encontrados", 0)
                
                print(f"\n📊 CONCLUSÃO DA INVESTIGAÇÃO:")
                print(f"   ⚠️ Alertas encontrados: {alertas_encontrados}")
                print(f"   ✅ Registros válidos: {registros_encontrados}")
                
                if registros_encontrados > 0:
                    print(f"\n🎯 RESULTADO FINAL:")
                    print(f"   ✅ CORREÇÃO APLICADA COM SUCESSO!")
                    print(f"   ✅ Sistema agora detecta profissionais registrados")
                    print(f"   ✅ Investigação automática funciona corretamente")
                    print(f"   ✅ Luiz Diego Vidal foi encontrado no CREF")
                else:
                    print(f"\n⚠️ PROBLEMA:")
                    print(f"   ❌ Nenhum registro válido encontrado")
                    print(f"   ❌ Sistema ainda não está funcionando corretamente")
                
            else:
                print(f"\n❌ INVESTIGAÇÃO AUTOMÁTICA NÃO FOI REALIZADA")
                print(f"   Verifique se o sistema de detecção está funcionando")
        
        else:
            print(f"❌ Erro ao enviar denúncia: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print(f"❌ ERRO: Não foi possível conectar ao servidor")
        print(f"   Certifique-se de que o servidor está rodando em {url_base}")
        print(f"   Execute: python app.py")
    
    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    testar_sistema_web_corrigido()
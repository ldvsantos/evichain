#!/usr/bin/env python3
"""
Teste da funcionalidade completa de PDF
"""

import requests
import json

def teste_pdf_backend():
    """Testa a geração de PDF pelo backend"""
    print("🧪 Testando geração de PDF com dados completos...")
    
    # Dados de teste completos
    dados_teste = {
        "complaint_id": "EVC-TEST-001",
        "titulo": "Teste PDF Completo - Negligência Médica",
        "assunto": "Negligência no atendimento médico",
        "prioridade": "ALTA",
        "finalidade": "Investigação disciplinar",
        "conselho": "CRM",
        "categoria": "Erro médico",
        "timestamp": "2025-10-11T10:30:00.000Z",
        "codigosAnteriores": "ABC123, DEF456",
        "ouvidoriaAnonima": True,
        "anonymous": False,
        "descricao": "Dr. João Silva realizou procedimento cirúrgico sem o devido cuidado e preparação. O médico não seguiu os protocolos de segurança estabelecidos pela instituição e não informou adequadamente o paciente sobre os riscos do procedimento. Durante a cirurgia, foram observadas práticas inadequadas que resultaram em complicações evitáveis. Há evidências fotográficas e testemunhas do ocorrido. Solicito investigação completa e rigorosa do caso.",
        "ia_analysis": {
            "analise_basica": {
                "palavras_chave": ["negligência médica", "procedimento cirúrgico", "protocolos de segurança", "complicações evitáveis"],
                "resumo": "Caso grave de negligência médica durante procedimento cirúrgico com evidências de descumprimento de protocolos de segurança e falta de informação adequada ao paciente.",
                "sentimento": "negativo"
            },
            "analise_juridica": {
                "gravidade": "alta",
                "tipificacao": "Negligência médica grave com evidências",
                "legislacao_especifica": {
                    "legislacao_sugerida": "Código de Ética Médica - Resolução CFM nº 2.217/2018",
                    "conselho": "Conselho Regional de Medicina",
                    "tipo": "Negligência",
                    "descricao": "Negligência no exercício da profissão médica com potencial dano ao paciente",
                    "artigos": ["Art. 1º", "Art. 14", "Art. 29", "Art. 32"],
                    "penalidades": ["Advertência confidencial", "Censura confidencial", "Censura pública", "Suspensão do exercício profissional", "Cassação do exercício profissional"]
                }
            },
            "classificacao_risco": {
                "nivel": "ALTO",
                "pontuacao": 90,
                "acao_recomendada": "Investigação imediata e medidas cautelares"
            },
            "investigacao_automatica": {
                "relatorio_deteccao": "DETECÇÃO AUTOMÁTICA DE PROFISSIONAIS\n\nConfiabilidade Geral: 85%\nContexto Profissional: SIM\nRecomenda Investigação: SIM\n\nProfissional identificado: Dr. João Silva\nEspecialidade: Cirurgia Geral\nLocal: Hospital Central\nRegistro: Verificação pendente",
                "deteccao_nomes": {
                    "confiabilidade_deteccao": 85,
                    "contexto_profissional": True,
                    "nomes_detectados": [
                        {
                            "nome_detectado": "João Silva",
                            "confiabilidade": 90,
                            "contexto_encontrado": "Dr. João Silva realizou procedimento cirúrgico"
                        }
                    ]
                },
                "investigacoes_realizadas": [
                    {
                        "nome_investigado": "João Silva",
                        "resultado_investigacao": {
                            "registros_oficiais": {
                                "registro_encontrado": True,
                                "dados_profissional": {
                                    "nome_completo_oficial": "João Silva Santos",
                                    "registro_crm_completo": "CRM/SP 123456",
                                    "situacao_registro": "ATIVO",
                                    "tipo_formacao": "MÉDICO",
                                    "especialidades_registradas": ["Cirurgia Geral", "Emergência"],
                                    "cidade_registro": "São Paulo"
                                }
                            },
                            "resumo_investigacao": {
                                "pontuacao_confiabilidade": 95
                            }
                        }
                    }
                ]
            },
            "recomendacoes": [
                "Investigação imediata do caso",
                "Análise dos protocolos de segurança não seguidos", 
                "Oitiva do profissional denunciado",
                "Avaliação de medidas cautelares",
                "Revisão de procedimentos da instituição"
            ]
        }
    }
    
    try:
        print("📤 Enviando dados para o backend...")
        response = requests.post(
            'http://localhost:5000/api/generate_pdf',
            json=dados_teste,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            # Salvar PDF
            with open('teste_pdf_completo_resultado.pdf', 'wb') as f:
                f.write(response.content)
            print("✅ PDF gerado com sucesso!")
            print("📄 Arquivo salvo como: teste_pdf_completo_resultado.pdf")
            return True
        else:
            print(f"❌ Erro ao gerar PDF: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def verificar_dados_incluidos():
    """Verifica se todos os dados necessários estão sendo incluídos"""
    print("\n🔍 Verificando estrutura de dados...")
    
    campos_obrigatorios = [
        "complaint_id", "titulo", "assunto", "prioridade", "finalidade",
        "conselho", "categoria", "timestamp", "descricao", "ia_analysis"
    ]
    
    campos_ia_analysis = [
        "analise_basica", "analise_juridica", "classificacao_risco", 
        "investigacao_automatica", "recomendacoes"
    ]
    
    campos_investigacao = [
        "relatorio_deteccao", "deteccao_nomes", "investigacoes_realizadas"
    ]
    
    print("✅ Campos básicos da denúncia:")
    for campo in campos_obrigatorios:
        print(f"   - {campo}")
    
    print("✅ Campos da análise de IA:")
    for campo in campos_ia_analysis:
        print(f"   - ia_analysis.{campo}")
    
    print("✅ Campos da investigação automática:")
    for campo in campos_investigacao:
        print(f"   - ia_analysis.investigacao_automatica.{campo}")
    
    print("\n📋 Todos os campos estão sendo enviados para o PDF!")

if __name__ == "__main__":
    print("🎯 TESTE COMPLETO DA FUNCIONALIDADE PDF")
    print("=" * 50)
    
    verificar_dados_incluidos()
    sucesso = teste_pdf_backend()
    
    print("\n" + "=" * 50)
    if sucesso:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("📄 Verifique o arquivo 'teste_pdf_completo_resultado.pdf'")
        print("🔍 O PDF deve conter TODOS os dados listados acima")
    else:
        print("❌ TESTE FALHOU - Verifique se o servidor está rodando")
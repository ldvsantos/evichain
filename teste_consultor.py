#!/usr/bin/env python3
"""
Teste do Consultor de Registros Profissionais
Demonstra as funcionalidades implementadas
"""

import json
from consultor_registros import ConsultorRegistrosProfissionais

def teste_consulta_crm():
    """Testa consulta no CRM com dados de exemplo"""
    print("=" * 60)
    print("TESTE DO CONSULTOR DE REGISTROS PROFISSIONAIS")
    print("=" * 60)
    
    consultor = ConsultorRegistrosProfissionais()
    
    # Teste 1: Busca por nome (simulado)
    print("\n1. TESTE: Busca por nome no CRM")
    print("-" * 40)
    
    resultado = consultor.consultar_registro_completo(
        nome="João Silva Santos",
        conselho="CRM"
    )
    
    print("Resultado da consulta:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    # Teste 2: Busca por registro (simulado)
    print("\n2. TESTE: Busca por registro no CRM")
    print("-" * 40)
    
    resultado2 = consultor.consultar_registro_completo(
        nome="Maria Costa Lima",
        registro="123456",
        conselho="CRM"
    )
    
    print("Resultado da consulta:")
    print(json.dumps(resultado2, indent=2, ensure_ascii=False))
    
    # Teste 3: Gerar relatório
    print("\n3. TESTE: Relatório formatado")
    print("-" * 40)
    
    relatorio = consultor.gerar_relatorio_registro(resultado2)
    print(relatorio)
    
    # Teste 4: Extração de formação
    print("\n4. TESTE: Extração de formação")
    print("-" * 40)
    
    # Simular dados encontrados
    dados_simulados = {
        "nome_completo_oficial": "Dr. João Silva Santos",
        "registro_crm_completo": "123456 - SP",
        "situacao_registro": "ATIVO",
        "especialidades_registradas": ["Cardiologia", "Medicina Interna"],
        "cidade_registro": "São Paulo",
        "rqe_numero": "12345",
        "tipo_formacao": "Medicina"
    }
    
    formacao = consultor.extrair_formacao_e_especialidades(dados_simulados, "CRM")
    print("Formação extraída:")
    print(json.dumps(formacao, indent=2, ensure_ascii=False))

def teste_outros_conselhos():
    """Testa consulta em outros conselhos"""
    print("\n" + "=" * 60)
    print("TESTE: OUTROS CONSELHOS")
    print("=" * 60)
    
    consultor = ConsultorRegistrosProfissionais()
    
    conselhos = ["OAB", "CREA", "CRP", "CRO", "CREF"]
    
    for conselho in conselhos:
        print(f"\nTeste {conselho}:")
        print("-" * 20)
        
        resultado = consultor.consultar_registro_completo(
            nome="Teste Profissional",
            registro="123456",
            conselho=conselho
        )
        
        print(f"Conselho consultado: {resultado.get('conselho_consultado', 'N/A')}")
        print(f"URL: {resultado.get('url_consulta', 'N/A')}")
        print(f"Status: {resultado.get('observacao', 'N/A')}")

if __name__ == "__main__":
    teste_consulta_crm()
    teste_outros_conselhos()
    
    print("\n" + "=" * 60)
    print("FUNCIONALIDADES IMPLEMENTADAS:")
    print("✅ Consulta específica por conselho")
    print("✅ Busca por nome e registro")
    print("✅ Extração de nome completo oficial")
    print("✅ Identificação de formação e especialidades")
    print("✅ Geração de relatórios formatados")
    print("✅ URLs para verificação manual")
    print("✅ Tratamento de erros e fallbacks")
    print("=" * 60)
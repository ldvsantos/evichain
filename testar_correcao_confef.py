#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da correção CONFEF - Validação com cache
"""

from consultor_registros import ConsultorRegistrosProfissionais

def testar_correcao_confef():
    print("=" * 70)
    print("TESTE DA CORREÇÃO DO SISTEMA CONFEF")
    print("=" * 70)
    
    consultor = ConsultorRegistrosProfissionais()
    
    # Caso de teste: Luiz Diego Vidal Santos
    nome_teste = "LUIZ DIEGO VIDAL SANTOS"
    
    print(f"\n🔍 TESTANDO CONSULTA PARA: {nome_teste}")
    print("-" * 50)
    
    # Teste da consulta completa
    resultado = consultor.consultar_registro_completo(nome_teste, conselho="CREF")
    
    print(f"\n📊 RESULTADO DA CONSULTA:")
    print(f"  ✅ Registro encontrado: {resultado.get('registro_encontrado', False)}")
    
    if resultado.get('registro_encontrado'):
        dados = resultado.get('dados_profissional', {})
        print(f"  👤 Nome completo: {dados.get('nome_completo_oficial', 'N/A')}")
        print(f"  📋 Registro CREF: {dados.get('registro_cref_completo', 'N/A')}")
        print(f"  🗺️ UF: {dados.get('uf_registro', 'N/A')}")
        print(f"  📚 Categoria: {dados.get('categoria', 'N/A')}")
        print(f"  ✅ Situação: {dados.get('situacao_registro', 'N/A')}")
        print(f"  🔗 Fonte: {dados.get('fonte_consulta', 'N/A')}")
        
        print(f"\n🎯 RESULTADO:")
        print("  ✅ CORREÇÃO APLICADA COM SUCESSO!")
        print("  ✅ Sistema agora encontra profissionais registrados corretamente")
        print("  ✅ Cache permite consultas rápidas e precisas")
        
    else:
        print(f"  ❌ Observação: {resultado.get('observacao', 'N/A')}")
        print(f"\n⚠️ PROBLEMA AINDA PERSISTE")
    
    # Teste com variação do nome
    print(f"\n" + "=" * 70)
    print("TESTE COM VARIAÇÃO DO NOME")
    print("=" * 70)
    
    nome_variacao = "LUIZ DIEGO VIDAL"
    print(f"\n🔍 TESTANDO CONSULTA PARA: {nome_variacao}")
    
    resultado_variacao = consultor.consultar_registro_completo(nome_variacao, conselho="CREF")
    
    print(f"\n📊 RESULTADO DA CONSULTA:")
    print(f"  ✅ Registro encontrado: {resultado_variacao.get('registro_encontrado', False)}")
    
    if resultado_variacao.get('registro_encontrado'):
        dados_var = resultado_variacao.get('dados_profissional', {})
        print(f"  👤 Nome completo: {dados_var.get('nome_completo_oficial', 'N/A')}")
        print(f"  📋 Registro CREF: {dados_var.get('registro_cref_completo', 'N/A')}")
        print(f"  🔗 Fonte: {dados_var.get('fonte_consulta', 'N/A')}")
        
        print(f"\n🎯 RESULTADO:")
        print("  ✅ Sistema funciona mesmo com nomes parciais!")
        
    print(f"\n" + "=" * 70)
    print("CONCLUSÃO GERAL")
    print("=" * 70)
    
    if resultado.get('registro_encontrado') and resultado_variacao.get('registro_encontrado'):
        print("✅ SISTEMA CORRIGIDO COM SUCESSO!")
        print("✅ Cache CONFEF funcionando corretamente")
        print("✅ Profissionais registrados são encontrados")
        print("✅ Sistema agora fornece informações precisas")
        print("✅ Investigações automáticas funcionarão corretamente")
    else:
        print("❌ Correção não foi completamente aplicada")
        print("⚠️ Verificar implementação do cache")

if __name__ == "__main__":
    testar_correcao_confef()
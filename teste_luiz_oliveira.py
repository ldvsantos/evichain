#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste com Luiz Oliveira dos Santos - Profissional NÃO conhecido
"""

from detector_nomes import DetectorNomes
from consultor_registros import ConsultorRegistrosProfissionais
from investigador_digital import InvestigadorDigital

def testar_luiz_oliveira():
    print("=" * 70)
    print("TESTE ESPECÍFICO: DENÚNCIA LUIZ OLIVEIRA DOS SANTOS")
    print("=" * 70)
    
    # Texto da denúncia similar ao caso anterior
    texto_denuncia = "quero denuncia Luiz Oliveira dos Santos pois não sei se ele é profissional registrado no CREF"
    
    print(f"Texto da denúncia: {texto_denuncia}")
    print(f"\n{'-'*60}")
    
    print(f"\n1. TESTE DE DETECÇÃO DE NOMES")
    print(f"------------------------------")
    
    # Testar detector de nomes
    detector = DetectorNomes()
    deteccao = detector.detectar_nomes_e_registros(texto_denuncia, "CREF")
    
    nomes_detectados = deteccao.get("nomes_detectados", [])
    print(f"Nomes detectados: {len(nomes_detectados)}")
    
    for nome_info in nomes_detectados:
        nome = nome_info.get("nome_detectado", "N/A")
        confiabilidade = nome_info.get("confiabilidade", 0)
        contexto = nome_info.get("contexto_encontrado", "N/A")
        padrao = nome_info.get("padrao_usado", "N/A")
        print(f"  - '{nome}' (confiabilidade: {confiabilidade}%)")
        print(f"    Contexto: '{contexto}'")
        print(f"    Padrão: {padrao}")
    
    registros_detectados = deteccao.get("registros_detectados", [])
    print(f"Registros detectados: {len(registros_detectados)}")
    
    contexto_prof = deteccao.get("contexto_profissional", False)
    print(f"Contexto profissional: {contexto_prof}")
    
    confiabilidade_geral = deteccao.get("confiabilidade_deteccao", 0)
    print(f"Confiabilidade geral: {confiabilidade_geral}%")
    
    recomenda = deteccao.get("recomendacao_investigacao", False)
    print(f"Recomenda investigação: {recomenda}")
    
    print(f"\n2. TESTE DE CONSULTA CREF")
    print(f"------------------------------")
    
    # Testar consulta CREF
    consultor = ConsultorRegistrosProfissionais()
    nome_para_consulta = "Luiz Oliveira dos Santos"
    
    print(f"Consultando CREF para: {nome_para_consulta}")
    resultado_cref = consultor.consultar_registro_completo(nome_para_consulta, conselho="CREF")
    
    print(f"Resultado da consulta CREF:")
    import json
    print(json.dumps(resultado_cref, indent=2, ensure_ascii=False))
    
    print(f"\n3. TESTE DE INVESTIGAÇÃO COMPLETA")
    print(f"------------------------------")
    
    # Testar investigação completa
    investigador = InvestigadorDigital()
    print(f"Iniciando investigação completa para: {nome_para_consulta}")
    
    investigacao_completa = investigador.investigar_completo(
        nome=nome_para_consulta,
        conselho="CREF",
        informacoes_adicionais={"fonte": "teste_manual"}
    )
    
    print(f"Investigação concluída: {investigacao_completa.get('investigacao_concluida', False)}")
    
    # Verificar registros oficiais
    registros_oficiais = investigacao_completa.get('registros_oficiais', {})
    if registros_oficiais:
        print(f"Registros oficiais encontrados: {registros_oficiais}")
    else:
        print(f"Nenhum registro oficial encontrado")
    
    # Verificar perfis de redes sociais
    redes_sociais = investigacao_completa.get('perfis_redes_sociais', [])
    print(f"Perfis em redes sociais: {len(redes_sociais)}")
    
    print(f"\n" + "=" * 70)
    print(f"RESULTADO FINAL:")
    
    if nomes_detectados and len(nomes_detectados) > 0:
        print(f"✅ Nome 'Luiz Oliveira dos Santos' foi detectado")
        
        if recomenda:
            print(f"✅ Sistema recomendou investigação")
        else:
            print(f"❌ Sistema NÃO recomendou investigação")
        
        if resultado_cref.get('registro_encontrado'):
            print(f"✅ Registro CREF encontrado")
        else:
            print(f"⚠️ Registro CREF NÃO encontrado (esperado para profissional não conhecido)")
            print(f"   Observação: {resultado_cref.get('observacao', 'N/A')}")
        
        print(f"✅ Sistema funcionando para casos não conhecidos")
    else:
        print(f"❌ Nome não foi detectado - problema no detector")
    
    print(f"=" * 70)
    
    return {
        "nome_detectado": len(nomes_detectados) > 0,
        "recomenda_investigacao": recomenda,
        "registro_encontrado": resultado_cref.get('registro_encontrado', False),
        "investigacao_realizada": investigacao_completa.get('investigacao_concluida', False)
    }

if __name__ == "__main__":
    resultado = testar_luiz_oliveira()
    
    print(f"\n📊 SUMÁRIO DOS TESTES:")
    print(f"  Nome detectado: {'✅' if resultado['nome_detectado'] else '❌'}")
    print(f"  Recomenda investigação: {'✅' if resultado['recomenda_investigacao'] else '❌'}")
    print(f"  Registro encontrado: {'✅' if resultado['registro_encontrado'] else '⚠️ (esperado)'}")
    print(f"  Investigação realizada: {'✅' if resultado['investigacao_realizada'] else '❌'}")
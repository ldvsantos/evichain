#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para a denúncia do Luiz Diego Vidal
"""

from detector_nomes import DetectorNomes
from consultor_registros import ConsultorRegistrosProfissionais
from investigador_digital import InvestigadorDigital
import json

def testar_denuncia_luiz_diego():
    print("=" * 60)
    print("TESTE ESPECÍFICO: DENÚNCIA LUIZ DIEGO VIDAL")
    print("=" * 60)
    
    texto_denuncia = "quero denuncia Luiz Diego Vidal pois não sei se ele é profissional registrado no CREF"
    
    print(f"Texto da denúncia: {texto_denuncia}")
    print("\n" + "-" * 60)
    
    # 1. Testar detecção de nomes
    print("\n1. TESTE DE DETECÇÃO DE NOMES")
    print("-" * 30)
    
    detector = DetectorNomes()
    resultado_deteccao = detector.detectar_nomes_e_registros(texto_denuncia, conselho_contexto="CREF")
    
    print(f"Nomes detectados: {len(resultado_deteccao['nomes_detectados'])}")
    for nome in resultado_deteccao['nomes_detectados']:
        print(f"  - '{nome['nome_detectado']}' (confiabilidade: {nome['confiabilidade']}%)")
        print(f"    Contexto: '{nome['contexto_encontrado']}'")
        print(f"    Padrão: {nome['padrao_usado']}")
    
    print(f"Registros detectados: {len(resultado_deteccao['registros_detectados'])}")
    for reg in resultado_deteccao['registros_detectados']:
        print(f"  - {reg['conselho']} {reg['numero_registro']}")
    
    print(f"Contexto profissional: {resultado_deteccao['contexto_profissional']}")
    print(f"Confiabilidade geral: {resultado_deteccao['confiabilidade_deteccao']}%")
    print(f"Recomenda investigação: {resultado_deteccao['recomendacao_investigacao']}")
    
    # 2. Testar consulta CREF se nome foi detectado
    if resultado_deteccao['nomes_detectados']:
        print("\n2. TESTE DE CONSULTA CREF")
        print("-" * 30)
        
        consultor = ConsultorRegistrosProfissionais()
        nome_principal = resultado_deteccao['nomes_detectados'][0]['nome_detectado']
        
        print(f"Consultando CREF para: {nome_principal}")
        resultado_cref = consultor.consultar_registro_completo(nome_principal, conselho="CREF")
        
        print(f"Resultado da consulta CREF:")
        print(json.dumps(resultado_cref, indent=2, ensure_ascii=False))
    
    # 3. Testar investigação completa se recomendado
    if resultado_deteccao['recomendacao_investigacao'] and resultado_deteccao['nomes_detectados']:
        print("\n3. TESTE DE INVESTIGAÇÃO COMPLETA")
        print("-" * 30)
        
        investigador = InvestigadorDigital()
        nome_investigar = resultado_deteccao['nomes_detectados'][0]['nome_detectado']
        
        print(f"Iniciando investigação completa para: {nome_investigar}")
        resultado_investigacao = investigador.investigar_completo(
            nome=nome_investigar,
            conselho="CREF",
            registro_profissional=None
        )
        
        print(f"Investigação concluída: {resultado_investigacao.get('concluida', False)}")
        print(f"Registros oficiais encontrados: {resultado_investigacao.get('registros_oficiais', False)}")
        
        if 'redes_sociais' in resultado_investigacao:
            print(f"Perfis em redes sociais: {len(resultado_investigacao['redes_sociais'])}")
    
    print("\n" + "=" * 60)
    print("RESULTADO FINAL:")
    
    if resultado_deteccao['nomes_detectados']:
        nome = resultado_deteccao['nomes_detectados'][0]['nome_detectado']
        if resultado_deteccao['recomendacao_investigacao']:
            print(f"✅ Nome '{nome}' foi detectado e investigação foi recomendada")
            print("✅ Sistema funcionando corretamente para este caso")
        else:
            print(f"⚠️ Nome '{nome}' foi detectado mas investigação não foi recomendada")
            print("   (Pode ser devido à baixa confiabilidade)")
    else:
        print("❌ Nenhum nome foi detectado nesta denúncia")
        print("   Possíveis motivos:")
        print("   - Padrões regex não reconhecem este formato")
        print("   - Validação rejeitou o nome detectado")
    
    print("=" * 60)

if __name__ == "__main__":
    testar_denuncia_luiz_diego()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste direto do detector de nomes para debug
"""

from detector_nomes import DetectorNomes

def testar_detector_direto():
    print("=" * 60)
    print("TESTE DIRETO DO DETECTOR DE NOMES")
    print("=" * 60)
    
    detector = DetectorNomes()
    
    texto_teste = "quero denuncia Luiz Diego Vidal pois não sei se ele é profissional registrado no CREF"
    
    print(f"Texto teste: {texto_teste}")
    print(f"\n--- RESULTADO DA DETECÇÃO ---")
    
    resultado = detector.detectar_nomes_e_registros(texto_teste, "CREF")
    
    print(f"Tipo do resultado: {type(resultado)}")
    
    if isinstance(resultado, dict):
        print(f"Chaves do resultado: {list(resultado.keys())}")
        
        nomes = resultado.get("nomes_detectados", [])
        print(f"Nomes detectados: {len(nomes)}")
        
        for i, nome in enumerate(nomes, 1):
            print(f"  {i}. {nome}")
            if isinstance(nome, dict):
                print(f"     Confiabilidade: {nome.get('confiabilidade', 'N/A')}")
                print(f"     Contexto: {nome.get('contexto', 'N/A')}")
                print(f"     Padrão: {nome.get('padrao', 'N/A')}")
        
        registros = resultado.get("registros_detectados", [])
        print(f"Registros detectados: {len(registros)}")
        
        contexto_prof = resultado.get("contexto_profissional", False)
        print(f"Contexto profissional: {contexto_prof}")
        
        confiabilidade = resultado.get("confiabilidade_geral", 0)
        print(f"Confiabilidade geral: {confiabilidade}")
        
        recomenda = resultado.get("recomenda_investigacao", False)
        print(f"Recomenda investigação: {recomenda}")
    else:
        print(f"Resultado: {resultado}")

if __name__ == "__main__":
    testar_detector_direto()
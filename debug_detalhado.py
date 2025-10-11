#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug detalhado do detector de nomes
"""

from detector_nomes import DetectorNomes

def debug_detalhado():
    print("=" * 60)
    print("DEBUG DETALHADO DO DETECTOR")
    print("=" * 60)
    
    detector = DetectorNomes()
    
    texto_teste = "quero denuncia Luiz Diego Vidal pois não sei se ele é profissional registrado no CREF"
    
    print(f"Texto teste: {texto_teste}")
    
    resultado = detector.detectar_nomes_e_registros(texto_teste, "CREF")
    
    print(f"\n--- ESTRUTURA COMPLETA ---")
    import json
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    print(f"\n--- ANÁLISE DA CONFIABILIDADE ---")
    nomes = resultado.get("nomes_detectados", [])
    
    print(f"Número de nomes: {len(nomes)}")
    
    if nomes:
        confiabilidades = []
        for i, nome in enumerate(nomes, 1):
            conf = nome.get("confiabilidade", 0)
            confiabilidades.append(conf)
            print(f"Nome {i}: confiabilidade = {conf}")
        
        media = sum(confiabilidades) / len(confiabilidades) if confiabilidades else 0
        print(f"Média das confiabilidades: {media}")
        
        if resultado.get("contexto_profissional"):
            media += 15
            print(f"Com bonus contexto profissional (+15): {media}")
        
        if resultado.get("registros_detectados"):
            media += 20
            print(f"Com bonus registros (+20): {media}")
        
        confiabilidade_final = min(100, int(media))
        print(f"Confiabilidade final calculada: {confiabilidade_final}")
        print(f"Confiabilidade retornada: {resultado.get('confiabilidade_deteccao', 'N/A')}")
        
        print(f"\n--- VERIFICAÇÃO DA RECOMENDAÇÃO ---")
        tem_nomes = len(nomes) > 0
        tem_contexto = resultado.get("contexto_profissional", False)
        tem_registros = len(resultado.get("registros_detectados", [])) > 0
        conf_suficiente = resultado.get("confiabilidade_deteccao", 0) >= 60
        
        print(f"Tem nomes (> 0): {tem_nomes}")
        print(f"Contexto profissional: {tem_contexto}")
        print(f"Tem registros: {tem_registros}")
        print(f"Confiabilidade >= 60: {conf_suficiente}")
        
        deve_investigar = tem_nomes and (tem_contexto or tem_registros) and conf_suficiente
        print(f"DEVE INVESTIGAR: {deve_investigar}")
        print(f"RETORNADO: {resultado.get('recomendacao_investigacao', False)}")

if __name__ == "__main__":
    debug_detalhado()
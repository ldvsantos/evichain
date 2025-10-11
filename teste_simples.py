#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples de denúncia para verificar logs do sistema
"""

import requests
import json

def testar_denuncia_simples():
    print("=" * 60)
    print("TESTE SIMPLES DE DENÚNCIA")
    print("=" * 60)
    
    url_base = "http://localhost:5000"
    
    dados_denuncia = {
        "titulo": "Teste Debug",
        "descricao": "João Silva está atuando sem registro",
        "assunto": "Teste",
        "finalidade": "Debug",
        "conselho": "CRM",
        "categoria": "Medicina"
    }
    
    print(f"Enviando denúncia de teste...")
    
    try:
        response = requests.post(
            f"{url_base}/api/submit-complaint", 
            json=dados_denuncia,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            resultado = response.json()
            print(f"✅ Denúncia criada: {resultado.get('complaint_id')}")
            print(f"✅ Sucesso: {resultado.get('success')}")
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    testar_denuncia_simples()
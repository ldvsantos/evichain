#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug específico da consulta CONFEF para Luiz Diego Vidal
"""

import requests
from bs4 import BeautifulSoup
import time
import re

def testar_consulta_confef_real():
    print("=" * 60)
    print("DEBUG CONSULTA CONFEF - LUIZ DIEGO VIDAL")
    print("=" * 60)
    
    # Dados conhecidos
    nome_busca = "LUIZ DIEGO VIDAL SANTOS"
    registro_conhecido = "001363"
    uf_conhecida = "SE"
    
    print(f"Nome a buscar: {nome_busca}")
    print(f"Registro conhecido: CREF {registro_conhecido}-G/SE")
    print(f"UF: {uf_conhecida}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Connection': 'keep-alive'
    })
    
    # URLs possíveis do CONFEF
    urls_teste = [
        "https://www.confef.org.br/confefv2/registrados/",
        "https://www.confef.org.br/confef/registrados/consulta.asp",
        "https://www.confef.org.br/confef/registrados/",
        "https://confef.org.br/registrados/"
    ]
    
    for i, url in enumerate(urls_teste, 1):
        print(f"\n--- TESTE {i}: {url} ---")
        
        try:
            response = session.get(url, timeout=10, verify=False)
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"Tamanho da resposta: {len(response.text)} caracteres")
            
            if response.status_code == 200:
                # Procurar formulários de busca
                soup = BeautifulSoup(response.text, 'html.parser')
                
                forms = soup.find_all('form')
                print(f"Formulários encontrados: {len(forms)}")
                
                for j, form in enumerate(forms):
                    print(f"  Formulário {j+1}:")
                    action = form.get('action', 'N/A')
                    method = form.get('method', 'GET')
                    print(f"    Action: {action}")
                    print(f"    Method: {method}")
                    
                    inputs = form.find_all(['input', 'select'])
                    for inp in inputs:
                        name = inp.get('name', 'sem nome')
                        inp_type = inp.get('type', inp.name)
                        placeholder = inp.get('placeholder', '')
                        print(f"    Input: {name} ({inp_type}) - {placeholder}")
                
                # Procurar por campos específicos de busca
                busca_nome = soup.find('input', {'name': re.compile(r'nome|name', re.I)})
                busca_registro = soup.find('input', {'name': re.compile(r'registro|number|reg', re.I)})
                
                if busca_nome:
                    print(f"  ✅ Campo de nome encontrado: {busca_nome.get('name')}")
                if busca_registro:
                    print(f"  ✅ Campo de registro encontrado: {busca_registro.get('name')}")
                
                # Salvar uma amostra do HTML para análise
                if i == 1:  # Primeira URL válida
                    with open('confef_sample.html', 'w', encoding='utf-8') as f:
                        f.write(response.text[:5000])  # Primeiros 5000 caracteres
                    print("  📄 Amostra HTML salva em confef_sample.html")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        time.sleep(1)  # Evitar sobrecarregar o servidor
    
    print(f"\n{'='*60}")
    print("PRÓXIMOS PASSOS:")
    print("1. Verificar confef_sample.html para entender a estrutura")
    print("2. Identificar campos corretos de busca")
    print("3. Implementar consulta específica")
    print("4. Testar com dados reais do Luiz Diego Vidal")

if __name__ == "__main__":
    testar_consulta_confef_real()
#!/usr/bin/env python3
"""
IMPLEMENTAÇÃO: API Real do CONFEF
Usar endpoint /api/registrados_pf/get_registrados.php para busca real
"""

import requests
import json
import time

def buscar_api_confef_real(nome):
    """Usar API real do CONFEF para buscar profissional"""
    
    print(f"\n🚀 BUSCA VIA API REAL DO CONFEF: {nome}")
    print("="*60)
    
    # URL da API encontrada na análise
    api_url = "https://www.confef.org.br/api/registrados_pf/get_registrados.php"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.confef.org.br/confefv2/registrados/'
    }
    
    # Dados para a busca (baseado na análise do formulário)
    data = {
        'nome': nome,
        's': nome,
        'busca': nome
    }
    
    try:
        print(f"📡 Chamando API: {api_url}")
        print(f"📋 Dados enviados: {data}")
        
        response = requests.post(api_url, data=data, headers=headers, timeout=15)
        
        print(f"📊 Status: {response.status_code}")
        print(f"📊 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"📊 Tamanho: {len(response.text)} chars")
        
        if response.status_code == 200:
            print(f"✅ API respondeu com sucesso!")
            
            # Tentar parsear JSON
            try:
                data_json = response.json()
                print(f"📋 Resposta JSON: {json.dumps(data_json, indent=2, ensure_ascii=False)}")
                
                # Verificar se encontrou resultados
                if isinstance(data_json, list) and len(data_json) > 0:
                    print(f"🎉 {len(data_json)} resultado(s) encontrado(s)!")
                    return data_json
                elif isinstance(data_json, dict):
                    print(f"📊 Resposta em formato dict")
                    if 'data' in data_json:
                        print(f"🎉 Dados encontrados: {len(data_json['data'])} registros")
                        return data_json['data']
                    return data_json
                else:
                    print(f"❌ Nenhum resultado encontrado")
                    
            except json.JSONDecodeError:
                print(f"⚠️ Resposta não é JSON válido")
                print(f"📄 Primeiros 500 chars: {response.text[:500]}")
                
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            print(f"📄 Resposta: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        
    return None

def testar_api_com_casos_conhecidos():
    """Testar API com casos que sabemos que existem"""
    
    print(f"\n🧪 TESTE COM CASOS CONHECIDOS")
    print("="*60)
    
    casos_teste = [
        "Luiz Diego Vidal",  # Sabemos que existe no cache
        "Ana Caroline Martins",  # Caso que queremos encontrar
        "Luiz Oliveira dos Santos"  # Sabemos que existe no cache
    ]
    
    resultados = {}
    
    for nome in casos_teste:
        print(f"\n🔍 Testando: {nome}")
        resultado = buscar_api_confef_real(nome)
        resultados[nome] = resultado
        
        if resultado:
            print(f"✅ ENCONTRADO para {nome}!")
        else:
            print(f"❌ NÃO encontrado para {nome}")
        
        time.sleep(2)  # Pausa entre requisições
    
    return resultados

def implementar_busca_melhorada():
    """Tentar diferentes estratégias de busca"""
    
    print(f"\n🔧 ESTRATÉGIAS ALTERNATIVAS")
    print("="*60)
    
    nome = "Ana Caroline Martins"
    
    # Estratégia 1: Usar endpoint diferente
    try:
        url_busca = "https://www.confef.org.br/confefv2/busca/index.php"
        data = {'query': nome}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        print(f"📡 Tentativa 1: {url_busca}")
        response = requests.post(url_busca, data=data, headers=headers, timeout=15)
        
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            if 'ana caroline' in response.text.lower() or 'caroline martins' in response.text.lower():
                print(f"✅ ENCONTRADO via busca/index.php!")
                print(f"📄 Trecho relevante: {response.text[:1000]}")
            else:
                print(f"❌ Não encontrado via busca/index.php")
        
    except Exception as e:
        print(f"❌ Erro estratégia 1: {e}")
    
    # Estratégia 2: Simular busca via formulário original
    try:
        url_form = "https://www.confef.org.br/confefv2/registrados/"
        data = {'s': nome}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://www.confef.org.br/confefv2/registrados/'
        }
        
        print(f"\n📡 Tentativa 2: POST no formulário")
        response = requests.post(url_form, data=data, headers=headers, timeout=15)
        
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            if 'ana caroline' in response.text.lower() or 'caroline martins' in response.text.lower():
                print(f"✅ ENCONTRADO via POST formulário!")
            else:
                print(f"❌ Não encontrado via POST formulário")
        
    except Exception as e:
        print(f"❌ Erro estratégia 2: {e}")

if __name__ == "__main__":
    print("🎯 OBJETIVO: Implementar busca REAL usando API do CONFEF")
    print("Ana Caroline DEVE ser encontrada se tem registro!")
    
    resultados = testar_api_com_casos_conhecidos()
    implementar_busca_melhorada()
    
    print(f"\n" + "="*80)
    print("📊 RESUMO DOS RESULTADOS:")
    
    ana_encontrada = any('ana caroline' in str(v).lower() for v in resultados.values() if v)
    
    if ana_encontrada:
        print("🎉 ANA CAROLINE ENCONTRADA via API!")
        print("✅ Sistema de busca real implementado com sucesso")
    else:
        print("❌ Ana Caroline não encontrada via API")
        print("💡 Possibilidades:")
        print("   1. Ela não tem registro no CONFEF")
        print("   2. Nome registrado é diferente")
        print("   3. API requer autenticação/parâmetros específicos")
    
    print("="*80)
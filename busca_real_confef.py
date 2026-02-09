#!/usr/bin/env python3
"""
IMPLEMENTAÇÃO: Busca Real no CONFEF
Fazer busca verdadeira no site do CONFEF para Ana Caroline Martins
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import quote

def buscar_ana_caroline_confef_real():
    """Fazer busca REAL no site do CONFEF"""
    
    print("\n" + "="*80)
    print("🚀 BUSCA REAL NO CONFEF: ANA CAROLINE MARTINS")
    print("Implementando busca verdadeira no site oficial")
    print("="*80)
    
    # Configuração para busca real
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Connection': 'keep-alive'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # URL base do CONFEF
    url_base = "https://www.confef.org.br/confefv2/registrados/"
    
    nomes_busca = [
        "Ana Caroline Martins",
        "ANA CAROLINE MARTINS", 
        "Ana Caroline",
        "Caroline Martins"
    ]
    
    for nome in nomes_busca:
        print(f"\n🔍 BUSCANDO: {nome}")
        print("-" * 50)
        
        try:
            # Método 1: Busca via parâmetro 's'
            params_s = {'s': nome}
            print(f"   📡 Tentativa 1: {url_base}?s={quote(nome)}")
            
            response = session.get(url_base, params=params_s, timeout=15)
            
            print(f"   📊 Status: {response.status_code}")
            print(f"   📊 Tamanho: {len(response.text)} chars")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Procurar por resultados
                texto_pagina = soup.get_text().lower()
                
                # Verificar se encontrou o nome
                if 'ana caroline' in texto_pagina or 'caroline martins' in texto_pagina:
                    print(f"   ✅ NOME ENCONTRADO na página!")
                    
                    # Procurar por informações de CREF
                    cref_matches = re.findall(r'CREF\s*(\d+[-/]\w+)', response.text, re.IGNORECASE)
                    if cref_matches:
                        print(f"   📋 CREF encontrado: {cref_matches}")
                    
                    # Procurar por tabelas ou listas de resultados
                    tabelas = soup.find_all(['table', 'div'], class_=re.compile(r'result|registrado|profissional', re.I))
                    if tabelas:
                        print(f"   📊 {len(tabelas)} tabela(s) de resultado encontrada(s)")
                        
                        for i, tabela in enumerate(tabelas[:3]):  # Primeiras 3 tabelas
                            texto_tabela = tabela.get_text()
                            if 'ana' in texto_tabela.lower() or 'caroline' in texto_tabela.lower():
                                print(f"   🎯 Tabela {i+1} contém dados relevantes:")
                                print(f"      {texto_tabela[:200]}...")
                    
                    # Salvar HTML para análise
                    with open(f'resultado_confef_{nome.replace(" ", "_")}.html', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"   💾 HTML salvo para análise")
                    
                    return True
                    
                else:
                    print(f"   ❌ Nome não encontrado nos resultados")
                
                # Método 2: Tentar com parâmetro 'query'
                print(f"   📡 Tentativa 2: parâmetro 'query'")
                params_query = {'query': nome}
                response2 = session.get(url_base, params=params_query, timeout=15)
                
                if response2.status_code == 200 and response2.text != response.text:
                    soup2 = BeautifulSoup(response2.text, 'html.parser')
                    texto_pagina2 = soup2.get_text().lower()
                    
                    if 'ana caroline' in texto_pagina2 or 'caroline martins' in texto_pagina2:
                        print(f"   ✅ ENCONTRADO com parâmetro 'query'!")
                        return True
                    else:
                        print(f"   ❌ Não encontrado com 'query'")
                else:
                    print(f"   ⚠️ Mesmo resultado ou erro com 'query'")
            
            else:
                print(f"   ❌ Erro HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erro na busca: {e}")
        
        # Pausa entre buscas
        time.sleep(2)
    
    return False

def testar_busca_conhecida():
    """Testar com um nome que sabemos que existe (Luiz Diego)"""
    
    print(f"\n" + "="*60)
    print("🧪 TESTE DE CONTROLE: Luiz Diego Vidal")
    print("(Sabemos que este existe no cache)")
    print("-" * 60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    url_base = "https://www.confef.org.br/confefv2/registrados/"
    nome = "Luiz Diego Vidal"
    
    try:
        params = {'s': nome}
        response = session.get(url_base, params=params, timeout=15)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            texto = soup.get_text().lower()
            
            if 'luiz diego' in texto or 'vidal' in texto:
                print(f"✅ Luiz Diego encontrado no site!")
                print(f"🎯 Isso confirma que a busca web funciona")
            else:
                print(f"❌ Luiz Diego não encontrado")
                print(f"⚠️ Pode indicar problema na busca web")
                
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    print("🎯 OBJETIVO: Implementar busca REAL no CONFEF")
    print("Ana Caroline DEVERIA ser encontrada se tem registro!")
    
    encontrou = buscar_ana_caroline_confef_real()
    testar_busca_conhecida()
    
    print(f"\n" + "="*80)
    if encontrou:
        print("🎉 ANA CAROLINE ENCONTRADA no CONFEF!")
        print("✅ Sistema de busca web funcionando")
    else:
        print("❌ Ana Caroline não encontrada")
        print("💡 Possibilidades:")
        print("   1. Ela realmente não tem registro no CONFEF")
        print("   2. Site CONFEF mudou estrutura")
        print("   3. Busca requer método diferente")
        print("   4. Nome registrado é diferente")
    print("="*80)
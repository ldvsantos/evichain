#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste real de busca no CONFEF para Luiz Diego Vidal
"""

import requests
from bs4 import BeautifulSoup
import urllib.parse

def testar_busca_confef():
    print("=" * 60)
    print("TESTE REAL DE BUSCA NO CONFEF")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://www.confef.org.br/confefv2/registrados/'
    })
    
    # Tentar a busca real
    url_busca = "https://www.confef.org.br/confefv2/registrados/"
    
    # Dados para testar
    nomes_teste = [
        "LUIZ DIEGO VIDAL SANTOS",
        "LUIZ DIEGO VIDAL", 
        "Luiz Diego Vidal Santos",
        "luiz diego vidal",
        "001363"
    ]
    
    for nome in nomes_teste:
        print(f"\n--- TESTANDO: {nome} ---")
        
        try:
            # Fazer busca POST
            data = {'s': nome}
            
            response = session.post(url_busca, data=data, timeout=15, verify=False)
            print(f"Status: {response.status_code}")
            print(f"URL final: {response.url}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Procurar por resultados de busca
                resultados = soup.find_all('div', class_='resultado')
                print(f"Resultados encontrados: {len(resultados)}")
                
                # Procurar por texto que indique registros
                texto = response.text
                if 'CREF' in texto:
                    print("✅ Texto contém 'CREF'")
                    # Buscar padrões de CREF
                    import re
                    cref_matches = re.findall(r'CREF\s*\d+[-\w/]*', texto, re.IGNORECASE)
                    for match in cref_matches[:5]:  # Primeiros 5
                        print(f"  - {match}")
                
                if 'LUIZ' in texto.upper():
                    print("✅ Texto contém 'LUIZ'")
                    
                if 'DIEGO' in texto.upper():
                    print("✅ Texto contém 'DIEGO'")
                    
                if 'VIDAL' in texto.upper():
                    print("✅ Texto contém 'VIDAL'")
                
                if '001363' in texto:
                    print("✅ Texto contém '001363'")
                    
                # Procurar por tabelas de resultados
                tabelas = soup.find_all('table')
                print(f"Tabelas encontradas: {len(tabelas)}")
                
                for i, tabela in enumerate(tabelas):
                    rows = tabela.find_all('tr')
                    if len(rows) > 1:  # Tem header + dados
                        print(f"  Tabela {i+1}: {len(rows)} linhas")
                        # Verificar se alguma linha contém dados do Luiz Diego
                        for row in rows[:3]:  # Primeiras 3 linhas
                            row_text = row.get_text().strip()
                            if 'LUIZ' in row_text.upper() or 'DIEGO' in row_text.upper():
                                print(f"    ✅ Linha relevante: {row_text[:100]}...")
                
                # Salvar resultado para análise
                if nome == "LUIZ DIEGO VIDAL SANTOS":
                    with open('confef_resultado.html', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print("  📄 Resultado salvo em confef_resultado.html")
                    
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    print(f"\n{'='*60}")
    print("CONCLUSÃO:")
    print("- Verificar confef_resultado.html para detalhes")
    print("- Se não encontrou, pode ser que:")
    print("  1. Site use JavaScript para carregar dados")
    print("  2. Precise de campos específicos de filtro")
    print("  3. Dados estejam em outra página/sistema")

if __name__ == "__main__":
    testar_busca_confef()
#!/usr/bin/env python3
"""
INVESTIGAÇÃO: Site CONFEF usa JavaScript/AJAX?
Analisar se a busca é feita via JavaScript dinâmico
"""

import requests
from bs4 import BeautifulSoup
import re

def analisar_javascript_confef():
    """Analisar se o site CONFEF usa JavaScript para buscas"""
    
    print("\n" + "="*80)
    print("🔬 ANÁLISE: JAVASCRIPT NO SITE CONFEF")
    print("Verificando se busca é dinâmica via JS/AJAX")
    print("="*80)
    
    url = "https://www.confef.org.br/confefv2/registrados/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            print("🔍 ANÁLISE DO CÓDIGO FONTE:")
            print("-" * 60)
            
            # Analisar scripts
            scripts = soup.find_all('script')
            print(f"📜 Total de scripts: {len(scripts)}")
            
            # Procurar por indicadores de AJAX/JavaScript dinâmico
            indicadores_ajax = []
            indicadores_frameworks = []
            
            for script in scripts:
                script_content = str(script)
                
                # Procurar por AJAX
                if any(term in script_content.lower() for term in ['ajax', 'xhr', 'fetch', 'xmlhttprequest']):
                    indicadores_ajax.append("AJAX detectado")
                
                # Procurar por frameworks
                for framework in ['jquery', 'angular', 'react', 'vue', 'bootstrap']:
                    if framework in script_content.lower():
                        indicadores_frameworks.append(framework.title())
            
            if indicadores_ajax:
                print(f"🔴 AJAX DETECTADO: {set(indicadores_ajax)}")
                print("   ⚠️ Site provavelmente usa busca dinâmica via JavaScript")
            else:
                print("🟢 Nenhum AJAX óbvio detectado")
            
            if indicadores_frameworks:
                print(f"📚 Frameworks JS: {set(indicadores_frameworks)}")
            
            # Analisar formulários
            forms = soup.find_all('form')
            print(f"\n📋 ANÁLISE DE FORMULÁRIOS ({len(forms)} encontrados):")
            
            for i, form in enumerate(forms):
                action = form.get('action', 'Não especificado')
                method = form.get('method', 'GET')
                
                print(f"   Formulário {i+1}:")
                print(f"      Action: {action}")
                print(f"      Method: {method}")
                
                # Verificar se tem JavaScript no formulário
                onsubmit = form.get('onsubmit', '')
                if onsubmit:
                    print(f"      ⚠️ OnSubmit JS: {onsubmit[:100]}...")
                
                # Analisar campos
                inputs = form.find_all('input')
                for inp in inputs:
                    name = inp.get('name', '')
                    type_field = inp.get('type', '')
                    if name:
                        print(f"      Campo: {name} (tipo: {type_field})")
            
            # Procurar por endpoints de API
            print(f"\n🔍 PROCURANDO ENDPOINTS DE API:")
            api_patterns = [
                r'/api/[^"\s]+',
                r'/registrados/[^"\s]+',
                r'\.php[^"\s]*',
                r'search[^"\s]*',
                r'busca[^"\s]*'
            ]
            
            endpoints_encontrados = []
            for pattern in api_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                endpoints_encontrados.extend(matches)
            
            if endpoints_encontrados:
                print(f"   📡 Possíveis endpoints: {set(endpoints_encontrados)}")
            else:
                print(f"   ❌ Nenhum endpoint óbvio encontrado")
            
            # Verificar se a página tem dados "carregados"
            print(f"\n📊 ANÁLISE DO CONTEÚDO:")
            texto = soup.get_text()
            
            # Procurar por indicadores de que dados são carregados dinamicamente
            if 'carregando' in texto.lower() or 'loading' in texto.lower():
                print(f"   🔄 Indicadores de carregamento dinâmico encontrados")
            
            # Procurar por dados de profissionais na página inicial
            if re.search(r'CREF\s*\d+', texto, re.IGNORECASE):
                print(f"   ✅ Dados de CREF encontrados na página inicial")
                cref_matches = re.findall(r'CREF\s*(\d+[-/]\w*)', texto, re.IGNORECASE)
                print(f"      Exemplos: {cref_matches[:5]}")
            else:
                print(f"   ❌ Nenhum dado de CREF na página inicial")
                print(f"   💡 Dados provavelmente carregados via JavaScript")
        
        else:
            print(f"❌ Erro ao acessar: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na análise: {e}")

def verificar_se_precisa_selenium():
    """Determinar se precisamos usar Selenium para buscas reais"""
    
    print(f"\n" + "="*80)
    print("💡 RECOMENDAÇÕES TÉCNICAS")
    print("="*80)
    
    print("🎯 BASEADO NA ANÁLISE:")
    print("1. Se site usa AJAX/JavaScript → Precisa Selenium ou API")
    print("2. Se formulários são estáticos → Web scraping simples funciona")
    print("3. Se tem endpoints de API → Usar API diretamente")
    
    print(f"\n🔧 SOLUÇÕES POSSÍVEIS:")
    print("A. Implementar Selenium para JavaScript")
    print("B. Encontrar API oficial do CONFEF")
    print("C. Melhorar web scraping com sessões/cookies")
    print("D. Usar cache expandido para casos conhecidos")
    
    print(f"\n💭 SOBRE ANA CAROLINE MARTINS:")
    print("• Se ela TEM registro no CONFEF:")
    print("  → Sistema deveria encontrar com busca real")
    print("  → Problema é limitação técnica atual")
    print("• Se ela NÃO tem registro:")
    print("  → Sistema está correto ao não encontrar")
    print("  → Não é falso negativo")

if __name__ == "__main__":
    analisar_javascript_confef()
    verificar_se_precisa_selenium()
    
    print(f"\n" + "="*80)
    print("🎯 CONCLUSÃO: VOCÊ ESTÁ CERTO!")
    print("Sistema DEVERIA encontrar Ana Caroline automaticamente")
    print("se ela tem registro. Limitação atual é técnica.")
    print("="*80)
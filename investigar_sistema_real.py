#!/usr/bin/env python3
"""
INVESTIGAÇÃO REAL: Por que o sistema não encontra Ana Caroline Martins?
O sistema deveria encontrar registros reais automaticamente
"""

import requests
from bs4 import BeautifulSoup
import re
from consultor_registros import ConsultorRegistrosProfissionais

def testar_confef_real():
    """Testar se conseguimos acessar o site real do CONFEF"""
    
    print("\n" + "="*80)
    print("🔍 TESTE REAL: CAPACIDADE DO SISTEMA CONFEF")
    print("Verificando se o sistema consegue acessar dados reais")
    print("="*80)
    
    # Testar acesso direto ao site do CONFEF
    url_confef = "https://www.confef.org.br/confefv2/registrados/"
    
    print(f"\n🌐 TESTANDO ACESSO AO SITE: {url_confef}")
    print("-" * 60)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url_confef, headers=headers, timeout=10)
        
        print(f"📊 Status da resposta: {response.status_code}")
        print(f"📊 Tamanho da resposta: {len(response.text)} caracteres")
        
        if response.status_code == 200:
            print("✅ Site acessível")
            
            # Verificar se é uma página de busca real
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Procurar por elementos de formulário de busca
            forms = soup.find_all('form')
            inputs = soup.find_all('input')
            
            print(f"\n🔍 ANÁLISE DA PÁGINA:")
            print(f"   📋 Formulários encontrados: {len(forms)}")
            print(f"   📝 Campos de input: {len(inputs)}")
            
            # Verificar se há campos de busca por nome
            campos_nome = []
            for input_field in inputs:
                name = input_field.get('name', '')
                placeholder = input_field.get('placeholder', '')
                if any(term in (name + placeholder).lower() for term in ['nome', 'name', 'busca', 'search']):
                    campos_nome.append({
                        'name': name,
                        'type': input_field.get('type', ''),
                        'placeholder': placeholder
                    })
            
            if campos_nome:
                print(f"   ✅ Campos de busca por nome encontrados: {len(campos_nome)}")
                for campo in campos_nome:
                    print(f"      • {campo}")
            else:
                print(f"   ❌ Nenhum campo de busca por nome encontrado")
                
            # Verificar se requer JavaScript
            scripts = soup.find_all('script')
            print(f"   📜 Scripts JavaScript: {len(scripts)}")
            
            # Procurar por indicações de SPA ou JavaScript heavy
            if any('angular' in str(script).lower() or 'react' in str(script).lower() or 'vue' in str(script).lower() for script in scripts):
                print(f"   ⚠️ DETECTADO: Site usa framework JavaScript (Angular/React/Vue)")
                print(f"   💡 Isso pode impedir web scraping simples")
            
        else:
            print(f"❌ Site inacessível - Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao acessar site: {e}")
    
    print(f"\n" + "="*60)
    print("🔧 TESTANDO MÉTODO INTERNO DO SISTEMA")
    print("-" * 60)
    
    # Testar o método interno
    consultor = ConsultorRegistrosProfissionais()
    
    # Verificar se o cache está sendo usado exclusivamente
    print(f"\n💾 VERIFICANDO CACHE CONFEF:")
    if hasattr(consultor, 'cache_confef'):
        cache_entries = list(consultor.cache_confef.keys())
        print(f"   📊 Entradas no cache: {len(cache_entries)}")
        print(f"   📋 Nomes no cache: {cache_entries}")
        
        if len(cache_entries) <= 10:  # Se há poucos entries, provavelmente só cache manual
            print(f"   ⚠️ PROBLEMA DETECTADO: Cache muito pequeno!")
            print(f"   💡 Sistema pode estar dependendo só de cache manual")
            print(f"   🔧 Isso explicaria por que Ana Caroline não é encontrada")
    
    print(f"\n🎯 CONCLUSÃO:")
    print(f"   • Se o site do CONFEF requer JavaScript complexo")
    print(f"   • E o sistema só tem cache manual limitado")
    print(f"   • Então Ana Caroline não será encontrada automaticamente")
    print(f"   • Precisamos melhorar a capacidade de busca real")

def verificar_capacidade_web_scraping():
    """Verificar se o web scraping realmente funciona"""
    
    print(f"\n" + "="*60)
    print("🧪 TESTE DE WEB SCRAPING REAL")
    print("-" * 60)
    
    consultor = ConsultorRegistrosProfissionais()
    
    # Tentar buscar um nome que sabemos que NÃO está no cache
    nome_teste = "TESTE INEXISTENTE 123"
    
    print(f"\n🔍 Testando busca web para: {nome_teste}")
    print(f"   (Este nome NÃO deve estar no cache)")
    
    try:
        resultado = consultor._consultar_confef_por_nome(nome_teste)
        
        print(f"\n📊 RESULTADO:")
        print(f"   Encontrado: {resultado.get('encontrado', False)}")
        print(f"   Dados: {resultado.get('dados', {})}")
        
        if 'cache' in str(resultado).lower():
            print(f"   ⚠️ Resultado veio do cache (esperado: busca web)")
        elif 'web' in str(resultado).lower() or 'scraping' in str(resultado).lower():
            print(f"   ✅ Sistema fez tentativa de web scraping")
        else:
            print(f"   ❓ Origem do resultado unclear")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

if __name__ == "__main__":
    print("🎯 INVESTIGAÇÃO: Por que Ana Caroline Martins não é encontrada?")
    print("O sistema DEVERIA encontrar registros reais automaticamente!")
    
    testar_confef_real()
    verificar_capacidade_web_scraping()
    
    print(f"\n" + "="*80)
    print("🎯 HIPÓTESES PARA INVESTIGAR:")
    print("1. Site do CONFEF mudou e quebrou o web scraping")
    print("2. Site requer JavaScript que nosso scraping não suporta") 
    print("3. Sistema só funciona com cache manual (limitação)")
    print("4. URL ou método de busca do CONFEF mudou")
    print("5. Sistema simula busca mas não faz busca real")
    print("="*80)
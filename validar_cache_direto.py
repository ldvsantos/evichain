#!/usr/bin/env python3
"""
Teste Direto: Validação da Correção do Cache CONFEF
Verificar se o cache está funcionando corretamente para Luiz Oliveira dos Santos
"""

from consultor_registros import ConsultorRegistrosProfissionais

def validar_cache_confef():
    """Validar se o cache CONFEF está funcionando"""
    
    print("\n" + "="*80)
    print("🎯 VALIDAÇÃO DIRETA DO CACHE CONFEF")
    print("Teste: Luiz Oliveira dos Santos")
    print("="*80)
    
    consultor = ConsultorRegistrosProfissionais()
    
    # Testar diferentes variações do nome
    nomes_teste = [
        "LUIZ OLIVEIRA DOS SANTOS",
        "Luiz Oliveira dos Santos", 
        "LUIZ OLIVEIRA",
        "Luiz Oliveira",
        "OLIVEIRA DOS SANTOS",
        "Oliveira dos Santos"
    ]
    
    print("\n🔍 TESTANDO VARIAÇÕES DO NOME:")
    print("-" * 60)
    
    encontrou_algum = False
    
    for nome in nomes_teste:
        print(f"\n📋 Testando: '{nome}'")
        resultado = consultor.consultar_confef(nome)
        
        if resultado['encontrado']:
            encontrou_algum = True
            print(f"   ✅ ENCONTRADO!")
            print(f"   📄 Nome: {resultado['dados']['nome']}")
            print(f"   📄 Registro: {resultado['dados']['numero']}")
            print(f"   📄 UF: {resultado['dados']['uf']}")
            print(f"   📄 Categoria: {resultado['dados']['categoria']}")
            print(f"   📄 Situação: {resultado['dados']['situacao']}")
        else:
            print(f"   ❌ NÃO ENCONTRADO")
            if 'erro' in resultado:
                print(f"   💬 Erro: {resultado['erro']}")
    
    print("\n" + "="*80)
    if encontrou_algum:
        print("🎉 CACHE FUNCIONANDO: Luiz Oliveira dos Santos encontrado!")
        print("✅ Correção validada com sucesso!")
    else:
        print("❌ PROBLEMA: Cache não está funcionando!")
        print("⚠️ Correção precisa ser verificada!")
    print("="*80)

if __name__ == "__main__":
    validar_cache_confef()
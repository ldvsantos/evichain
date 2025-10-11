#!/usr/bin/env python3
"""
TESTE: Sistema Corrigido - Ana Caroline Martins
Verificar se a correção da busca web funciona
"""

from consultor_registros import ConsultorRegistrosProfissionais

def testar_sistema_corrigido():
    """Testar sistema com busca web corrigida"""
    
    print("\n" + "="*80)
    print("🚀 TESTE: SISTEMA CORRIGIDO - ANA CAROLINE MARTINS")
    print("Verificando se busca web real funciona agora")
    print("="*80)
    
    consultor = ConsultorRegistrosProfissionais()
    
    nomes_teste = [
        "Ana Caroline Martins",
        "ANA CAROLINE MARTINS",
        "Ana Caroline", 
        "Caroline Martins"
    ]
    
    resultados_encontrados = []
    
    for nome in nomes_teste:
        print(f"\n🔍 TESTANDO: {nome}")
        print("-" * 50)
        
        try:
            # Testar diretamente o método corrigido
            resultado = consultor._consultar_confef_por_nome(nome)
            
            if resultado.get('encontrado', False):
                print(f"✅ ENCONTRADO: {nome}")
                dados = resultado.get('dados', {})
                
                print(f"📄 DADOS ENCONTRADOS:")
                for chave, valor in dados.items():
                    print(f"   • {chave}: {valor}")
                
                resultados_encontrados.append({
                    'nome': nome,
                    'dados': dados
                })
                
                # Se encontrou, não precisa testar outras variações
                break
                
            else:
                print(f"❌ NÃO ENCONTRADO: {nome}")
                
        except Exception as e:
            print(f"⚠️ ERRO: {e}")
    
    # Teste de controle com caso conhecido
    print(f"\n" + "="*60)
    print("🧪 TESTE DE CONTROLE: Luiz Diego Vidal")
    print("(Verificar se sistema ainda funciona para casos conhecidos)")
    print("-" * 60)
    
    try:
        resultado_controle = consultor.consultar_registro_completo("Luiz Diego Vidal", "", "CREF")
        
        if resultado_controle.get('registro_encontrado', False):
            print(f"✅ CONTROLE OK: Luiz Diego ainda é encontrado")
            print(f"📄 Fonte: {resultado_controle.get('dados_profissional', {}).get('fonte_consulta', 'N/A')}")
        else:
            print(f"❌ PROBLEMA: Luiz Diego não encontrado (regressão)")
            
    except Exception as e:
        print(f"⚠️ ERRO no controle: {e}")
    
    print(f"\n" + "="*80)
    print("📊 RESUMO DOS RESULTADOS:")
    print("-" * 60)
    
    if resultados_encontrados:
        print(f"🎉 ANA CAROLINE ENCONTRADA!")
        print(f"✅ Sistema de busca web real implementado com SUCESSO!")
        
        for resultado in resultados_encontrados:
            print(f"\n🎯 Resultado para: {resultado['nome']}")
            dados = resultado['dados']
            fonte = dados.get('fonte_consulta', 'N/A')
            
            if 'cache' in fonte.lower():
                print(f"   📦 Fonte: Cache (dados pré-carregados)")
            elif 'web' in fonte.lower():
                print(f"   🌐 Fonte: Busca web real - FUNCIONOU!")
            else:
                print(f"   📄 Fonte: {fonte}")
                
            cref = dados.get('registro_cref_completo', 'N/A')
            print(f"   📋 CREF: {cref}")
            
    else:
        print(f"❌ Ana Caroline não encontrada")
        print(f"💡 Possibilidades:")
        print(f"   1. Ela realmente não tem registro no CONFEF")
        print(f"   2. Nome está registrado de forma diferente")
        print(f"   3. Busca web ainda precisa de ajustes")
        print(f"   4. Site CONFEF requer método específico")
    
    print("="*80)
    
    return len(resultados_encontrados) > 0

if __name__ == "__main__":
    print("🎯 OBJETIVO: Testar se Ana Caroline é encontrada com sistema corrigido")
    print("Sistema DEVERIA encontrar ela automaticamente agora!")
    
    sucesso = testar_sistema_corrigido()
    
    if sucesso:
        print("\n🎉 MISSÃO CUMPRIDA!")
        print("✅ Ana Caroline Martins encontrada automaticamente")
        print("✅ Sistema de busca web real funcionando")
    else:
        print("\n🔄 INVESTIGAÇÃO CONTINUA...")
        print("❓ Ana Caroline pode não ter registro ou nome diferente")
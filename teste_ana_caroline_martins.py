#!/usr/bin/env python3
"""
Teste: Ana Caroline Martins
Verificar se o sistema consegue localizar este profissional
"""

from consultor_registros import ConsultorRegistrosProfissionais

def testar_ana_caroline_martins():
    """Teste para verificar se Ana Caroline Martins é encontrada"""
    
    print("\n" + "="*80)
    print("🔍 TESTE: ANA CAROLINE MARTINS")
    print("Verificando se o profissional é encontrado no sistema")
    print("="*80)
    
    consultor = ConsultorRegistrosProfissionais()
    
    # Variações do nome para testar
    nomes_teste = [
        "ANA CAROLINE MARTINS",
        "Ana Caroline Martins",
        "ANA CAROLINE",
        "Ana Caroline", 
        "CAROLINE MARTINS",
        "Caroline Martins",
        "ANA MARTINS",
        "Ana Martins"
    ]
    
    print("\n🔍 TESTANDO VARIAÇÕES DO NOME:")
    print("-" * 60)
    
    resultados_encontrados = []
    
    for nome in nomes_teste:
        print(f"\n📋 Testando: '{nome}'")
        
        # Testar em diferentes conselhos
        conselhos = ['CREF', 'CRM', 'CRP', 'CRO', 'CREA', 'OAB']
        
        encontrou_em_algum = False
        
        for conselho in conselhos:
            try:
                resultado = consultor.consultar_registro_completo(nome, '', conselho)
                
                if resultado.get('registro_encontrado', False):
                    encontrou_em_algum = True
                    print(f"   ✅ ENCONTRADO no {conselho}!")
                    print(f"   📄 Dados: {resultado.get('dados_profissional', {})}")
                    
                    resultados_encontrados.append({
                        'nome_pesquisado': nome,
                        'conselho': conselho,
                        'dados': resultado.get('dados_profissional', {})
                    })
                    break
                    
            except Exception as e:
                print(f"   ⚠️ Erro ao consultar {conselho}: {e}")
        
        if not encontrou_em_algum:
            print(f"   ❌ NÃO ENCONTRADO em nenhum conselho")
    
    print("\n" + "="*80)
    print("📊 RESUMO DOS RESULTADOS:")
    print("-" * 60)
    
    if resultados_encontrados:
        print(f"✅ PROFISSIONAL ENCONTRADO em {len(resultados_encontrados)} consulta(s)!")
        
        for i, resultado in enumerate(resultados_encontrados, 1):
            print(f"\n🎯 Resultado {i}:")
            print(f"   📝 Nome pesquisado: {resultado['nome_pesquisado']}")
            print(f"   🏛️ Conselho: {resultado['conselho']}")
            print(f"   📄 Dados completos:")
            for chave, valor in resultado['dados'].items():
                print(f"      • {chave}: {valor}")
                
    else:
        print("❌ PROFISSIONAL NÃO ENCONTRADO")
        print("   • Ana Caroline Martins não foi localizada no sistema")
        print("   • Pode ser necessário:")
        print("     - Verificar se o profissional possui registro ativo")
        print("     - Confirmar a grafia correta do nome")
        print("     - Adicionar ao cache se for um caso conhecido")
    
    print("\n" + "="*80)
    
    return resultados_encontrados

if __name__ == "__main__":
    resultados = testar_ana_caroline_martins()
    
    if resultados:
        print("🎉 TESTE CONCLUÍDO: Ana Caroline Martins ENCONTRADA!")
    else:
        print("⚠️ TESTE CONCLUÍDO: Ana Caroline Martins NÃO ENCONTRADA")
        print("💡 SUGESTÃO: Verificar se é necessário adicionar ao cache")
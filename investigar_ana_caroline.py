#!/usr/bin/env python3
"""
Investigação Específica: Ana Caroline Martins - CREF
Verificar se é outro caso de falso negativo no CONFEF
"""

from consultor_registros import ConsultorRegistrosProfissionais

def investigar_ana_caroline_cref():
    """Investigação específica para Ana Caroline Martins no CREF"""
    
    print("\n" + "="*80)
    print("🔍 INVESTIGAÇÃO: ANA CAROLINE MARTINS - CREF")
    print("Verificando possível falso negativo no CONFEF")
    print("="*80)
    
    consultor = ConsultorRegistrosProfissionais()
    
    # Variações específicas do nome para CREF
    nomes_teste = [
        "ANA CAROLINE MARTINS",
        "Ana Caroline Martins",
        "ANA CAROLINE",
        "Ana Caroline", 
        "CAROLINE MARTINS",
        "Caroline Martins",
        "ANA MARTINS",
        "Ana Martins",
        "A CAROLINE MARTINS",
        "CAROLINE",
        "ANA C MARTINS",
        "A C MARTINS"
    ]
    
    print("\n🔍 TESTANDO ESPECIFICAMENTE NO CREF/CONFEF:")
    print("-" * 60)
    
    encontrou_cache = False
    encontrou_web = False
    
    for nome in nomes_teste:
        print(f"\n📋 Testando: '{nome}'")
        
        try:
            # Testar especificamente no CREF
            resultado = consultor.consultar_registro_completo(nome, '', 'CREF')
            
            if resultado.get('registro_encontrado', False):
                encontrou_cache = True
                print(f"   ✅ ENCONTRADO no CREF!")
                print(f"   📄 Dados: {resultado.get('dados_profissional', {})}")
                break
            else:
                print(f"   ❌ NÃO encontrado no cache")
                
                # Verificar se houve tentativa de web scraping
                dados = resultado.get('dados_profissional', {})
                if dados.get('fonte_consulta') and 'web' in str(dados.get('fonte_consulta')).lower():
                    encontrou_web = True
                    print(f"   🌐 Tentativa de web scraping realizada")
                
        except Exception as e:
            print(f"   ⚠️ Erro na consulta: {e}")
    
    print("\n" + "="*80)
    print("📊 ANÁLISE DOS RESULTADOS:")
    print("-" * 60)
    
    if encontrou_cache:
        print("✅ PROFISSIONAL ENCONTRADO NO CACHE")
        print("   • Ana Caroline Martins está no sistema")
        print("   • Registro CREF localizado com sucesso")
        
    elif encontrou_web:
        print("🌐 TENTATIVA DE WEB SCRAPING REALIZADA")
        print("   • Sistema tentou buscar no site do CONFEF")
        print("   • Não encontrado via web scraping")
        print("   • Pode ser necessário adicionar ao cache")
        
    else:
        print("❌ POSSÍVEL FALSO NEGATIVO DETECTADO")
        print("   • Ana Caroline Martins não encontrada")
        print("   • Similar aos casos anteriores:")
        print("     - Luiz Diego Vidal Santos (corrigido)")
        print("     - Luiz Oliveira dos Santos (corrigido)")
        print("   • RECOMENDAÇÃO: Verificar registro real no CONFEF")
        
    print("\n💡 PRÓXIMOS PASSOS:")
    print("   1. Confirmar se Ana Caroline tem registro ativo no CONFEF")
    print("   2. Obter número CREF completo (ex: CREF 123456-G/SP)")
    print("   3. Verificar UF e categoria do registro")
    print("   4. Se confirmado, adicionar ao cache como correção")
    
    print("\n🔍 INFORMAÇÕES NECESSÁRIAS:")
    print("   • Número CREF completo")
    print("   • Estado (UF) do registro")
    print("   • Categoria (Graduado/Provisionado)")
    print("   • Situação (Ativo/Inativo)")
    
    print("\n" + "="*80)
    
    return not encontrou_cache

if __name__ == "__main__":
    possivel_falso_negativo = investigar_ana_caroline_cref()
    
    if possivel_falso_negativo:
        print("⚠️ POSSÍVEL FALSO NEGATIVO DETECTADO!")
        print("🔧 Aguardando informações do registro para correção")
    else:
        print("✅ Profissional encontrado no sistema")
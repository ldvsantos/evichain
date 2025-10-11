#!/usr/bin/env python3
"""
Teste Final Web: Luiz Oliveira dos Santos
Validação da correção implementada via API web
"""

import requests
import json
import time

def testar_web_luiz_oliveira():
    """Teste final da correção via API web"""
    
    print("\n" + "="*80)
    print("🎯 TESTE FINAL WEB: LUIZ OLIVEIRA DOS SANTOS")
    print("Validação da correção implementada")
    print("="*80)
    
    base_url = "http://localhost:5000"
    
    # Verificar se servidor está rodando
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ Servidor respondendo: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar no servidor: {e}")
        return
    
    print("\n📝 TESTANDO DENÚNCIA COM LUIZ OLIVEIRA DOS SANTOS...")
    
    # Dados da investigação de teste
    investigacao_data = {
        "nome": "Luiz Oliveira dos Santos",
        "registro": "",
        "conselho": "CONFEF",
        "informacoes_adicionais": {
            "contexto": "Denúncia sobre serviços de personal trainer",
            "motivo": "Verificação de registro profissional"
        }
    }
    
    try:
        print("🔍 Enviando denúncia para investigação...")
        response = requests.post(
            f"{base_url}/api/investigacao/iniciar",
            json=investigacao_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📊 Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            resultado = response.json()
            
            print("\n📋 RESULTADO DA INVESTIGAÇÃO:")
            print("-" * 60)
            
            # Analisar nomes detectados
            if 'nomes_detectados' in resultado:
                nomes = resultado['nomes_detectados']
                print(f"👤 Nomes detectados: {len(nomes)}")
                for nome in nomes:
                    print(f"   • {nome}")
                    
                # Verificar se Luiz Oliveira foi detectado corretamente
                nomes_str = ' '.join(nomes).lower()
                if 'luiz oliveira' in nomes_str or 'luiz oliveira dos santos' in nomes_str:
                    print("✅ Nome 'Luiz Oliveira dos Santos' detectado corretamente!")
                else:
                    print("❌ Nome 'Luiz Oliveira dos Santos' NÃO detectado!")
                    print(f"   Detectados: {nomes}")
            
            # Analisar registros profissionais
            if 'registros_profissionais' in resultado:
                registros = resultado['registros_profissionais']
                print(f"\n📋 Registros encontrados: {len(registros)}")
                
                encontrou_luiz = False
                for registro in registros:
                    print(f"\n   📄 Registro encontrado:")
                    print(f"      Nome: {registro.get('nome', 'N/A')}")
                    print(f"      Conselho: {registro.get('conselho', 'N/A')}")
                    print(f"      Número: {registro.get('numero', 'N/A')}")
                    print(f"      UF: {registro.get('uf', 'N/A')}")
                    print(f"      Situação: {registro.get('situacao', 'N/A')}")
                    
                    # Verificar se é o Luiz Oliveira
                    nome_registro = str(registro.get('nome', '')).lower()
                    numero_registro = str(registro.get('numero', ''))
                    
                    if 'luiz oliveira' in nome_registro and '008072' in numero_registro:
                        encontrou_luiz = True
                        print("      ✅ ESTE É O LUIZ OLIVEIRA DOS SANTOS!")
                        
                        # Verificar dados específicos
                        if 'CREF 008072-P/BA' in numero_registro or '008072-P/BA' in numero_registro:
                            print("      ✅ Registro CREF correto: 008072-P/BA")
                        else:
                            print(f"      ⚠️ Registro diferente do esperado: {numero_registro}")
                            
                        if registro.get('uf') == 'BA':
                            print("      ✅ UF correta: BA")
                        else:
                            print(f"      ⚠️ UF diferente: {registro.get('uf')}")
                
                if encontrou_luiz:
                    print("\n🎉 CORREÇÃO VALIDADA: Luiz Oliveira dos Santos encontrado!")
                else:
                    print("\n❌ PROBLEMA: Luiz Oliveira dos Santos NÃO encontrado nos registros!")
            
            # Mostrar resumo da investigação
            if 'resumo_investigacao' in resultado:
                resumo = resultado['resumo_investigacao']
                print(f"\n📊 RESUMO DA INVESTIGAÇÃO:")
                print(f"   {resumo}")
            
            # Salvar resultado completo
            with open('resultado_teste_web_luiz_oliveira.json', 'w', encoding='utf-8') as f:
                json.dump(resultado, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Resultado completo salvo em 'resultado_teste_web_luiz_oliveira.json'")
            
        else:
            print(f"❌ Erro na investigação: {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    testar_web_luiz_oliveira()
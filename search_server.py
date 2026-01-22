#!/usr/bin/env python3
"""
Servidor Flask simples apenas para testar busca
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from pathlib import Path

from blockchain_simulator import EviChainBlockchain
from evichain import load_settings

app = Flask(__name__)
CORS(app)

# Inicializar blockchain
print("🔗 Inicializando blockchain...")
evichain = EviChainBlockchain(data_file="blockchain_data.json")
print(f"✅ Blockchain carregada com {len(evichain.chain)} blocos")

@app.route('/')
def home():
    return jsonify({
        "message": "EviChain Search API",
        "status": "running",
        "total_blocks": len(evichain.chain)
    })

@app.route('/api/search', methods=['GET'])
def search_complaints():
    """Busca denúncias na blockchain por termo de pesquisa"""
    try:
        query = request.args.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Parâmetro query é obrigatório'
            }), 400
        
        print(f"[INFO] Buscando denúncias por: '{query}'")
        
        # Obter todas as denúncias da blockchain
        complaints = evichain.get_all_complaints()
        results = []
        
        # Buscar nos campos de texto das denúncias
        search_fields = ['titulo', 'nomeDenunciado', 'descricao', 'conselho', 'categoria', 'assunto']
        
        for complaint in complaints:
            match_found = False
            match_details = []
            
            # Buscar em cada campo
            for field in search_fields:
                field_value = str(complaint.get(field, '')).lower()
                if query.lower() in field_value:
                    match_found = True
                    match_details.append(f"{field}: {query}")
            
            # Buscar também na análise da IA se disponível
            ia_analysis = complaint.get('ia_analysis', {})
            if ia_analysis:
                # Buscar no resumo
                resumo = str(ia_analysis.get('analise_basica', {}).get('resumo', '')).lower()
                if query.lower() in resumo:
                    match_found = True
                    match_details.append("análise_ia: resumo")
                
                # Buscar nas palavras-chave
                palavras_chave = ia_analysis.get('analise_basica', {}).get('palavras_chave', [])
                for palavra in palavras_chave:
                    if query.lower() in str(palavra).lower():
                        match_found = True
                        match_details.append("análise_ia: palavra_chave")
                        break
            
            if match_found:
                # Adicionar informações do resultado
                result = {
                    'complaint_id': complaint.get('complaint_id', 'N/A'),
                    'titulo': complaint.get('titulo', 'N/A'),
                    'nomeDenunciado': complaint.get('nomeDenunciado', 'N/A'),
                    'conselho': complaint.get('conselho', 'N/A'),
                    'categoria': complaint.get('categoria', 'N/A'),
                    'timestamp': complaint.get('timestamp', 'N/A'),
                    'match_details': match_details,
                    'risk_level': ia_analysis.get('classificacao_risco', {}).get('nivel', 'N/A'),
                    'risk_score': ia_analysis.get('classificacao_risco', {}).get('pontuacao', 0)
                }
                results.append(result)
        
        # Ordenar por pontuação de risco (maior primeiro) e depois por timestamp
        results.sort(key=lambda x: (x.get('risk_score', 0), x.get('timestamp', '')), reverse=True)
        
        print(f"[INFO] Encontrados {len(results)} resultados para '{query}'")
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results),
            'query': query
        })
        
    except Exception as e:
        print(f"[ERROR] Erro na busca de denúncias: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Retorna estatísticas básicas do sistema"""
    try:
        complaints = evichain.get_all_complaints()
        
        total_complaints = len(complaints)
        total_blocks = len(evichain.chain)
        
        # Contar por conselho
        councils = {}
        categories = {}
        
        for complaint in complaints:
            conselho = complaint.get('conselho', 'N/A')
            categoria = complaint.get('categoria', 'N/A')
            
            councils[conselho] = councils.get(conselho, 0) + 1
            categories[categoria] = categories.get(categoria, 0) + 1
        
        return jsonify({
            'success': True,
            'total_complaints': total_complaints,
            'total_blocks': total_blocks,
            'councils': councils,
            'categories': categories
        })
        
    except Exception as e:
        print(f"[ERROR] Erro nas estatísticas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    settings = load_settings(project_root=Path(__file__).resolve().parent)
    port = int(os.getenv('FLASK_SEARCH_PORT', '5001'))

    print("\n🔍 EviChain Search Server")
    print(f"🔗 http://localhost:{port}")
    print("📊 Endpoints disponíveis:")
    print("   GET /api/search?query=termo")
    print("   GET /api/stats")
    print()

    app.run(host=settings.host, port=port, debug=settings.debug)
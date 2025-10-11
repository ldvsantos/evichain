#!/usr/bin/env python3
"""
EviChain API Server (Versão Final Definitiva)
"""
from flask import Flask, request, jsonify, send_from_directory
import os
import json
import re
import time
import uuid
from datetime import datetime
from collections import deque
import traceback
from blockchain_simulator import EviChainBlockchain, generate_complaint_id
from ia_engine_openai_padrao import IAEngineOpenAIPadrao
from assistente_denuncia import AssistenteDenuncia

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"').strip("'")
        print("✅ Arquivo .env carregado com sucesso")
    else:
        print("⚠️ Arquivo .env não encontrado.")

load_env()

app = Flask(__name__)
TRACE_BUFFER = deque(maxlen=120)

# Inicializar componentes
assistente = AssistenteDenuncia()

def log_trace(trace_id, stage, detail=""):
    timestamp = datetime.now().isoformat()
    print(f"[TRACE][{timestamp}][{trace_id}] {stage} - {detail}", flush=True)

# (O resto das funções de parse de JSON permanece o mesmo, sem necessidade de alteração)
def _split_loose_items(body: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    depth = 0
    in_quotes = False
    quote_char = ''
    for char in body:
        if in_quotes:
            current.append(char)
            if char == quote_char:
                in_quotes = False
            continue
        if char in ('"', "'"):
            in_quotes = True
            quote_char = char
            current.append(char)
            continue
        if char in '{[':
            depth += 1
        elif char in '}]':
            depth = max(depth - 1, 0)
        if char == ',' and depth == 0:
            segment = ''.join(current).strip()
            if segment:
                items.append(segment)
            current = []
            continue
        current.append(char)
    tail = ''.join(current).strip()
    if tail:
        items.append(tail)
    return items

def _parse_loose_value(value: str):
    value = value.strip()
    if not value: return ''
    if value[0] in ('"', "'"): return value.strip('"' + "'")
    if value.startswith('[') and value.endswith(']'):
        inner = value[1:-1].strip()
        if not inner: return []
        return [_parse_loose_value(part) for part in _split_loose_items(inner)]
    if value.startswith('{') and value.endswith('}'):
        parsed = _parse_loose_object(value)
        if parsed is None: raise ValueError('Invalid nested object')
        return parsed
    lowered = value.lower()
    if lowered in {'true', 'false'}: return lowered == 'true'
    if lowered == 'null': return None
    if re.fullmatch(r'-?\d+(?:\.\d+)?', value):
        return float(value) if '.' in value else int(value)
    return value

def _parse_loose_object(raw: str):
    if not raw: return None
    stripped = raw.strip()
    if stripped.startswith('{') and stripped.endswith('}'):
        stripped = stripped[1:-1]
    else:
        return None
    result = {}
    for item in _split_loose_items(stripped):
        if ':' not in item: return None
        key_part, value_part = item.split(':', 1)
        key = key_part.strip().strip('"' + "'")
        if not key: return None
        try:
            result[key] = _parse_loose_value(value_part)
        except ValueError:
            return None
    return result
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

evichain = EviChainBlockchain(data_file="blockchain_data.json")
ia_engine = IAEngineOpenAIPadrao()

@app.route("/")
def serve_index(): return send_from_directory(".", "index.html")

@app.route("/dashboard.html")
def serve_dashboard(): return send_from_directory(".", "dashboard.html")

@app.route("/<path:path>")
def serve_static_files(path): return send_from_directory(".", path)

@app.route('/api/submit-complaint', methods=['POST'])
def submit_complaint():
    trace_id = f"REQ-{uuid.uuid4().hex[:6]}"
    log_trace(trace_id, 'request_start')
    
    try:
        data = request.get_json(silent=True)
        if data is None:
            raw_body = request.get_data(as_text=True) or ''
            data = _parse_loose_object(raw_body)
            if data is None: return jsonify({"success": False, "error": "Formato JSON inválido."}), 400

        # ===== CORREÇÃO FINAL =====
        title = data.get('titulo', 'Denúncia sem Título')
        description = data.get('descricao', '')
        # ==========================
        
        if not description:
            return jsonify({"success": False, "error": "O campo 'descricao' é obrigatório."}), 400
        
        # Validação dos novos campos obrigatórios
        assunto = data.get('assunto', '').strip()
        finalidade = data.get('finalidade', '').strip()
        
        if not assunto:
            return jsonify({"success": False, "error": "O campo 'assunto' é obrigatório."}), 400
            
        if not finalidade:
            return jsonify({"success": False, "error": "O campo 'finalidade' é obrigatório."}), 400

        transaction_data = {
            'titulo': title,
            'descricao': description,
            'conselho': data.get('conselho', 'N/A'),
            'categoria': data.get('categoria', 'N/A'),
            'anonymous': data.get('anonymous', True),
            'ouvidoriaAnonima': data.get('ouvidoriaAnonima', False),
            'assunto': data.get('assunto', ''),
            'prioridade': data.get('prioridade', ''),
            'finalidade': data.get('finalidade', ''),
            'codigosAnteriores': data.get('codigosAnteriores', ''),
            'file_hashes': []
        }

        log_trace(trace_id, 'ia_analysis_start')
        ia_analysis_result = ia_engine.analisar_denuncia_completa(transaction_data, trace_id=trace_id)
        transaction_data["ia_analysis"] = ia_analysis_result or {}

        log_trace(trace_id, 'blockchain_add_start')
        complaint_id = evichain.add_evidence_transaction(transaction_data)
        
        log_trace(trace_id, 'mining_start')
        new_block = evichain.mine_pending_transactions()

        response = {
            'success': True,
            'complaint_id': complaint_id,
            'block_index': new_block.index if new_block else None,
        }
        return jsonify(response), 200

    except Exception as e:
        log_trace(trace_id, 'uncaught_exception', str(e))
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Erro interno no servidor: {e}"}), 500

@app.route('/api/complaints', methods=['GET'])
def get_complaints():
    try:
        return jsonify({"success": True, "complaints": evichain.get_all_complaints()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/blockchain-info', methods=['GET'])
def get_blockchain_info():
    try:
        info = evichain.get_chain_info()
        return jsonify({"success": True, "blockchain": info})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/assistente/analisar', methods=['POST'])
def analisar_com_assistente():
    """Endpoint para análise de texto com assistente de IA"""
    try:
        data = request.json
        texto = data.get('texto', '').strip()
        conselho = data.get('conselho')
        categoria = data.get('categoria')
        
        if not texto:
            return jsonify({
                'success': False,
                'error': 'Texto da denúncia é obrigatório'
            }), 400
        
        print(f"[INFO] Analisando texto com assistente: {len(texto)} caracteres")
        
        # Analisar com assistente (usa OpenAI se disponível, senão local)
        analise = assistente.analisar_denuncia(texto, conselho, categoria)
        
        # Gerar relatório HTML
        relatorio_html = assistente.gerar_relatorio_html(analise)
        
        print(f"[INFO] Análise concluída - Fonte: {analise.get('fonte')}, Pontuação: {analise['pontuacao_qualidade']}/100")
        
        return jsonify({
            'success': True,
            'analise': analise,
            'relatorio_html': relatorio_html
        })
    
    except Exception as e:
        print(f"[ERROR] Erro ao analisar com assistente: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("\n================ EviChain API Server ==================")
    print(f"🔗 Acesso principal: http://localhost:5000")
    print(f"📊 Dashboard: http://localhost:5000/dashboard.html")
    print("=======================================================")
    
    try:
        from waitress import serve
        serve(app, host='0.0.0.0', port=5000)
    except ImportError:
        app.run(host='0.0.0.0', port=5000, debug=True)
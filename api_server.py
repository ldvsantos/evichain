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
from investigador_digital import InvestigadorDigital
from consultor_registros import ConsultorRegistrosProfissionais

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
investigador = InvestigadorDigital()
consultor_registros = ConsultorRegistrosProfissionais()

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
        complaints = evichain.get_all_complaints()
        return jsonify({"success": True, "complaints": complaints})
    except Exception as e:
        print(f"[ERROR] Erro ao obter denúncias: {e}")
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

@app.route('/api/registros/consultar', methods=['POST'])
def consultar_registro_profissional():
    """Endpoint específico para consulta detalhada de registros profissionais"""
    try:
        data = request.json
        nome = data.get('nome', '').strip()
        registro = data.get('registro', '').strip()
        conselho = data.get('conselho', '').strip()
        
        if not nome:
            return jsonify({
                'success': False,
                'error': 'Nome do profissional é obrigatório'
            }), 400
        
        print(f"[INFO] Consultando registro profissional: {nome} - {conselho} - {registro}")
        
        # Realizar consulta detalhada
        resultado_consulta = consultor_registros.consultar_registro_completo(
            nome=nome,
            registro=registro,
            conselho=conselho
        )
        
        # Se encontrou registro, extrair formação
        if resultado_consulta.get("registro_encontrado") and resultado_consulta.get("dados_profissional"):
            formacao_info = consultor_registros.extrair_formacao_e_especialidades(
                resultado_consulta["dados_profissional"],
                conselho or "GENERICO"
            )
            resultado_consulta["formacao_detalhada"] = formacao_info
        
        # Gerar relatório
        relatorio = consultor_registros.gerar_relatorio_registro(resultado_consulta)
        
        print(f"[SUCCESS] Consulta concluída - Registro encontrado: {resultado_consulta.get('registro_encontrado', False)}")
        
        return jsonify({
            'success': True,
            'consulta': resultado_consulta,
            'relatorio': relatorio,
            'encontrado': resultado_consulta.get('registro_encontrado', False)
        })
    
    except Exception as e:
        print(f"[ERROR] Erro na consulta de registro: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/investigacao/iniciar', methods=['POST'])
def iniciar_investigacao():
    """Endpoint para iniciar investigação digital de um profissional"""
    try:
        data = request.json
        nome = data.get('nome', '').strip()
        registro = data.get('registro', '').strip()
        conselho = data.get('conselho', '').strip()
        informacoes_adicionais = data.get('informacoes_adicionais', {})
        
        if not nome:
            return jsonify({
                'success': False,
                'error': 'Nome do profissional é obrigatório'
            }), 400
        
        print(f"[INFO] Iniciando investigação digital para: {nome}")
        
        # Realizar investigação completa
        resultado_investigacao = investigador.investigar_completo(
            nome=nome,
            registro_profissional=registro,
            conselho=conselho,
            informacoes_adicionais=informacoes_adicionais
        )
        
        print(f"[SUCCESS] Investigação concluída para {nome}")
        
        return jsonify({
            'success': True,
            'investigacao': resultado_investigacao
        })
    
    except Exception as e:
        print(f"[ERROR] Erro durante investigação: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/investigacao/relatorio/<formato>', methods=['POST'])
def gerar_relatorio_investigacao(formato):
    """Endpoint para gerar relatório de investigação em diferentes formatos"""
    try:
        data = request.json
        dados_investigacao = data.get('dados_investigacao')
        
        if not dados_investigacao:
            return jsonify({
                'success': False,
                'error': 'Dados de investigação são obrigatórios'
            }), 400
        
        if formato not in ['json', 'html', 'txt']:
            return jsonify({
                'success': False,
                'error': 'Formato deve ser: json, html ou txt'
            }), 400
        
        relatorio = investigador.gerar_relatorio_investigacao(dados_investigacao, formato)
        
        if formato == 'json':
            return jsonify({
                'success': True,
                'relatorio': json.loads(relatorio),
                'formato': 'json'
            })
        else:
            return jsonify({
                'success': True,
                'relatorio': relatorio,
                'formato': formato
            })
    
    except Exception as e:
        print(f"[ERROR] Erro ao gerar relatório: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/investigacao/buscar-redes-sociais', methods=['POST'])
def buscar_redes_sociais():
    """Endpoint específico para busca em redes sociais"""
    try:
        data = request.json
        nome = data.get('nome', '').strip()
        
        if not nome:
            return jsonify({
                'success': False,
                'error': 'Nome é obrigatório'
            }), 400
        
        print(f"[INFO] Buscando redes sociais para: {nome}")
        
        # Buscar apenas redes sociais
        redes_sociais = investigador._investigar_redes_sociais(nome)
        
        return jsonify({
            'success': True,
            'redes_sociais': redes_sociais
        })
    
    except Exception as e:
        print(f"[ERROR] Erro na busca de redes sociais: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Retorna estatísticas analíticas das denúncias"""
    try:
        complaints = evichain.get_all_complaints()
        
        total_complaints = len(complaints)
        pending_complaints = len([c for c in complaints if c.get('status', 'pending') == 'pending'])
        resolved_complaints = total_complaints - pending_complaints
        
        # Cálculo simples do tempo médio de resolução (em horas)
        average_resolution_time = 24  # Valor padrão para demonstração
        
        return jsonify({
            'totalComplaints': total_complaints,
            'pendingComplaints': pending_complaints,
            'resolvedComplaints': resolved_complaints,
            'averageResolutionTime': f'{average_resolution_time}h'
        })
    
    except Exception as e:
        print(f"[ERROR] Erro ao obter analytics: {e}")
        return jsonify({
            'totalComplaints': 0,
            'pendingComplaints': 0,
            'resolvedComplaints': 0,
            'averageResolutionTime': '0h'
        }), 500

@app.route('/api/latest-analysis', methods=['GET'])
def get_latest_analysis():
    """Retorna a análise mais recente de denúncia"""
    try:
        complaints = evichain.get_all_complaints()
        
        if not complaints:
            return jsonify({
                'success': False,
                'error': 'Nenhuma denúncia encontrada'
            }), 404
        
        # Pega a denúncia mais recente com análise de IA
        latest_complaint = None
        for complaint in reversed(complaints):
            if complaint.get('ia_analysis'):
                latest_complaint = complaint
                break
        
        if not latest_complaint:
            return jsonify({
                'success': False,
                'error': 'Nenhuma análise de IA encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'complaint_id': latest_complaint.get('id', 'N/A'),
            'full_analysis': latest_complaint.get('ia_analysis', {})
        })
    
    except Exception as e:
        print(f"[ERROR] Erro ao obter última análise: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate_pdf', methods=['POST'])
def generate_pdf():
    """Gera PDF com dados da denúncia"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
        
        # Extrair todos os dados da denúncia
        complaint_id = data.get('complaint_id', 'N/A')
        titulo = data.get('titulo', 'N/A')
        assunto = data.get('assunto', 'N/A')
        prioridade = data.get('prioridade', 'N/A')
        finalidade = data.get('finalidade', 'N/A')
        conselho = data.get('conselho', 'N/A')
        categoria = data.get('categoria', 'N/A')
        timestamp = data.get('timestamp', datetime.datetime.now().isoformat())
        codigosAnteriores = data.get('codigosAnteriores')
        ouvidoriaAnonima = data.get('ouvidoriaAnonima', False)
        anonymous = data.get('anonymous', False)
        descricao = data.get('descricao', 'Não disponível')
        ia_analysis = data.get('ia_analysis', {})
        metadata = data.get('metadata', {})
        
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from io import BytesIO
        import datetime
        
        # Criar documento PDF em memória
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centralizado
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor='#2c3e50'
        )
        
        # Conteúdo do PDF
        story = []
        
        # Título
        story.append(Paragraph("RELATÓRIO DE DENÚNCIA - EVICHAIN", title_style))
        story.append(Spacer(1, 20))
        
        # Informações básicas completas
        story.append(Paragraph("INFORMAÇÕES BÁSICAS DA DENÚNCIA", heading_style))
        story.append(Paragraph(f"<b>ID da Denúncia:</b> {complaint_id}", styles['Normal']))
        story.append(Paragraph(f"<b>Título:</b> {titulo}", styles['Normal']))
        story.append(Paragraph(f"<b>Assunto:</b> {assunto}", styles['Normal']))
        story.append(Paragraph(f"<b>Prioridade:</b> {prioridade}", styles['Normal']))
        story.append(Paragraph(f"<b>Finalidade:</b> {finalidade}", styles['Normal']))
        story.append(Paragraph(f"<b>Conselho:</b> {conselho}", styles['Normal']))
        story.append(Paragraph(f"<b>Categoria:</b> {categoria}", styles['Normal']))
        
        # Formatar data
        try:
            from datetime import datetime as dt
            if timestamp:
                data_formatada = dt.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
            else:
                data_formatada = 'N/A'
        except:
            data_formatada = timestamp or 'N/A'
            
        story.append(Paragraph(f"<b>Data de Registro:</b> {data_formatada}", styles['Normal']))
        story.append(Paragraph(f"<b>Status:</b> Registrada", styles['Normal']))
        
        if codigosAnteriores:
            story.append(Paragraph(f"<b>Códigos Anteriores:</b> {codigosAnteriores}", styles['Normal']))
        
        story.append(Spacer(1, 15))
        
        # Configurações de privacidade
        story.append(Paragraph("CONFIGURAÇÕES DE PRIVACIDADE", heading_style))
        story.append(Paragraph(f"<b>Ouvidoria Anônima:</b> {'Sim' if ouvidoriaAnonima else 'Não'}", styles['Normal']))
        story.append(Paragraph(f"<b>Manter Anonimato:</b> {'Sim' if anonymous else 'Não'}", styles['Normal']))
        story.append(Spacer(1, 15))
        
        # Descrição da denúncia
        story.append(Paragraph("DESCRIÇÃO DA DENÚNCIA", heading_style))
        story.append(Paragraph(descricao, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Análise da IA
        if ia_analysis:
            story.append(Paragraph("ANÁLISE DA INTELIGÊNCIA ARTIFICIAL", heading_style))
            
            if 'classificacao' in ia_analysis:
                story.append(Paragraph(f"<b>Classificação:</b> {ia_analysis['classificacao']}", styles['Normal']))
            
            if 'gravidade' in ia_analysis:
                story.append(Paragraph(f"<b>Gravidade:</b> {ia_analysis['gravidade']}", styles['Normal']))
            
            if 'analise_detalhada' in ia_analysis:
                story.append(Paragraph("<b>Análise Detalhada:</b>", styles['Normal']))
                story.append(Paragraph(ia_analysis['analise_detalhada'], styles['Normal']))
            
            if 'recomendacoes' in ia_analysis:
                story.append(Paragraph("<b>Recomendações:</b>", styles['Normal']))
                for rec in ia_analysis['recomendacoes']:
                    story.append(Paragraph(f"• {rec}", styles['Normal']))
            
            story.append(Spacer(1, 20))
        
        # Investigação automática
        investigacao = ia_analysis.get('investigacao_automatica', {}) if ia_analysis else {}
        if investigacao:
            story.append(Paragraph("INVESTIGAÇÃO AUTOMÁTICA REALIZADA", heading_style))
            
            # Relatório de detecção
            if 'relatorio_deteccao' in investigacao:
                story.append(Paragraph("<b>Relatório de Detecção:</b>", styles['Normal']))
                story.append(Paragraph(investigacao['relatorio_deteccao'], styles['Normal']))
                story.append(Spacer(1, 10))
            
            # Profissionais identificados
            deteccao = investigacao.get('deteccao_nomes', {})
            if deteccao.get('nomes_detectados'):
                story.append(Paragraph("<b>Profissionais Identificados:</b>", styles['Normal']))
                for nome in deteccao['nomes_detectados']:
                    story.append(Paragraph(f"• <b>{nome.get('nome_detectado', 'N/A')}</b> (Confiabilidade: {nome.get('confiabilidade', 0)}%)", styles['Normal']))
                    story.append(Paragraph(f"  Contexto: {nome.get('contexto_encontrado', 'N/A')}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            # Resultados das investigações
            investigacoes = investigacao.get('investigacoes_realizadas', [])
            if investigacoes:
                story.append(Paragraph("<b>Resultados das Investigações:</b>", styles['Normal']))
                for inv in investigacoes:
                    story.append(Paragraph(f"<b>Investigado:</b> {inv.get('nome_investigado', 'N/A')}", styles['Normal']))
                    
                    resultado = inv.get('resultado_investigacao', {})
                    registros = resultado.get('registros_oficiais', {})
                    
                    if registros.get('registro_encontrado'):
                        story.append(Paragraph("Status: REGISTRO ENCONTRADO", styles['Normal']))
                        dados_prof = registros.get('dados_profissional', {})
                        if dados_prof.get('nome_completo_oficial'):
                            story.append(Paragraph(f"• Nome Oficial: {dados_prof['nome_completo_oficial']}", styles['Normal']))
                        if dados_prof.get('registro_crm_completo') or dados_prof.get('registro_completo'):
                            registro = dados_prof.get('registro_crm_completo') or dados_prof.get('registro_completo')
                            story.append(Paragraph(f"• Registro: {registro}", styles['Normal']))
                        if dados_prof.get('situacao_registro'):
                            story.append(Paragraph(f"• Situação: {dados_prof['situacao_registro']}", styles['Normal']))
                        if dados_prof.get('tipo_formacao'):
                            story.append(Paragraph(f"• Formação: {dados_prof['tipo_formacao']}", styles['Normal']))
                    else:
                        story.append(Paragraph("Status: BUSCA REALIZADA", styles['Normal']))
                    
                    resumo = resultado.get('resumo_investigacao', {})
                    if resumo.get('pontuacao_confiabilidade') is not None:
                        story.append(Paragraph(f"• Confiabilidade: {resumo['pontuacao_confiabilidade']}/100", styles['Normal']))
                    
                    story.append(Spacer(1, 8))
            
            story.append(Spacer(1, 20))
        
        # Rodapé
        story.append(Spacer(1, 30))
        story.append(Paragraph("_" * 80, styles['Normal']))
        story.append(Paragraph("Documento gerado automaticamente pelo sistema EviChain", styles['Italic']))
        
        # Construir PDF
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Retornar PDF como resposta
        from flask import make_response
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=denuncia_{complaint_id}.pdf'
        
        return response
        
    except ImportError:
        # Se reportlab não estiver disponível, retornar erro informativo
        return jsonify({
            'success': False,
            'error': 'Biblioteca reportlab não está instalada. Use: pip install reportlab'
        }), 500
    
    except Exception as e:
        print(f"[ERROR] Erro ao gerar PDF: {e}")
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
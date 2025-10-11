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
        timestamp = data.get('timestamp', datetime.now().isoformat())
        codigosAnteriores = data.get('codigosAnteriores')
        ouvidoriaAnonima = data.get('ouvidoriaAnonima', False)
        anonymous = data.get('anonymous', False)
        descricao = data.get('descricao', 'Não disponível')
        ia_analysis = data.get('ia_analysis', {})
        metadata = data.get('metadata', {})
        
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
        from io import BytesIO
        
        # Criar documento PDF em memória com margens profissionais
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=2*cm, leftMargin=2*cm,
                              topMargin=3*cm, bottomMargin=2*cm)
        
        # Estilos profissionais para relatório
        styles = getSampleStyleSheet()
        
        # Estilo do cabeçalho principal
        header_style = ParagraphStyle(
            'ReportHeader',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a365d')
        )
        
        # Estilo do subtítulo
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica',
            textColor=colors.HexColor('#2d3748')
        )
        
        # Estilo para seções principais
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2c5282'),
            borderWidth=1,
            borderColor=colors.HexColor('#e2e8f0'),
            borderPadding=8,
            backColor=colors.HexColor('#f7fafc')
        )
        
        # Estilo para subseções
        subsection_style = ParagraphStyle(
            'SubsectionHeader',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=12,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#4a5568')
        )
        
        # Estilo para texto normal com melhor formatação
        normal_style = ParagraphStyle(
            'ReportNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            leading=14
        )
        
        # Estilo para dados importantes
        important_style = ParagraphStyle(
            'ImportantData',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            alignment=TA_LEFT,
            fontName='Helvetica',
            textColor=colors.HexColor('#2d3748'),
            leftIndent=20
        )
        
        # Conteúdo do relatório
        story = []
        
        # Formatar data primeiro
        try:
            if timestamp:
                data_formatada = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
            else:
                data_formatada = datetime.now().strftime('%d/%m/%Y %H:%M')
        except:
            data_formatada = timestamp or datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # === CABEÇALHO FORMAL DO RELATÓRIO ===
        
        # Logo/Título institucional
        story.append(Paragraph("EVICHAIN", header_style))
        story.append(Paragraph("Sistema Blockchain para Evidências Digitais", subtitle_style))
        
        # Linha divisória
        story.append(Spacer(1, 10))
        divider_table = Table([['_' * 80]], colWidths=[15*cm])
        divider_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#a0aec0'))
        ]))
        story.append(divider_table)
        story.append(Spacer(1, 20))
        
        # Título do relatório
        story.append(Paragraph("RELATÓRIO DE ANÁLISE DE DENÚNCIA", header_style))
        story.append(Spacer(1, 10))
        
        # Informações do documento
        doc_info_data = [
            ['ID da Denúncia:', complaint_id],
            ['Data de Geração:', data_formatada],
            ['Documento:', f'EviChain_Relatorio_{complaint_id}_{datetime.now().strftime("%Y-%m-%d")}.pdf'],
            ['Status:', 'CONFIDENCIAL - USO RESTRITO']
        ]
        
        doc_info_table = Table(doc_info_data, colWidths=[4*cm, 10*cm])
        doc_info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(doc_info_table)
        story.append(Spacer(1, 30))
        
        # === SEÇÃO 1: INFORMAÇÕES BÁSICAS DA DENÚNCIA ===
        story.append(Paragraph("1. INFORMAÇÕES BÁSICAS DA DENÚNCIA", section_style))
        
        # Criar tabela para informações básicas
        basic_info_data = [
            ['Título:', titulo],
            ['Assunto:', assunto],
            ['Prioridade:', prioridade],
            ['Finalidade:', finalidade],
            ['Conselho:', conselho],
            ['Categoria:', categoria],
            ['Data de Registro:', data_formatada],
            ['Status:', 'Registrada e Analisada']
        ]
        
        if codigosAnteriores:
            basic_info_data.append(['Códigos Anteriores:', codigosAnteriores])
        
        basic_info_table = Table(basic_info_data, colWidths=[4*cm, 11*cm])
        basic_info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(basic_info_table)
        story.append(Spacer(1, 20))
        
        # === SEÇÃO 2: CONFIGURAÇÕES DE PRIVACIDADE ===
        story.append(Paragraph("2. CONFIGURAÇÕES DE PRIVACIDADE", section_style))
        
        privacy_data = [
            ['Ouvidoria Anônima:', 'Sim' if ouvidoriaAnonima else 'Não'],
            ['Manter Anonimato:', 'Sim' if anonymous else 'Não']
        ]
        
        privacy_table = Table(privacy_data, colWidths=[4*cm, 11*cm])
        privacy_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(privacy_table)
        story.append(Spacer(1, 20))
        
        # === SEÇÃO 3: DESCRIÇÃO DA DENÚNCIA ===
        story.append(Paragraph("3. DESCRIÇÃO DA DENÚNCIA", section_style))
        story.append(Paragraph(descricao, normal_style))
        story.append(Spacer(1, 25))
        
        # === SEÇÃO 4: ANÁLISE DA INTELIGÊNCIA ARTIFICIAL ===
        if ia_analysis:
            story.append(Paragraph("4. ANÁLISE DA INTELIGÊNCIA ARTIFICIAL", section_style))
            story.append(Spacer(1, 10))
            
            # Informações básicas da análise
            analise_juridica = ia_analysis.get('analise_juridica', {})
            classificacao_risco = ia_analysis.get('classificacao_risco', {})
            analise_basica = ia_analysis.get('analise_basica', {})
            
            # Criar tabela de análise principal
            analise_data = []
            
            if analise_juridica.get('gravidade'):
                analise_data.append(['Gravidade:', analise_juridica['gravidade'].title()])
            
            if analise_juridica.get('tipificacao'):
                analise_data.append(['Tipificação:', analise_juridica['tipificacao']])
            
            if classificacao_risco.get('nivel') and classificacao_risco.get('pontuacao'):
                nivel = classificacao_risco['nivel']
                pontuacao = classificacao_risco['pontuacao']
                analise_data.append(['Nível de Risco:', f"{nivel} ({pontuacao}/100)"])
            
            if classificacao_risco.get('acao_recomendada'):
                analise_data.append(['Ação Recomendada:', classificacao_risco['acao_recomendada']])
            
            if analise_data:
                analise_table = Table(analise_data, colWidths=[4*cm, 11*cm])
                analise_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
                    ('PADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(analise_table)
                story.append(Spacer(1, 15))
            
            # Resumo da análise
            if analise_basica.get('resumo'):
                story.append(Paragraph("4.1 Resumo da Análise", subsection_style))
                story.append(Paragraph(analise_basica['resumo'], normal_style))
                story.append(Spacer(1, 12))
            
            if analise_juridica.get('fundamentacao'):
                story.append(Paragraph("4.2 Análise Detalhada", subsection_style))
                story.append(Paragraph(analise_juridica['fundamentacao'], normal_style))
                story.append(Spacer(1, 12))
            
            # === SUBSEÇÃO: LEGISLAÇÃO RECOMENDADA ===
            legislacao_especifica = analise_juridica.get('legislacao_especifica', {})
            if legislacao_especifica:
                story.append(Paragraph("4.3 Legislação Recomendada pela IA", subsection_style))
                
                leg_data = []
                if legislacao_especifica.get('legislacao_sugerida'):
                    leg_data.append(['Legislação Sugerida:', legislacao_especifica['legislacao_sugerida']])
                
                if legislacao_especifica.get('conselho'):
                    leg_data.append(['Conselho:', legislacao_especifica['conselho']])
                
                if legislacao_especifica.get('tipo'):
                    leg_data.append(['Tipo de Infração:', legislacao_especifica['tipo']])
                
                if legislacao_especifica.get('descricao'):
                    leg_data.append(['Descrição:', legislacao_especifica['descricao']])
                
                if legislacao_especifica.get('artigos'):
                    artigos = legislacao_especifica['artigos']
                    if isinstance(artigos, list):
                        artigos = ' '.join(artigos)
                    leg_data.append(['Artigos:', artigos])
                
                if legislacao_especifica.get('penalidades'):
                    penalidades = legislacao_especifica['penalidades']
                    if isinstance(penalidades, list):
                        penalidades = ', '.join(penalidades)
                    leg_data.append(['Penalidades:', penalidades])
                
                if leg_data:
                    leg_table = Table(leg_data, colWidths=[4*cm, 11*cm])
                    leg_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fff8dc')),
                        ('PADDING', (0, 0), (-1, -1), 8),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    story.append(leg_table)
                    story.append(Spacer(1, 12))
            
            # === SUBSEÇÃO: PALAVRAS-CHAVE ===
            palavras_chave = analise_basica.get('palavras_chave', [])
            if palavras_chave:
                story.append(Paragraph("4.4 Palavras-Chave Identificadas", subsection_style))
                if isinstance(palavras_chave, list):
                    for palavra in palavras_chave:
                        story.append(Paragraph(f"• {palavra}", important_style))
                else:
                    story.append(Paragraph(palavras_chave, normal_style))
                story.append(Spacer(1, 12))
            
            # === SUBSEÇÃO: RECOMENDAÇÕES ===
            recomendacoes = ia_analysis.get('recomendacoes', [])
            if recomendacoes:
                story.append(Paragraph("4.5 Recomendações", subsection_style))
                if isinstance(recomendacoes, list):
                    for rec in recomendacoes:
                        story.append(Paragraph(f"• {rec}", important_style))
                else:
                    story.append(Paragraph(recomendacoes, normal_style))
                story.append(Spacer(1, 12))
            
            # Fatores de risco
            fatores_risco = classificacao_risco.get('fatores_risco', [])
            if fatores_risco and isinstance(fatores_risco, list):
                story.append(Paragraph("4.6 Fatores de Risco", subsection_style))
                for fator in fatores_risco:
                    story.append(Paragraph(f"• {fator}", important_style))
                story.append(Spacer(1, 15))
            
            story.append(Spacer(1, 20))
        
        # === SEÇÃO 5: INVESTIGAÇÃO AUTOMÁTICA ===
        investigacao = ia_analysis.get('investigacao_automatica', {}) if ia_analysis else {}
        if investigacao:
            story.append(Paragraph("5. INVESTIGAÇÃO AUTOMÁTICA REALIZADA", section_style))
            story.append(Spacer(1, 10))
            
            # Relatório de detecção formatado
            if 'relatorio_deteccao' in investigacao:
                story.append(Paragraph("5.1 Relatório de Detecção de Profissionais", subsection_style))
                
                deteccao = investigacao.get('deteccao_nomes', {})
                
                # Estatísticas gerais em tabela
                stats_data = []
                if deteccao.get('confiabilidade_deteccao') is not None:
                    stats_data.append(['Confiabilidade Geral:', f"{deteccao.get('confiabilidade_deteccao', 0)}%"])
                
                if deteccao.get('contexto_profissional') is not None:
                    contexto = "SIM" if deteccao.get('contexto_profissional') else "NÃO"
                    stats_data.append(['Contexto Profissional Detectado:', contexto])
                
                if deteccao.get('recomendacao_investigacao') is not None:
                    recomenda = "SIM" if deteccao.get('recomendacao_investigacao') else "NÃO"
                    stats_data.append(['Recomenda Investigação:', recomenda])
                
                if stats_data:
                    stats_table = Table(stats_data, colWidths=[6*cm, 9*cm])
                    stats_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f8ff')),
                        ('PADDING', (0, 0), (-1, -1), 8),
                    ]))
                    story.append(stats_table)
                    story.append(Spacer(1, 15))
            
            # Profissionais identificados de forma organizada
            deteccao = investigacao.get('deteccao_nomes', {})
            if deteccao.get('nomes_detectados'):
                story.append(Paragraph("5.2 Profissionais Identificados", subsection_style))
                
                # Criar tabela para profissionais detectados
                prof_data = [['#', 'Nome Detectado', 'Confiabilidade', 'Contexto']]
                
                for i, nome in enumerate(deteccao['nomes_detectados'], 1):
                    nome_profissional = nome.get('nome_detectado', f'Profissional {i}')
                    confiabilidade = f"{nome.get('confiabilidade', 0)}%"
                    contexto = nome.get('contexto_encontrado', 'N/A')
                    
                    prof_data.append([str(i), nome_profissional, confiabilidade, contexto])
                
                prof_table = Table(prof_data, colWidths=[1*cm, 5*cm, 2.5*cm, 6.5*cm])
                prof_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(prof_table)
                story.append(Spacer(1, 15))
            
            # Resultados das investigações de forma organizada
            investigacoes = investigacao.get('investigacoes_realizadas', [])
            if investigacoes:
                story.append(Paragraph("5.3 Resultados das Investigações Detalhadas", subsection_style))
                
                for i, inv in enumerate(investigacoes, 1):
                    nome_investigado = inv.get('nome_investigado', f'Investigação {i}')
                    story.append(Paragraph(f"5.3.{i} Investigação: {nome_investigado}", subsection_style))
                    
                    resultado = inv.get('resultado_investigacao', {})
                    registros = resultado.get('registros_oficiais', {})
                    
                    inv_data = []
                    
                    if registros.get('registro_encontrado'):
                        inv_data.append(['Status:', 'REGISTRO ENCONTRADO ✓'])
                        
                        dados_prof = registros.get('dados_profissional', {})
                        if dados_prof.get('nome_completo_oficial'):
                            inv_data.append(['Nome Oficial:', dados_prof['nome_completo_oficial']])
                        
                        if dados_prof.get('registro_crm_completo') or dados_prof.get('registro_completo'):
                            registro = dados_prof.get('registro_crm_completo') or dados_prof.get('registro_completo')
                            inv_data.append(['Registro:', registro])
                        
                        if dados_prof.get('situacao_registro'):
                            inv_data.append(['Situação:', dados_prof['situacao_registro']])
                        
                        if dados_prof.get('especialidades'):
                            especialidades = ', '.join(dados_prof['especialidades'])
                            inv_data.append(['Especialidades:', especialidades])
                            
                    else:
                        inv_data.append(['Status:', 'REGISTRO NÃO ENCONTRADO ✗'])
                        if resultado.get('motivo_nao_encontrado'):
                            inv_data.append(['Motivo:', resultado['motivo_nao_encontrado']])
                    
                    if inv_data:
                        inv_table = Table(inv_data, colWidths=[3*cm, 12*cm])
                        inv_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0fff0')),
                            ('PADDING', (0, 0), (-1, -1), 6),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ]))
                        story.append(inv_table)
                        story.append(Spacer(1, 12))
                
                story.append(Spacer(1, 15))
        
        # === RODAPÉ FORMAL DO RELATÓRIO ===
        story.append(Spacer(1, 30))
        
        # Assinatura digital
        footer_data = [
            ['', ''],
            ['Documento gerado automaticamente pelo', ''],
            ['Sistema EviChain v2.1', ''],
            ['Blockchain para Evidências Digitais', ''],
            ['', ''],
            [f'Data/Hora de Geração: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}', ''],
            ['Este documento possui validade jurídica conforme', ''],
            ['Lei 14.063/2020 (Marco Legal das Assinaturas Eletrônicas)', '']
        ]
        
        footer_table = Table(footer_data, colWidths=[15*cm, 0*cm])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#6b7280')),
            ('FONTNAME', (0, 2), (0, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (0, 2), 10),
            ('TEXTCOLOR', (0, 2), (0, 2), colors.HexColor('#1f2937')),
        ]))
        story.append(footer_table)
        
        # Linha final
        story.append(Spacer(1, 10))
        final_line = Table([['_' * 80]], colWidths=[15*cm])
        final_line.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#a0aec0'))
        ]))
        story.append(final_line)
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
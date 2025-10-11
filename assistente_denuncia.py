#!/usr/bin/env python3
"""
Assistente de IA para Melhorar Denúncias - VERSÃO CORRIGIDA
Analisa o texto da denúncia e sugere melhorias
Integrado com OpenAI v1.x para sugestões mais inteligentes
"""

from typing import Dict, List
import re
import os
import json

# Importação corrigida - importar apenas o módulo openai
try:
    import openai
    from openai import OpenAI, AuthenticationError
    OPENAI_DISPONIVEL = True
except ImportError:
    OPENAI_DISPONIVEL = False
    print("[WARN] Biblioteca openai não instalada. Use: pip install openai>=1.0.0")


class AssistenteDenuncia:
    """Assistente que ajuda a melhorar a qualidade das denúncias"""
    
    def __init__(self):
        # Inicializar cliente OpenAI (versão 1.x)
        self.client = None
        self.usar_openai = False
        
        # SEMPRE inicializar os atributos essenciais primeiro
        # Elementos essenciais de uma denúncia
        self.elementos_essenciais = {
            "quem": {
                "nome": "Nome ou identificação do profissional",
                "keywords": ["nome", "dr.", "dra.", "profissional", "médico", "advogado", "engenheiro"],
                "peso": 10
            },
            "o_que": {
                "nome": "O que aconteceu (fatos)",
                "keywords": ["fez", "deixou de", "realizou", "não", "omitiu", "negligenciou"],
                "peso": 10
            },
            "quando": {
                "nome": "Quando aconteceu (data/período)",
                "keywords": ["dia", "data", "em", "durante", "no dia", "mês", "ano", "2024", "2025"],
                "peso": 8
            },
            "onde": {
                "nome": "Onde aconteceu (local)",
                "keywords": ["hospital", "consultório", "clínica", "escritório", "obra", "local", "endereço"],
                "peso": 7
            },
            "como": {
                "nome": "Como aconteceu (circunstâncias)",
                "keywords": ["porque", "pois", "devido", "causou", "resultou", "consequência"],
                "peso": 6
            },
            "consequencias": {
                "nome": "Consequências/danos",
                "keywords": ["dano", "prejuízo", "lesão", "morte", "sequela", "perda", "sofreu"],
                "peso": 9
            }
        }
        
        # Problemas comuns em denúncias
        self.problemas_comuns = [
            {
                "tipo": "texto_curto",
                "condicao": lambda texto: len(texto) < 100,
                "mensagem": "Texto muito curto. Adicione mais detalhes sobre o que aconteceu.",
                "sugestao": "Descreva os fatos com mais detalhes: quem, o que, quando, onde e como."
            },
            {
                "tipo": "sem_data",
                "condicao": lambda texto: not any(palavra in texto.lower() for palavra in ["dia", "data", "em", "durante", "2024", "2025"]),
                "mensagem": "Não identificamos uma data ou período.",
                "sugestao": "Informe quando os fatos ocorreram (dia, mês, ano ou período)."
            },
            {
                "tipo": "sem_local",
                "condicao": lambda texto: not any(palavra in texto.lower() for palavra in ["hospital", "consultório", "clínica", "escritório", "obra", "local"]),
                "mensagem": "Não identificamos o local dos fatos.",
                "sugestao": "Informe onde aconteceu (hospital, consultório, endereço, etc.)."
            },
            {
                "tipo": "sem_consequencias",
                "condicao": lambda texto: not any(palavra in texto.lower() for palavra in ["dano", "prejuízo", "lesão", "morte", "sequela", "perda", "sofreu"]),
                "mensagem": "Não identificamos as consequências do ocorrido.",
                "sugestao": "Descreva os danos ou prejuízos causados."
            },
            {
                "tipo": "texto_emocional",
                "condicao": lambda texto: sum(1 for palavra in ["horrível", "péssimo", "terrível", "absurdo", "ridículo"] if palavra in texto.lower()) > 2,
                "mensagem": "Texto com muitas expressões emocionais.",
                "sugestao": "Prefira uma linguagem objetiva e factual, focando nos fatos concretos."
            },
            {
                "tipo": "falta_identificacao",
                "condicao": lambda texto: not any(palavra in texto.lower() for palavra in ["dr.", "dra.", "nome", "profissional", "médico", "advogado"]),
                "mensagem": "Não identificamos o profissional denunciado.",
                "sugestao": "Identifique o profissional (nome, registro, local de trabalho)."
            }
        ]
        
        # Agora tentar configurar OpenAI (se disponível)
        if not OPENAI_DISPONIVEL:
            print("[INFO] OpenAI não disponível - usando análise local")
            return
        
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "sua_api_key_aqui":
            try:
                # Usar a sintaxe correta do OpenAI v1.x
                self.client = OpenAI(
                    api_key=api_key,
                    timeout=30.0,
                    max_retries=1
                )
                
                # Testar conexão
                test_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "teste"}],
                    max_tokens=5
                )
                
                self.usar_openai = True
                print("[INFO] Assistente configurado com OpenAI v1.x")
                
            except AuthenticationError:
                print("[WARN] Erro de autenticação OpenAI: API Key inválida")
                self.usar_openai = False
            except Exception as e:
                print(f"[WARN] Falha ao configurar OpenAI: {e}")
                self.usar_openai = False
        else:
            print("[INFO] OpenAI não configurado - usando análise local")
    
    def analisar_denuncia(self, texto: str, conselho: str = None, categoria: str = None) -> Dict:
        """
        Analisa a denúncia e retorna sugestões de melhoria
        
        Args:
            texto: Texto da denúncia
            conselho: Conselho profissional (opcional)
            categoria: Categoria da infração (opcional)
            
        Returns:
            Dict com análise completa e sugestões
        """
        # Tentar usar OpenAI primeiro
        if self.usar_openai and self.client:
            try:
                return self._analisar_com_openai(texto, conselho, categoria)
            except Exception as e:
                print(f"[WARN] Falha ao usar OpenAI, usando análise local: {e}")
        
        # Fallback para análise local
        return self._analisar_local(texto, conselho, categoria)
    
    def _analisar_com_openai(self, texto: str, conselho: str = None, categoria: str = None) -> Dict:
        """Analisa usando OpenAI para sugestões mais inteligentes"""
        print("[INFO] Analisando com OpenAI...")
        
        prompt = f"""Você é um assistente especializado em ajudar pessoas a escrever denúncias profissionais completas e eficazes.

Analise o seguinte texto de denúncia e forneça:
1. Pontuação de qualidade (0-100)
2. Elementos presentes e faltantes (Quem, Quando, Onde, Consequências)
3. Sugestões específicas de melhoria
4. Versão melhorada do texto com estrutura organizada

TEXTO DA DENÚNCIA:
"{texto}"

CONTEXTO:
- Conselho: {conselho or 'Não especificado'}
- Categoria: {categoria or 'Não especificada'}

Retorne APENAS um JSON no seguinte formato:
{{
    "pontuacao_qualidade": 0-100,
    "elementos_presentes": ["lista de elementos presentes"],
    "elementos_faltantes": ["lista de elementos faltantes"],
    "sugestoes": ["lista de sugestões específicas"],
    "texto_melhorado": "versão melhorada do texto",
    "explicacao_melhorias": ["lista de explicações das melhorias"]
}}"""

        # Usar a sintaxe correta do OpenAI v1.x
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em análise de denúncias profissionais."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        resposta_texto = response.choices[0].message.content.strip()
        
        # Extrair JSON da resposta
        try:
            # Tentar encontrar JSON na resposta
            inicio = resposta_texto.find('{')
            fim = resposta_texto.rfind('}') + 1
            if inicio != -1 and fim > inicio:
                json_str = resposta_texto[inicio:fim]
                analise_openai = json.loads(json_str)
            else:
                raise ValueError("JSON não encontrado na resposta")
        except Exception as e:
            print(f"[WARN] Erro ao parsear resposta OpenAI: {e}")
            return self._analisar_local(texto, conselho, categoria)
        
        # Converter para formato padrão
        resultado = {
            "texto_original": texto,
            "tamanho": len(texto),
            "palavras": len(texto.split()),
            "elementos_presentes": [{"nome": elem} for elem in analise_openai.get("elementos_presentes", [])],
            "elementos_faltantes": [{"nome": elem} for elem in analise_openai.get("elementos_faltantes", [])],
            "problemas_identificados": [],
            "sugestoes": analise_openai.get("sugestoes", []),
            "pontuacao_qualidade": analise_openai.get("pontuacao_qualidade", 50),
            "texto_melhorado": analise_openai.get("texto_melhorado", texto),
            "explicacao_melhorias": analise_openai.get("explicacao_melhorias", []),
            "fonte": "OpenAI"
        }
        
        print(f"[INFO] Análise OpenAI concluída - Pontuação: {resultado['pontuacao_qualidade']}/100")
        return resultado
    
    def _analisar_local(self, texto: str, conselho: str = None, categoria: str = None) -> Dict:
        """Análise local quando OpenAI não está disponível"""
        print("[INFO] Analisando localmente...")
        
        resultado = {
            "texto_original": texto,
            "tamanho": len(texto),
            "palavras": len(texto.split()),
            "elementos_presentes": [],
            "elementos_faltantes": [],
            "problemas_identificados": [],
            "sugestoes": [],
            "pontuacao_qualidade": 0,
            "texto_melhorado": "",
            "explicacao_melhorias": [],
            "fonte": "Local"
        }
        
        # 1. Verificar elementos essenciais
        for elemento_id, elemento_info in self.elementos_essenciais.items():
            presente = any(keyword in texto.lower() for keyword in elemento_info["keywords"])
            if presente:
                resultado["elementos_presentes"].append({
                    "elemento": elemento_id,
                    "nome": elemento_info["nome"],
                    "peso": elemento_info["peso"]
                })
                resultado["pontuacao_qualidade"] += elemento_info["peso"]
            else:
                resultado["elementos_faltantes"].append({
                    "elemento": elemento_id,
                    "nome": elemento_info["nome"],
                    "peso": elemento_info["peso"]
                })
        
        # 2. Identificar problemas comuns
        for problema in self.problemas_comuns:
            if problema["condicao"](texto):
                resultado["problemas_identificados"].append({
                    "tipo": problema["tipo"],
                    "mensagem": problema["mensagem"],
                    "sugestao": problema["sugestao"]
                })
        
        # 3. Gerar sugestões específicas
        resultado["sugestoes"] = self._gerar_sugestoes(texto, resultado["elementos_faltantes"], conselho, categoria)
        
        # 4. Gerar texto melhorado
        resultado["texto_melhorado"] = self._gerar_texto_melhorado(texto, resultado["elementos_faltantes"], conselho, categoria)
        
        # 5. Explicar melhorias
        resultado["explicacao_melhorias"] = self._explicar_melhorias(texto, resultado["texto_melhorado"], resultado["elementos_faltantes"])
        
        # 6. Calcular pontuação final (0-100)
        pontuacao_maxima = sum(info["peso"] for info in self.elementos_essenciais.values())
        resultado["pontuacao_qualidade"] = int((resultado["pontuacao_qualidade"] / pontuacao_maxima) * 100)
        
        return resultado
    
    def _gerar_sugestoes(self, texto: str, elementos_faltantes: List[Dict], conselho: str, categoria: str) -> List[str]:
        """Gera sugestões específicas de melhoria"""
        sugestoes = []
        
        # Sugestões baseadas em elementos faltantes
        for elemento in elementos_faltantes:
            if elemento["elemento"] == "quem":
                sugestoes.append("📝 Identifique o profissional: nome completo, número de registro (CRM, OAB, etc.) e local de trabalho.")
            elif elemento["elemento"] == "quando":
                sugestoes.append("📅 Informe a data ou período: dia/mês/ano ou período aproximado (ex: 'entre 10 e 15 de setembro de 2025').")
            elif elemento["elemento"] == "onde":
                sugestoes.append("📍 Descreva o local: nome do hospital/consultório/escritório e endereço, se possível.")
            elif elemento["elemento"] == "consequencias":
                sugestoes.append("⚠️ Descreva as consequências: danos físicos, prejuízos financeiros, sequelas, etc.")
        
        # Sugestões baseadas no conselho
        if conselho:
            if conselho == "CRM":
                sugestoes.append("🏥 Para denúncias médicas, inclua: sintomas apresentados, procedimento realizado/omitido, resultado/complicação.")
            elif conselho == "OAB":
                sugestoes.append("⚖️ Para denúncias advocatícias, inclua: número do processo, tipo de ação, honorários cobrados, prazo descumprido.")
            elif conselho == "CREA":
                sugestoes.append("🏗️ Para denúncias de engenharia, inclua: tipo de obra/projeto, ART, problema técnico identificado.")
        
        # Sugestões gerais
        if len(texto) < 200:
            sugestoes.append("✍️ Amplie a descrição: quanto mais detalhes, melhor a análise e investigação.")
        
        sugestoes.append("📎 Se possível, mencione se há documentos, fotos ou testemunhas que comprovem os fatos.")
        
        return sugestoes
    
    def _gerar_texto_melhorado(self, texto: str, elementos_faltantes: List[Dict], conselho: str, categoria: str) -> str:
        """Gera uma versão melhorada do texto"""
        texto_melhorado = texto.strip()
        
        # Se o texto é muito curto, adicionar estrutura
        if len(texto) < 100:
            template = f"""Denúncia contra profissional do {conselho or '[CONSELHO]'} por {categoria or '[CATEGORIA]'}.

FATOS:
{texto}

[ADICIONE AQUI: Quando ocorreu - data ou período]
[ADICIONE AQUI: Onde ocorreu - local específico]
[ADICIONE AQUI: Consequências - danos ou prejuízos causados]

DOCUMENTOS/PROVAS:
[Se houver, mencione: documentos, fotos, laudos, testemunhas, etc.]"""
            return template
        
        # Se o texto é razoável, apenas sugerir complementos
        complementos = []
        
        for elemento in elementos_faltantes:
            if elemento["elemento"] == "quando":
                complementos.append("\n\n[ADICIONE: Data ou período em que os fatos ocorreram]")
            elif elemento["elemento"] == "onde":
                complementos.append("\n\n[ADICIONE: Local onde os fatos ocorreram (hospital, consultório, endereço)]")
            elif elemento["elemento"] == "consequencias":
                complementos.append("\n\n[ADICIONE: Consequências/danos causados pelos fatos]")
        
        if complementos:
            texto_melhorado += "".join(complementos)
        
        return texto_melhorado
    
    def _explicar_melhorias(self, texto_original: str, texto_melhorado: str, elementos_faltantes: List[Dict]) -> List[str]:
        """Explica as melhorias sugeridas"""
        explicacoes = []
        
        if len(texto_original) < 100:
            explicacoes.append("✅ Adicionamos uma estrutura organizada para facilitar o preenchimento.")
        
        for elemento in elementos_faltantes:
            if elemento["elemento"] == "quando":
                explicacoes.append("📅 Adicionamos campo para data/período - essencial para investigação.")
            elif elemento["elemento"] == "onde":
                explicacoes.append("📍 Adicionamos campo para local - ajuda a identificar o contexto.")
            elif elemento["elemento"] == "consequencias":
                explicacoes.append("⚠️ Adicionamos campo para consequências - demonstra a gravidade dos fatos.")
        
        if not explicacoes:
            explicacoes.append("✅ O texto já possui boa estrutura. Revisamos a organização.")
        
        return explicacoes
    
    def gerar_relatorio_html(self, analise: Dict) -> str:
        """Gera um relatório HTML formatado da análise"""
        
        # Definir cor baseada na pontuação
        pontuacao = analise.get("pontuacao_qualidade", 0)
        if pontuacao >= 80:
            cor_pontuacao = "#28a745"  # Verde
            status = "Excelente"
        elif pontuacao >= 60:
            cor_pontuacao = "#ffc107"  # Amarelo
            status = "Bom"
        elif pontuacao >= 40:
            cor_pontuacao = "#fd7e14"  # Laranja
            status = "Regular"
        else:
            cor_pontuacao = "#dc3545"  # Vermelho
            status = "Precisa melhorar"
        
        # Elementos presentes
        elementos_presentes_html = ""
        for elem in analise.get("elementos_presentes", []):
            nome = elem.get("nome", elem) if isinstance(elem, dict) else elem
            elementos_presentes_html += f"<li>✅ {nome}</li>"
        
        # Elementos faltantes
        elementos_faltantes_html = ""
        for elem in analise.get("elementos_faltantes", []):
            nome = elem.get("nome", elem) if isinstance(elem, dict) else elem
            elementos_faltantes_html += f"<li>❌ {nome}</li>"
        
        # Sugestões
        sugestoes_html = ""
        for sugestao in analise.get("sugestoes", []):
            sugestoes_html += f"<li>{sugestao}</li>"
        
        # Problemas identificados
        problemas_html = ""
        for problema in analise.get("problemas_identificados", []):
            mensagem = problema.get("mensagem", problema) if isinstance(problema, dict) else problema
            problemas_html += f"<li>{mensagem}</li>"
        
        # Explicações das melhorias
        explicacoes_html = ""
        for explicacao in analise.get("explicacao_melhorias", []):
            explicacoes_html += f"<li>{explicacao}</li>"
        
        # Texto melhorado
        texto_melhorado = analise.get("texto_melhorado", "").replace("\n", "<br>")
        
        # Fonte da análise
        fonte = analise.get("fonte", "Local")
        badge_fonte = f'<span class="badge badge-info">Análise: {fonte}</span>'
        
        # Construir HTML sem f-string para evitar conflitos com CSS
        problemas_section = f'''
            <div class="secao-analise">
                <h4>⚠️ Problemas Identificados</h4>
                <ul class="lista-problemas">
                    {problemas_html}
                </ul>
            </div>
            ''' if problemas_html else ''
        
        explicacoes_section = f'''
                <div class="explicacoes-melhorias">
                    <h5>O que foi melhorado:</h5>
                    <ul>
                        {explicacoes_html}
                    </ul>
                </div>
                ''' if explicacoes_html else ''
        
        html = f"""
        <div class="analise-resultado">
            <div class="header-analise">
                <h3>📊 Análise da Denúncia</h3>
                {badge_fonte}
            </div>
            
            <div class="pontuacao-box" style="background: linear-gradient(135deg, {cor_pontuacao}22, {cor_pontuacao}11);">
                <div class="pontuacao-numero" style="color: {cor_pontuacao};">{pontuacao}/100</div>
                <div class="pontuacao-status">{status}</div>
            </div>
            
            <div class="secao-analise">
                <h4>📋 Elementos da Denúncia</h4>
                <div class="row">
                    <div class="col-md-6">
                        <h5>Presentes:</h5>
                        <ul class="lista-elementos">
                            {elementos_presentes_html or '<li>Nenhum elemento identificado</li>'}
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h5>Faltantes:</h5>
                        <ul class="lista-elementos">
                            {elementos_faltantes_html or '<li>Todos os elementos presentes!</li>'}
                        </ul>
                    </div>
                </div>
            </div>
            
            {problemas_section}
            
            <div class="secao-analise">
                <h4>💡 Sugestões de Melhoria</h4>
                <ul class="lista-sugestoes">
                    {sugestoes_html or '<li>Nenhuma sugestão adicional</li>'}
                </ul>
            </div>
            
            <div class="secao-analise">
                <h4>✨ Texto Melhorado</h4>
                <div class="texto-melhorado">
                    {texto_melhorado}
                </div>
                {explicacoes_section}
            </div>
            
            <div class="info-analise">
                <small>
                    📝 Texto original: {analise.get('tamanho', 0)} caracteres, {analise.get('palavras', 0)} palavras
                </small>
            </div>
        </div>
        """ + """
        <style>
            .analise-resultado {
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin: 20px 0;
            }
            
            .header-analise {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 2px solid #e9ecef;
            }
            
            .header-analise h3 {
                margin: 0;
                color: #2c3e50;
            }
            
            .badge {
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 600;
            }
            
            .badge-info {
                background: #17a2b8;
                color: white;
            }
            
            .pontuacao-box {
                text-align: center;
                padding: 30px;
                border-radius: 12px;
                margin: 20px 0;
            }
            
            .pontuacao-numero {
                font-size: 3em;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .pontuacao-status {
                font-size: 1.2em;
                color: #6c757d;
                font-weight: 500;
            }
            
            .secao-analise {
                margin: 25px 0;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
            }
            
            .secao-analise h4 {
                color: #2c3e50;
                margin-bottom: 15px;
                font-size: 1.3em;
            }
            
            .secao-analise h5 {
                color: #495057;
                margin-bottom: 10px;
                font-size: 1.1em;
            }
            
            .lista-elementos, .lista-problemas, .lista-sugestoes {
                list-style: none;
                padding: 0;
            }
            
            .lista-elementos li, .lista-problemas li, .lista-sugestoes li {
                padding: 8px 0;
                border-bottom: 1px solid #dee2e6;
            }
            
            .lista-elementos li:last-child, 
            .lista-problemas li:last-child, 
            .lista-sugestoes li:last-child {
                border-bottom: none;
            }
            
            .texto-melhorado {
                background: white;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #28a745;
                margin: 15px 0;
                line-height: 1.6;
                color: #495057;
            }
            
            .explicacoes-melhorias {
                margin-top: 15px;
                padding: 15px;
                background: #e7f3ff;
                border-radius: 8px;
            }
            
            .explicacoes-melhorias h5 {
                color: #0066cc;
                margin-bottom: 10px;
            }
            
            .explicacoes-melhorias ul {
                margin: 0;
                padding-left: 20px;
            }
            
            .explicacoes-melhorias li {
                margin: 5px 0;
                color: #495057;
            }
            
            .info-analise {
                margin-top: 20px;
                padding-top: 15px;
                border-top: 1px solid #dee2e6;
                color: #6c757d;
                text-align: center;
            }
            
            .row {
                display: flex;
                flex-wrap: wrap;
                margin: 0 -15px;
            }
            
            .col-md-6 {
                flex: 0 0 50%;
                max-width: 50%;
                padding: 0 15px;
            }
            
            @media (max-width: 768px) {
                .col-md-6 {
                    flex: 0 0 100%;
                    max-width: 100%;
                }
            }
        </style>
        """
        
        return html


# Teste rápido
if __name__ == "__main__":
    print("=== Teste do Assistente de Denúncia ===\n")
    
    assistente = AssistenteDenuncia()
    
    # Texto de teste
    texto_teste = """
    O médico não me atendeu direito e fui embora com dor.
    """
    
    print("Analisando texto de teste...")
    resultado = assistente.analisar_denuncia(texto_teste.strip(), "CRM", "Negligência")
    
    print(f"\n✅ Análise concluída!")
    print(f"📊 Pontuação: {resultado['pontuacao_qualidade']}/100")
    print(f"🔍 Fonte: {resultado['fonte']}")
    print(f"📝 Elementos presentes: {len(resultado['elementos_presentes'])}")
    print(f"❌ Elementos faltantes: {len(resultado['elementos_faltantes'])}")
    print(f"💡 Sugestões: {len(resultado['sugestoes'])}")
    
    print("\n=== Teste concluído ===")


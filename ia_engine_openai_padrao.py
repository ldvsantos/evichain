import os
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime
from time import perf_counter
from typing import Any, Dict, Optional

# CORREÇÃO: Importar as classes corretamente
try:
    from openai import OpenAI
    OPENAI_DISPONIVEL = True
except ImportError:
    OPENAI_DISPONIVEL = False
    print("[WARN] Biblioteca openai não instalada. Use: pip install openai>=1.0.0")

from ia_analisador_texto import AnalisadorTexto
from detector_nomes import DetectorNomes
from consultor_registros import ConsultorRegistrosProfissionais
from investigador_digital import InvestigadorDigital


class IAEngineOpenAIPadrao:
    def _citar_legislacao_especifica(self, conselho: str, categoria: str) -> Optional[Dict[str, Any]]:
        """Retorna a legislação específica do conselho e categoria, se existir."""
        # Normalizar o nome do conselho para encontrar a correspondência
        conselho_normalizado = conselho
        if conselho.startswith("CREF"):
            conselho_normalizado = "CREF"
        elif conselho.startswith("CRM"):
            conselho_normalizado = "CRM"
        elif conselho.startswith("OAB"):
            conselho_normalizado = "OAB"
        elif conselho.startswith("CREA"):
            conselho_normalizado = "CREA"
        elif conselho.startswith("CRO"):
            conselho_normalizado = "CRO"
        elif conselho.startswith("CRF"):
            conselho_normalizado = "CRF"
            
        if conselho_normalizado not in self.legislacao:
            return None
            
        info_conselho = self.legislacao[conselho_normalizado]
        mapa_categoria = {
            "Negligência": "negligencia",
            "negligencia": "negligencia",
            "Neglig": "negligencia",
            "Assédio": "assedio",
            "assedio": "assedio",
            "Má Conduta": "ma_conduta",
            "ma_conduta": "ma_conduta",
            "Fraude": "fraude",
            "fraude": "fraude",
            "Outra": "ma_conduta",
            "outra": "ma_conduta"
        }
        tipo_infracao = mapa_categoria.get(categoria, "ma_conduta")
        infracoes = info_conselho.get("infrações", {})
        if tipo_infracao in infracoes:
            infracao = infracoes[tipo_infracao]
            codigo_etica = info_conselho.get("codigo_etica", "")
            artigos = infracao.get("artigos", [])
            
            # Formatar legislação sugerida no formato desejado
            legislacao_sugerida = f"{codigo_etica}"
            if artigos:
                legislacao_sugerida += f" {', '.join(artigos)}"
            
            return {
                "conselho": info_conselho.get("nome_completo", conselho),
                "tipo": infracao.get("tipo", categoria),
                "artigos": artigos,
                "penalidades": infracao.get("penalidades", []),
                "descricao": infracao.get("descricao", ""),
                "legislacao_sugerida": legislacao_sugerida
            }
        return None
    """Motor de IA usando OpenAI para analise de denuncias com base de conhecimento legislativa"""

    def __init__(self) -> None:
        """Inicializa o motor de IA e o cliente OpenAI."""
        self.versao = "EviChain IA v2.1"
        self.client = None
        self.legislacao: Dict[str, Any] = {}
        self.analisador = AnalisadorTexto()
        
        # Inicializar componentes de investigação automática
        self.detector_nomes = DetectorNomes()
        self.consultor_registros = ConsultorRegistrosProfissionais()
        # Inicializar cache CONFEF com dados conhecidos
        self.consultor_registros._inicializar_cache_confef()
        self.investigador = InvestigadorDigital()

        # Carregar base de conhecimento legislativa
        self._carregar_legislacao()

        if not OPENAI_DISPONIVEL:
            print("[WARN] OpenAI não disponível. Usando fallback.")
            return

        api_key = os.getenv("OPENAI_API_KEY")
        project_id = os.getenv("OPENAI_PROJECT_ID")

        request_timeout_env = os.getenv("OPENAI_REQUEST_TIMEOUT", "20")
        client_timeout_env = os.getenv("OPENAI_CLIENT_TIMEOUT", "40")
        max_retries_env = os.getenv("OPENAI_MAX_RETRIES", "1")

        try:
            self._request_timeout = float(request_timeout_env)
        except ValueError:
            self._request_timeout = 20.0

        try:
            self._client_timeout = float(client_timeout_env)
        except ValueError:
            self._client_timeout = 40.0

        try:
            self._max_retries = max(0, int(max_retries_env))
        except ValueError:
            self._max_retries = 1

        if not api_key or not project_id:
            print("[WARN] Credenciais da OpenAI nao encontradas. Usando fallback.")
            return

        try:
            # CORREÇÃO: Usar apenas parâmetros suportados
            self.client = OpenAI(
                api_key=api_key,
                timeout=self._client_timeout,
                max_retries=self._max_retries
            )
            print(f"[INFO] IA OpenAI inicializada com sucesso")
        except Exception as exc:
            print(f"[WARN] Erro ao inicializar OpenAI: {exc}. Fallback habilitado.")
            self.client = None

    def _carregar_legislacao(self) -> None:
        """Carrega a base de conhecimento legislativa dos conselhos."""
        try:
            legislacao_path = os.path.join(os.path.dirname(__file__), 'legislacao_conselhos.json')
            if os.path.exists(legislacao_path):
                with open(legislacao_path, 'r', encoding='utf-8') as f:
                    self.legislacao = json.load(f)
                print(f"[INFO] Base de conhecimento carregada: {len(self.legislacao)} conselhos")
            else:
                print("[WARN] Arquivo legislacao_conselhos.json nao encontrado")
        except Exception as exc:
            print(f"[WARN] Erro ao carregar legislacao: {exc}")
            self.legislacao = {}

    def _obter_contexto_legislativo(self, conselho: str, categoria: str) -> str:
        """Obtém o contexto legislativo específico para o conselho e categoria."""
        if conselho not in self.legislacao:
            return "Legislação específica não disponível para este conselho."

        info_conselho = self.legislacao[conselho]
        contexto = f"\n=== CONTEXTO LEGISLATIVO ===\n"
        contexto += f"Conselho: {info_conselho['nome_completo']}\n"
        contexto += f"Código de Ética: {info_conselho['codigo_etica']}\n\n"

        # Mapear categoria para tipo de infração
        mapa_categoria = {
            "Negligência": "negligencia",
            "negligencia": "negligencia",
            "Neglig": "negligencia",
            "Assédio": "assedio",
            "assedio": "assedio",
            "Má Conduta": "ma_conduta",
            "ma_conduta": "ma_conduta",
            "Fraude": "fraude",
            "fraude": "fraude",
            "Outra": "ma_conduta",
            "outra": "ma_conduta"
        }

        tipo_infracao = mapa_categoria.get(categoria, "ma_conduta")
        
        if tipo_infracao in info_conselho.get("infracoes_comuns", {}):
            infracao = info_conselho["infracoes_comuns"][tipo_infracao]
            contexto += f"TIPO DE INFRAÇÃO: {infracao['tipo']}\n"
            contexto += f"Artigos Aplicáveis: {', '.join(infracao['artigos'])}\n"
            contexto += f"Penalidades: {', '.join(infracao['penalidades'])}\n"
            contexto += f"Elementos de Prova: {', '.join(infracao['elementos_prova'])}\n"

        return contexto

    def analisar_denuncia_completa(self, transaction_data: Dict[str, Any], trace_id: str = "N/A") -> Optional[Dict[str, Any]]:
        """
        Analisa a denúncia de forma completa usando OpenAI ou fallback local.
        AGORA INCLUI DETECÇÃO AUTOMÁTICA DE NOMES E INVESTIGAÇÃO
        
        Args:
            transaction_data: Dados da transação/denúncia
            trace_id: ID de rastreamento
            
        Returns:
            Dicionário com análise completa E investigação automática
        """
        descricao = transaction_data.get("descricao", "")
        conselho = transaction_data.get("conselho", "N/A")
        categoria = transaction_data.get("categoria", "N/A")

        if not descricao:
            return None

        print(f"[INFO][{trace_id}] Iniciando análise completa com investigação automática")

        # 1. ANÁLISE PRINCIPAL (OpenAI ou local)
        analise_principal = None
        if self.client:
            try:
                analise_principal = self._analisar_com_openai(descricao, conselho, categoria, trace_id)
            except Exception as exc:
                print(f"[WARN][{trace_id}] Falha OpenAI: {exc}. Usando fallback.")

        if not analise_principal:
            analise_principal = self._analisar_local(descricao, conselho, categoria, trace_id)

        # 2. DETECÇÃO AUTOMÁTICA DE NOMES E PROFISSIONAIS
        print(f"[INFO][{trace_id}] Detectando nomes no texto da denúncia...")
        deteccao_nomes = self.detector_nomes.detectar_nomes_e_registros(descricao, conselho)
        
        # 3. INVESTIGAÇÃO AUTOMÁTICA DOS PROFISSIONAIS DETECTADOS
        investigacoes_automaticas = []
        if deteccao_nomes.get("recomendacao_investigacao", False):
            print(f"[INFO][{trace_id}] Investigação automática recomendada - executando...")
            
            for nome_info in deteccao_nomes.get("nomes_detectados", []):
                nome = nome_info["nome_detectado"]
                print(f"[INFO][{trace_id}] Investigando automaticamente: {nome}")
                
                try:
                    # Tentar determinar conselho baseado no registro associado ou contexto
                    conselho_investigacao = conselho
                    registro_investigacao = None
                    
                    if nome_info.get("registro_associado"):
                        conselho_investigacao = nome_info["registro_associado"]["conselho"]
                        registro_investigacao = nome_info["registro_associado"]["numero"]
                    
                    # Realizar investigação completa
                    investigacao_resultado = self.investigador.investigar_completo(
                        nome=nome,
                        registro_profissional=registro_investigacao,
                        conselho=conselho_investigacao,
                        informacoes_adicionais={"fonte": "deteccao_automatica", "trace_id": trace_id}
                    )
                    
                    investigacoes_automaticas.append({
                        "nome_investigado": nome,
                        "confiabilidade_deteccao": nome_info["confiabilidade"],
                        "resultado_investigacao": investigacao_resultado,
                        "timestamp_investigacao": datetime.now().isoformat()
                    })
                    
                    print(f"[SUCCESS][{trace_id}] Investigação concluída para {nome}")
                    
                except Exception as e:
                    print(f"[ERROR][{trace_id}] Erro na investigação de {nome}: {e}")
                    investigacoes_automaticas.append({
                        "nome_investigado": nome,
                        "confiabilidade_deteccao": nome_info["confiabilidade"],
                        "erro_investigacao": str(e),
                        "timestamp_investigacao": datetime.now().isoformat()
                    })

        # 4. CONSOLIDAR RESULTADOS
        analise_principal["investigacao_automatica"] = {
            "deteccao_nomes": deteccao_nomes,
            "total_investigacoes": len(investigacoes_automaticas),
            "investigacoes_realizadas": investigacoes_automaticas,
            "relatorio_deteccao": self.detector_nomes.gerar_relatorio_deteccao(deteccao_nomes)
        }
        
        # 5. ATUALIZAR RECOMENDAÇÕES COM BASE NA INVESTIGAÇÃO
        if investigacoes_automaticas:
            if "recomendacoes" not in analise_principal:
                analise_principal["recomendacoes"] = []
            
            analise_principal["recomendacoes"].append("✅ INVESTIGAÇÃO AUTOMÁTICA REALIZADA - Consultar seção de investigação para detalhes dos profissionais identificados")
            
            # Atualizar gravidade se encontrou registros suspensos/irregulares
            for inv in investigacoes_automaticas:
                resultado_inv = inv.get("resultado_investigacao", {})
                registros = resultado_inv.get("registros_oficiais", {})
                
                if registros.get("registro_encontrado"):
                    dados_prof = registros.get("dados_profissional", {})
                    situacao = dados_prof.get("situacao_registro", "").lower()
                    
                    if "suspenso" in situacao or "cancelado" in situacao or "inativo" in situacao:
                        analise_principal["classificacao_risco"]["nivel"] = "ALTO"
                        analise_principal["classificacao_risco"]["pontuacao"] = min(100, analise_principal["classificacao_risco"].get("pontuacao", 50) + 30)
                        analise_principal["recomendacoes"].append(f"⚠️ ALERTA: Profissional {inv['nome_investigado']} com registro {situacao.upper()}")

        print(f"[SUCCESS][{trace_id}] Análise completa com investigação finalizada")
        return analise_principal

    def _analisar_com_openai(self, descricao: str, conselho: str, categoria: str, trace_id: str) -> Dict[str, Any]:
        """Análise usando OpenAI."""
        print(f"[INFO][{trace_id}] Analisando com OpenAI...")
        
        contexto_legislativo = self._obter_contexto_legislativo(conselho, categoria)
        
        prompt = f"""Você é um assistente especializado em análise de denúncias contra profissionais regulamentados.

{contexto_legislativo}

DENÚNCIA:
{descricao}

CONSELHO: {conselho}
CATEGORIA: {categoria}

Analise a denúncia e retorne APENAS um JSON no seguinte formato:
{{
    "gravidade": "baixa|media|alta|critica",
    "score_confianca": 0-100,
    "elementos_presentes": ["lista de elementos identificados"],
    "elementos_faltantes": ["lista de elementos que faltam"],
    "artigos_aplicaveis": ["lista de artigos legais aplicáveis"],
    "recomendacoes": ["lista de recomendações"],
    "resumo": "resumo da análise em 2-3 linhas"
}}"""

        start_time = perf_counter()
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um especialista em análise de denúncias profissionais."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        elapsed = perf_counter() - start_time
        resposta_texto = response.choices[0].message.content.strip()
        
        # Extrair JSON
        try:
            inicio = resposta_texto.find('{')
            fim = resposta_texto.rfind('}') + 1
            if inicio != -1 and fim > inicio:
                json_str = resposta_texto[inicio:fim]
                analise = json.loads(json_str)
            else:
                raise ValueError("JSON não encontrado")
        except Exception as e:
            print(f"[WARN][{trace_id}] Erro ao parsear JSON: {e}")
            return self._analisar_local(descricao, conselho, categoria, trace_id)
        
        resultado = {
            "versao": self.versao,
            "analise_basica": {
                "resumo": analise.get("resumo", "Análise concluída"),
                "palavras_chave": analise.get("elementos_presentes", []),
                "sentimento": "neutro"
            },
            "analise_juridica": {
                "tipificacao": f"Análise baseada em {conselho} - {categoria}",
                "gravidade": analise.get("gravidade", "media"),
                "artigos_violados": analise.get("artigos_aplicaveis", []),
                "fundamentacao": analise.get("resumo", "Análise automatizada com IA"),
                "legislacao_especifica": self._citar_legislacao_especifica(conselho, categoria)
            },
            "classificacao_risco": {
                "nivel": self._mapear_gravidade_para_nivel(analise.get("gravidade", "media")),
                "pontuacao": analise.get("score_confianca", 50),
                "cor": self._obter_cor_risco(analise.get("gravidade", "media")),
                "acao_recomendada": "Análise detalhada recomendada",
                "fatores_risco": analise.get("elementos_faltantes", [])
            },
            "recomendacoes": analise.get("recomendacoes", []),
            "precedentes": [],
            "timestamp_analise": datetime.now().isoformat(),
            "tempo_analise_ms": int(elapsed * 1000),
            "fonte": "OpenAI"
        }
        
        print(f"[INFO][{trace_id}] Análise OpenAI concluída em {elapsed:.2f}s")
        return resultado

    def _mapear_gravidade_para_nivel(self, gravidade: str) -> str:
        """Mapeia gravidade para nível de risco."""
        mapeamento = {
            "baixa": "BAIXO",
            "media": "MEDIO", 
            "alta": "ALTO",
            "critica": "CRITICO"
        }
        return mapeamento.get(gravidade.lower(), "MEDIO")

    def _obter_cor_risco(self, gravidade: str) -> str:
        """Obtém cor do risco baseada na gravidade."""
        cores = {
            "baixa": "#10b981",
            "media": "#ffc107",
            "alta": "#ef4444",
            "critica": "#dc2626"
        }
        return cores.get(gravidade.lower(), "#ffc107")

    def _analisar_local(self, descricao: str, conselho: str, categoria: str, trace_id: str) -> Dict[str, Any]:
        """Análise local quando OpenAI não está disponível."""
        print(f"[INFO][{trace_id}] Analisando localmente...")
        
        start_time = perf_counter()
        
        # Usar o analisador de texto local
        analise_texto = self.analisador.analisar_texto(descricao)
        
        # Calcular gravidade baseada em palavras-chave
        palavras_graves = ["morte", "sequela", "grave", "irreversível", "permanente"]
        palavras_medias = ["dano", "prejuízo", "lesão", "perda"]
        
        texto_lower = descricao.lower()
        tem_graves = any(p in texto_lower for p in palavras_graves)
        tem_medias = any(p in texto_lower for p in palavras_medias)
        
        if tem_graves:
            gravidade = "alta"
            score = 75
        elif tem_medias:
            gravidade = "media"
            score = 60
        else:
            gravidade = "baixa"
            score = 40
        
        # Elementos presentes/faltantes
        elementos_presentes = []
        elementos_faltantes = []
        
        if any(p in texto_lower for p in ["dr.", "dra.", "profissional", "médico"]):
            elementos_presentes.append("Identificação do profissional")
        else:
            elementos_faltantes.append("Identificação do profissional")
        
        if any(p in texto_lower for p in ["dia", "data", "em", "durante"]):
            elementos_presentes.append("Data/período dos fatos")
        else:
            elementos_faltantes.append("Data/período dos fatos")
        
        if any(p in texto_lower for p in ["hospital", "consultório", "clínica", "local"]):
            elementos_presentes.append("Local dos fatos")
        else:
            elementos_faltantes.append("Local dos fatos")
        
        elapsed = perf_counter() - start_time
        
        resultado = {
            "versao": self.versao,
            "analise_basica": {
                "resumo": f"Denúncia classificada como {gravidade} gravidade. {len(elementos_presentes)} elementos identificados.",
                "palavras_chave": elementos_presentes,
                "sentimento": "neutro"
            },
            "analise_juridica": {
                "tipificacao": f"Análise local baseada em {conselho} - {categoria}",
                "gravidade": gravidade,
                "artigos_violados": ["Análise detalhada requer consulta legislativa"],
                "fundamentacao": "Análise automatizada local por indisponibilidade da IA",
                "legislacao_especifica": self._citar_legislacao_especifica(conselho, categoria)
            },
            "classificacao_risco": {
                "nivel": self._mapear_gravidade_para_nivel(gravidade),
                "pontuacao": score,
                "cor": self._obter_cor_risco(gravidade),
                "acao_recomendada": "Análise detalhada recomendada",
                "fatores_risco": elementos_faltantes
            },
            "recomendacoes": [
                "Complementar informações faltantes",
                "Anexar documentos comprobatórios se disponível"
            ],
            "precedentes": [],
            "timestamp_analise": datetime.now().isoformat(),
            "tempo_analise_ms": int(elapsed * 1000),
            "fonte": "Local"
        }
        
        print(f"[INFO][{trace_id}] Análise local concluída em {elapsed:.2f}s")
        return resultado


# Teste rápido
if __name__ == "__main__":
    print("=== Teste do Motor de IA ===\n")
    
    engine = IAEngineOpenAIPadrao()
    
    teste_data = {
        "descricao": "O médico não me atendeu direito no hospital e fiquei com sequelas.",
        "conselho": "CRM",
        "categoria": "Negligência"
    }
    
    print("Testando análise...")
    resultado = engine.analisar_denuncia_completa(teste_data, "TEST-001")
    
    if resultado:
        print(f"\n✅ Análise concluída!")
        print(f"Fonte: {resultado['fonte']}")
        print(f"Gravidade: {resultado['gravidade']}")
        print(f"Score: {resultado['score_confianca']}/100")
        print(f"Tempo: {resultado['tempo_analise_ms']}ms")
    else:
        print("\n❌ Falha na análise")
    
    print("\n=== Teste concluído ===")


#!/usr/bin/env python3
"""
Investigador Digital para Órgãos Públicos - EviChain
Sistema de investigação digital para coleta de evidências em denúncias profissionais
DESTINADO EXCLUSIVAMENTE PARA USO DE ÓRGÃOS PÚBLICOS COM COMPETÊNCIA INVESTIGATIVA
"""

import requests
import json
import re
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
from urllib.parse import quote
import base64
from consultor_registros import ConsultorRegistrosProfissionais

class InvestigadorDigital:
    """
    Sistema de investigação digital para órgãos públicos
    Coleta informações públicas e de redes sociais para investigação de denúncias
    """
    
    def __init__(self):
        self.versao = "EviChain Investigador v1.0"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.sessao = requests.Session()
        self.sessao.headers.update(self.headers)
        
        # Inicializar consultor de registros profissionais
        self.consultor_registros = ConsultorRegistrosProfissionais()
        
        # URLs de APIs e endpoints para investigação
        self.apis = {
            'google_search': 'https://www.googleapis.com/customsearch/v1',
            'facebook_graph': 'https://graph.facebook.com/v18.0',
            'linkedin_api': 'https://api.linkedin.com/v2',
            'twitter_api': 'https://api.twitter.com/2',
            'instagram_basic': 'https://graph.instagram.com'
        }
        
        # Configurar APIs se as chaves estiverem disponíveis
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_cx = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.facebook_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.linkedin_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        self.twitter_bearer = os.getenv('TWITTER_BEARER_TOKEN')
        
        print(f"[INFO] {self.versao} inicializado")
        print("[WARN] Este sistema deve ser usado apenas por órgãos públicos com competência investigativa")
    
    def investigar_completo(self, nome: str, registro_profissional: str = None, 
                          conselho: str = None, informacoes_adicionais: Dict = None) -> Dict[str, Any]:
        """
        Realiza investigação completa de um profissional
        
        Args:
            nome: Nome completo do profissional
            registro_profissional: Número de registro no conselho
            conselho: Tipo de conselho (CRM, OAB, CREA, etc.)
            informacoes_adicionais: Informações extras como cidade, especialidade, etc.
        
        Returns:
            Dict com todas as informações coletadas
        """
        print(f"[INFO] Iniciando investigação completa de: {nome}")
        
        resultado_investigacao = {
            "dados_basicos": {
                "nome": nome,
                "registro": registro_profissional,
                "conselho": conselho,
                "timestamp_investigacao": datetime.now().isoformat(),
                "investigador": "EviChain Digital"
            },
            "registros_oficiais": {},
            "redes_sociais": {},
            "busca_geral": {},
            "historico_sancoes": {},
            "informacoes_profissionais": {},
            "alertas_e_bandeiras": [],
            "resumo_investigacao": {}
        }
        
        try:
            # 1. Verificar registros oficiais nos conselhos
            print("[INFO] Verificando registros oficiais...")
            resultado_investigacao["registros_oficiais"] = self._verificar_registros_oficiais(
                nome, registro_profissional, conselho
            )
            
            # 2. Buscar em redes sociais
            print("[INFO] Investigando redes sociais...")
            resultado_investigacao["redes_sociais"] = self._investigar_redes_sociais(nome)
            
            # 3. Busca geral na internet
            print("[INFO] Realizando busca geral...")
            resultado_investigacao["busca_geral"] = self._busca_geral_internet(nome, registro_profissional)
            
            # 4. Verificar histórico de sanções
            print("[INFO] Verificando histórico de sanções...")
            resultado_investigacao["historico_sancoes"] = self._verificar_historico_sancoes(
                nome, registro_profissional, conselho
            )
            
            # 5. Informações profissionais
            print("[INFO] Coletando informações profissionais...")
            resultado_investigacao["informacoes_profissionais"] = self._coletar_info_profissionais(nome, conselho)
            
            # 6. Análise de alertas
            print("[INFO] Analisando alertas...")
            resultado_investigacao["alertas_e_bandeiras"] = self._analisar_alertas(resultado_investigacao)
            
            # 7. Resumo da investigação
            resultado_investigacao["resumo_investigacao"] = self._gerar_resumo_investigacao(resultado_investigacao)
            
            print(f"[SUCCESS] Investigação concluída para {nome}")
            
        except Exception as e:
            print(f"[ERROR] Erro durante investigação: {e}")
            resultado_investigacao["erro"] = str(e)
        
        return resultado_investigacao
    
    def _verificar_registros_oficiais(self, nome: str, registro: str, conselho: str) -> Dict[str, Any]:
        """Verifica registros oficiais nos conselhos profissionais usando consultor especializado"""
        print(f"[INFO] Consultando registros oficiais para {nome} no {conselho}")
        
        try:
            # Usar o consultor especializado
            resultado_consulta = self.consultor_registros.consultar_registro_completo(
                nome=nome,
                registro=registro,
                conselho=conselho
            )
            
            # Extrair informações de formação se encontrou registro
            if resultado_consulta.get("registro_encontrado") and resultado_consulta.get("dados_profissional"):
                formacao_info = self.consultor_registros.extrair_formacao_e_especialidades(
                    resultado_consulta["dados_profissional"],
                    conselho
                )
                resultado_consulta["formacao_detalhada"] = formacao_info
            
            # Gerar relatório
            relatorio_texto = self.consultor_registros.gerar_relatorio_registro(resultado_consulta)
            resultado_consulta["relatorio_consulta"] = relatorio_texto
            
            return resultado_consulta
            
        except Exception as e:
            print(f"[ERROR] Erro na consulta de registros: {e}")
            
            # Fallback para método anterior
            registros = {
                "status_verificacao": "erro_na_consulta",
                "encontrado": False,
                "erro": str(e),
                "detalhes": {},
                "fontes_consultadas": []
            }
            
            # URLs dos principais conselhos para consulta manual
            urls_conselhos = {
                "CRM": "https://portal.cfm.org.br/busca-medicos/",
                "OAB": "https://www.oab.org.br/servicos/consulta-de-advogado",
                "CREA": "https://www.confea.org.br/sistemas/busca-por-profissional",
                "CRP": "https://www.cfp.org.br/servicos/consulta-psicologos/",
                "CRO": "https://website.cfo.org.br/servicos/consulta-de-profissionais/",
                "CREF": "https://www.confef.org.br/confef/registrados/"
            }
            
            if conselho and conselho.upper() in urls_conselhos:
                url_consulta = urls_conselhos[conselho.upper()]
                registros["fontes_consultadas"].append(url_consulta)
                registros["detalhes"] = {
                    "url_consultada": url_consulta,
                    "metodo": "consulta_manual_necessaria",
                    "observacao": f"Erro na consulta automatizada. Verificar manualmente em {url_consulta}"
                }
                
                if registro:
                    registros["detalhes"]["numero_registro"] = registro
            
            return registros
    
    def _investigar_redes_sociais(self, nome: str) -> Dict[str, Any]:
        """Investiga presença em redes sociais"""
        redes_sociais = {
            "facebook": self._buscar_facebook(nome),
            "instagram": self._buscar_instagram(nome),
            "linkedin": self._buscar_linkedin(nome),
            "twitter": self._buscar_twitter(nome),
            "youtube": self._buscar_youtube(nome),
            "tiktok": self._buscar_tiktok(nome),
            "outras_redes": self._buscar_outras_redes(nome)
        }
        
        return redes_sociais
    
    def _buscar_facebook(self, nome: str) -> Dict[str, Any]:
        """Busca perfis no Facebook"""
        resultado = {
            "plataforma": "Facebook",
            "perfis_encontrados": [],
            "status": "pesquisado",
            "metodo": "busca_publica"
        }
        
        try:
            # Busca usando Graph API se disponível
            if self.facebook_token:
                url = f"{self.apis['facebook_graph']}/search"
                params = {
                    'q': nome,
                    'type': 'user',
                    'access_token': self.facebook_token,
                    'fields': 'id,name,picture,link'
                }
                
                response = self.sessao.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data:
                        for perfil in data['data']:
                            resultado["perfis_encontrados"].append({
                                "id": perfil.get('id'),
                                "nome": perfil.get('name'),
                                "link": perfil.get('link'),
                                "foto": perfil.get('picture', {}).get('data', {}).get('url')
                            })
            else:
                # Busca alternativa por scraping (simulada)
                resultado["perfis_encontrados"].append({
                    "metodo": "busca_manual_necessaria",
                    "observacao": f"Buscar manualmente por '{nome}' no Facebook",
                    "url_busca": f"https://www.facebook.com/search/people/?q={quote(nome)}"
                })
                
        except Exception as e:
            resultado["erro"] = str(e)
        
        return resultado
    
    def _buscar_instagram(self, nome: str) -> Dict[str, Any]:
        """Busca perfis no Instagram"""
        resultado = {
            "plataforma": "Instagram",
            "perfis_encontrados": [],
            "status": "pesquisado"
        }
        
        try:
            # Busca por username comum baseado no nome
            nome_limpo = re.sub(r'[^a-zA-Z0-9]', '', nome.lower())
            possiveis_usernames = [
                nome_limpo,
                nome_limpo.replace(' ', ''),
                f"dr{nome_limpo}",
                f"dra{nome_limpo}",
                f"{nome_limpo}oficial"
            ]
            
            for username in possiveis_usernames:
                url_perfil = f"https://www.instagram.com/{username}/"
                try:
                    response = self.sessao.head(url_perfil, timeout=5)
                    if response.status_code == 200:
                        resultado["perfis_encontrados"].append({
                            "username": username,
                            "url": url_perfil,
                            "status": "perfil_existe",
                            "verificacao": "automatica"
                        })
                except:
                    continue
            
            # Adicionar busca manual
            resultado["busca_manual"] = f"https://www.instagram.com/explore/search/keyword/?q={quote(nome)}"
            
        except Exception as e:
            resultado["erro"] = str(e)
        
        return resultado
    
    def _buscar_linkedin(self, nome: str) -> Dict[str, Any]:
        """Busca perfis no LinkedIn"""
        resultado = {
            "plataforma": "LinkedIn",
            "perfis_encontrados": [],
            "status": "pesquisado"
        }
        
        try:
            if self.linkedin_token:
                # Usar API oficial se disponível
                url = f"{self.apis['linkedin_api']}/people-search"
                headers = {'Authorization': f'Bearer {self.linkedin_token}'}
                params = {'keywords': nome}
                
                response = self.sessao.get(url, headers=headers, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Processar resultados da API
                    for pessoa in data.get('elements', []):
                        resultado["perfis_encontrados"].append({
                            "nome": pessoa.get('localizedFirstName', '') + ' ' + pessoa.get('localizedLastName', ''),
                            "headline": pessoa.get('localizedHeadline'),
                            "id": pessoa.get('id')
                        })
            else:
                # Busca alternativa
                resultado["busca_manual"] = f"https://www.linkedin.com/search/results/people/?keywords={quote(nome)}"
                resultado["observacao"] = "Busca manual necessária no LinkedIn"
                
        except Exception as e:
            resultado["erro"] = str(e)
        
        return resultado
    
    def _buscar_twitter(self, nome: str) -> Dict[str, Any]:
        """Busca perfis no Twitter/X"""
        resultado = {
            "plataforma": "Twitter/X",
            "perfis_encontrados": [],
            "status": "pesquisado"
        }
        
        try:
            if self.twitter_bearer:
                url = f"{self.apis['twitter_api']}/users/by"
                headers = {'Authorization': f'Bearer {self.twitter_bearer}'}
                params = {
                    'usernames': nome.replace(' ', '').lower(),
                    'user.fields': 'description,public_metrics,verified'
                }
                
                response = self.sessao.get(url, headers=headers, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data:
                        for usuario in data['data']:
                            resultado["perfis_encontrados"].append({
                                "username": usuario.get('username'),
                                "nome": usuario.get('name'),
                                "descricao": usuario.get('description'),
                                "verificado": usuario.get('verified'),
                                "seguidores": usuario.get('public_metrics', {}).get('followers_count')
                            })
            else:
                resultado["busca_manual"] = f"https://twitter.com/search?q={quote(nome)}"
                
        except Exception as e:
            resultado["erro"] = str(e)
        
        return resultado
    
    def _buscar_youtube(self, nome: str) -> Dict[str, Any]:
        """Busca canais no YouTube"""
        return {
            "plataforma": "YouTube",
            "busca_manual": f"https://www.youtube.com/results?search_query={quote(nome)}",
            "status": "busca_manual_necessaria"
        }
    
    def _buscar_tiktok(self, nome: str) -> Dict[str, Any]:
        """Busca perfis no TikTok"""
        return {
            "plataforma": "TikTok",
            "busca_manual": f"https://www.tiktok.com/search/user?q={quote(nome)}",
            "status": "busca_manual_necessaria"
        }
    
    def _buscar_outras_redes(self, nome: str) -> List[Dict[str, str]]:
        """Busca em outras redes sociais"""
        outras_redes = [
            {"nome": "Telegram", "url": f"https://t.me/{nome.replace(' ', '').lower()}"},
            {"nome": "WhatsApp Business", "busca": "Verificar diretórios comerciais"},
            {"nome": "Clubhouse", "busca": "Busca manual necessária"},
            {"nome": "Pinterest", "url": f"https://pinterest.com/search/users/?q={quote(nome)}"},
            {"nome": "Twitch", "url": f"https://www.twitch.tv/{nome.replace(' ', '').lower()}"}
        ]
        
        return outras_redes
    
    def _busca_geral_internet(self, nome: str, registro: str = None) -> Dict[str, Any]:
        """Realiza busca geral na internet"""
        busca_geral = {
            "google_search": {},
            "noticias": {},
            "artigos_academicos": {},
            "diretorios_profissionais": {}
        }
        
        try:
            # Busca no Google se API disponível
            if self.google_api_key and self.google_cx:
                busca_geral["google_search"] = self._buscar_google(nome, registro)
            else:
                busca_geral["google_search"] = {
                    "busca_manual": f"https://www.google.com/search?q={quote(nome + ' ' + (registro or ''))}",
                    "status": "busca_manual_necessaria"
                }
            
            # Busca em sites de notícias
            busca_geral["noticias"] = self._buscar_noticias(nome)
            
            # Busca acadêmica
            busca_geral["artigos_academicos"] = self._buscar_academico(nome)
            
            # Diretórios profissionais
            busca_geral["diretorios_profissionais"] = self._buscar_diretorios(nome)
            
        except Exception as e:
            busca_geral["erro"] = str(e)
        
        return busca_geral
    
    def _buscar_google(self, nome: str, registro: str = None) -> Dict[str, Any]:
        """Busca usando Google Custom Search API"""
        resultado = {"resultados": [], "total": 0}
        
        try:
            query = nome
            if registro:
                query += f" {registro}"
            
            params = {
                'key': self.google_api_key,
                'cx': self.google_cx,
                'q': query,
                'num': 10
            }
            
            response = self.sessao.get(self.apis['google_search'], params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'items' in data:
                    for item in data['items']:
                        resultado["resultados"].append({
                            "titulo": item.get('title'),
                            "link": item.get('link'),
                            "descricao": item.get('snippet'),
                            "fonte": item.get('displayLink')
                        })
                    resultado["total"] = len(data['items'])
                    
        except Exception as e:
            resultado["erro"] = str(e)
        
        return resultado
    
    def _buscar_noticias(self, nome: str) -> Dict[str, Any]:
        """Busca em sites de notícias"""
        return {
            "google_news": f"https://news.google.com/search?q={quote(nome)}",
            "globo": f"https://g1.globo.com/busca/?q={quote(nome)}",
            "folha": f"https://search.folha.uol.com.br/?q={quote(nome)}",
            "estadao": f"https://www.estadao.com.br/buscar/?q={quote(nome)}",
            "status": "busca_manual_necessaria"
        }
    
    def _buscar_academico(self, nome: str) -> Dict[str, Any]:
        """Busca publicações acadêmicas"""
        return {
            "google_scholar": f"https://scholar.google.com/scholar?q={quote(nome)}",
            "pubmed": f"https://pubmed.ncbi.nlm.nih.gov/?term={quote(nome)}",
            "lattes": f"http://lattes.cnpq.br/web/dgp/consulta-simples?termo={quote(nome)}",
            "status": "busca_manual_necessaria"
        }
    
    def _buscar_diretorios(self, nome: str) -> Dict[str, Any]:
        """Busca em diretórios profissionais"""
        return {
            "doctoralia": f"https://www.doctoralia.com.br/buscar?q={quote(nome)}",
            "viva_local": f"https://www.vivalocal.com/brasil/buscar?q={quote(nome)}",
            "paginas_amarelas": f"https://www.paginasamarelas.com.br/buscar/{quote(nome)}",
            "status": "busca_manual_necessaria"
        }
    
    def _verificar_historico_sancoes(self, nome: str, registro: str, conselho: str) -> Dict[str, Any]:
        """Verifica histórico de sanções e processos"""
        historico = {
            "sancoes_conselho": {},
            "processos_judiciais": {},
            "tribunal_contas": {},
            "portal_transparencia": {}
        }
        
        try:
            # Verificar sanções no conselho
            if conselho and registro:
                historico["sancoes_conselho"] = {
                    "conselho": conselho,
                    "registro": registro,
                    "observacao": "Verificação manual necessária no site do conselho",
                    "status": "pendente_verificacao"
                }
            
            # Buscar processos judiciais
            historico["processos_judiciais"] = {
                "tjsp": f"https://esaj.tjsp.jus.br/cjsg/consultaCompleta.do?f=1",
                "tjrj": f"https://www3.tjrj.jus.br/consultaprocessual/",
                "observacao": "Buscar por nome do profissional",
                "status": "busca_manual_necessaria"
            }
            
            # Portal da Transparência
            historico["portal_transparencia"] = {
                "cgu": f"https://portaldatransparencia.gov.br/busca?termo={quote(nome)}",
                "tcu": f"https://contas.tcu.gov.br/pessoaFisica/",
                "status": "busca_manual_necessaria"
            }
            
        except Exception as e:
            historico["erro"] = str(e)
        
        return historico
    
    def _coletar_info_profissionais(self, nome: str, conselho: str) -> Dict[str, Any]:
        """Coleta informações profissionais específicas"""
        info_prof = {
            "especialidades": [],
            "locais_trabalho": [],
            "titulacao": [],
            "associacoes": []
        }
        
        # Buscar em sites específicos por profissão
        if conselho:
            if conselho.upper() == "CRM":
                info_prof["buscar_em"] = [
                    "https://www.doctoralia.com.br",
                    "https://www.consultaremedio.com.br",
                    "https://www.medicoresponde.com.br"
                ]
            elif conselho.upper() == "OAB":
                info_prof["buscar_em"] = [
                    "https://www.advogados.com.br",
                    "https://www.jusbrasil.com.br",
                    "https://www.escritoriosdeadvocacia.com.br"
                ]
            elif conselho.upper() == "CREA":
                info_prof["buscar_em"] = [
                    "https://www.engenhariaefocus.com.br",
                    "https://www.construcaocivil.com.br"
                ]
        
        return info_prof
    
    def _analisar_alertas(self, dados_investigacao: Dict[str, Any]) -> List[Dict[str, str]]:
        """Analisa os dados coletados e gera alertas"""
        alertas = []
        
        # Verificar se há múltiplas identidades suspeitas
        redes_sociais = dados_investigacao.get("redes_sociais", {})
        total_perfis = sum(len(rede.get("perfis_encontrados", [])) for rede in redes_sociais.values() if isinstance(rede, dict))
        
        if total_perfis > 5:
            alertas.append({
                "tipo": "multiplos_perfis",
                "nivel": "medio",
                "descricao": f"Encontrados {total_perfis} perfis em redes sociais - verificar autenticidade"
            })
        
        # Verificar inconsistências
        registros = dados_investigacao.get("registros_oficiais", {})
        if not registros.get("encontrado", False):
            alertas.append({
                "tipo": "registro_nao_encontrado",
                "nivel": "alto",
                "descricao": "Registro profissional não encontrado nos sistemas oficiais"
            })
        
        # Adicionar mais verificações conforme necessário
        if not alertas:
            alertas.append({
                "tipo": "nenhum_alerta",
                "nivel": "baixo",
                "descricao": "Nenhum alerta identificado na investigação"
            })
        
        return alertas
    
    def _gerar_resumo_investigacao(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Gera resumo executivo da investigação"""
        resumo = {
            "timestamp": datetime.now().isoformat(),
            "status_investigacao": "concluida",
            "pontuacao_confiabilidade": 0,
            "principais_achados": [],
            "recomendacoes": [],
            "proximos_passos": []
        }
        
        # Calcular pontuação de confiabilidade
        pontos = 0
        if dados["registros_oficiais"].get("encontrado"):
            pontos += 30
        
        redes_sociais = dados.get("redes_sociais", {})
        perfis_verificados = sum(1 for rede in redes_sociais.values() if isinstance(rede, dict) and rede.get("perfis_encontrados"))
        pontos += min(perfis_verificados * 10, 40)
        
        alertas = dados.get("alertas_e_bandeiras", [])
        alertas_altos = sum(1 for alerta in alertas if alerta.get("nivel") == "alto")
        pontos -= alertas_altos * 20
        
        resumo["pontuacao_confiabilidade"] = max(0, min(100, pontos))
        
        # Principais achados
        if dados["registros_oficiais"].get("encontrado"):
            resumo["principais_achados"].append("Registro profissional confirmado")
        
        if perfis_verificados > 0:
            resumo["principais_achados"].append(f"Presença confirmada em {perfis_verificados} redes sociais")
        
        # Recomendações
        if alertas_altos > 0:
            resumo["recomendacoes"].append("Investigação mais aprofundada recomendada devido aos alertas identificados")
        
        resumo["recomendacoes"].append("Verificar manualmente os links e perfis identificados")
        resumo["recomendacoes"].append("Cruzar informações com outras fontes disponíveis")
        
        # Próximos passos
        resumo["proximos_passos"].append("Documentar evidências coletadas")
        resumo["proximos_passos"].append("Realizar verificações manuais dos links fornecidos")
        resumo["proximos_passos"].append("Considerar contato direto com o profissional para esclarecimentos")
        
        return resumo
    
    def gerar_relatorio_investigacao(self, dados_investigacao: Dict[str, Any], formato: str = "json") -> str:
        """
        Gera relatório formatado da investigação
        
        Args:
            dados_investigacao: Dados coletados na investigação
            formato: Formato do relatório ('json', 'html', 'txt')
        
        Returns:
            Relatório formatado
        """
        if formato == "json":
            return json.dumps(dados_investigacao, indent=2, ensure_ascii=False)
        
        elif formato == "html":
            return self._gerar_relatorio_html(dados_investigacao)
        
        elif formato == "txt":
            return self._gerar_relatorio_txt(dados_investigacao)
        
        else:
            raise ValueError("Formato não suportado. Use: json, html ou txt")
    
    def _gerar_relatorio_html(self, dados: Dict[str, Any]) -> str:
        """Gera relatório em formato HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Relatório de Investigação Digital - EviChain</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 3px solid #007acc; }}
                .alerta-alto {{ color: red; font-weight: bold; }}
                .alerta-medio {{ color: orange; font-weight: bold; }}
                .alerta-baixo {{ color: green; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Relatório de Investigação Digital</h1>
                <p><strong>Investigado:</strong> {dados['dados_basicos']['nome']}</p>
                <p><strong>Data:</strong> {dados['dados_basicos']['timestamp_investigacao']}</p>
                <p><strong>Sistema:</strong> {dados['dados_basicos']['investigador']}</p>
            </div>
        """
        
        # Adicionar seções do relatório
        resumo = dados.get("resumo_investigacao", {})
        html += f"""
            <div class="section">
                <h2>Resumo Executivo</h2>
                <p><strong>Status:</strong> {resumo.get('status_investigacao', 'N/A')}</p>
                <p><strong>Confiabilidade:</strong> {resumo.get('pontuacao_confiabilidade', 0)}/100</p>
            </div>
        """
        
        # Alertas
        alertas = dados.get("alertas_e_bandeiras", [])
        if alertas:
            html += '<div class="section"><h2>Alertas Identificados</h2><ul>'
            for alerta in alertas:
                classe_css = f"alerta-{alerta.get('nivel', 'baixo')}"
                html += f'<li class="{classe_css}">[{alerta.get("nivel", "").upper()}] {alerta.get("descricao", "")}</li>'
            html += '</ul></div>'
        
        html += "</body></html>"
        return html
    
    def _gerar_relatorio_txt(self, dados: Dict[str, Any]) -> str:
        """Gera relatório em formato texto simples"""
        txt = "=" * 60 + "\n"
        txt += "           RELATÓRIO DE INVESTIGAÇÃO DIGITAL\n"
        txt += "                    EviChain System\n"
        txt += "=" * 60 + "\n\n"
        
        # Dados básicos
        txt += f"INVESTIGADO: {dados['dados_basicos']['nome']}\n"
        txt += f"REGISTRO: {dados['dados_basicos'].get('registro', 'N/A')}\n"
        txt += f"CONSELHO: {dados['dados_basicos'].get('conselho', 'N/A')}\n"
        txt += f"DATA: {dados['dados_basicos']['timestamp_investigacao']}\n\n"
        
        # Resumo
        resumo = dados.get("resumo_investigacao", {})
        txt += "-" * 40 + "\n"
        txt += "RESUMO EXECUTIVO\n"
        txt += "-" * 40 + "\n"
        txt += f"Status: {resumo.get('status_investigacao', 'N/A')}\n"
        txt += f"Confiabilidade: {resumo.get('pontuacao_confiabilidade', 0)}/100\n\n"
        
        # Alertas
        alertas = dados.get("alertas_e_bandeiras", [])
        if alertas:
            txt += "-" * 40 + "\n"
            txt += "ALERTAS\n"
            txt += "-" * 40 + "\n"
            for alerta in alertas:
                txt += f"[{alerta.get('nivel', '').upper()}] {alerta.get('descricao', '')}\n"
            txt += "\n"
        
        # Principais achados
        principais_achados = resumo.get("principais_achados", [])
        if principais_achados:
            txt += "-" * 40 + "\n"
            txt += "PRINCIPAIS ACHADOS\n"
            txt += "-" * 40 + "\n"
            for achado in principais_achados:
                txt += f"• {achado}\n"
            txt += "\n"
        
        # Recomendações
        recomendacoes = resumo.get("recomendacoes", [])
        if recomendacoes:
            txt += "-" * 40 + "\n"
            txt += "RECOMENDAÇÕES\n"
            txt += "-" * 40 + "\n"
            for rec in recomendacoes:
                txt += f"• {rec}\n"
            txt += "\n"
        
        txt += "=" * 60 + "\n"
        txt += "Relatório gerado automaticamente pelo sistema EviChain\n"
        txt += "CONFIDENCIAL - Uso restrito a órgãos públicos\n"
        
        return txt


# Exemplo de uso
if __name__ == "__main__":
    investigador = InvestigadorDigital()
    
    # Teste com dados fictícios
    resultado = investigador.investigar_completo(
        nome="João Silva Santos",
        registro_profissional="123456",
        conselho="CRM",
        informacoes_adicionais={"cidade": "São Paulo", "especialidade": "Cardiologia"}
    )
    
    print("=== INVESTIGAÇÃO CONCLUÍDA ===")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
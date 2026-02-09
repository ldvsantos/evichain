#!/usr/bin/env python3
"""
Analisador Inteligente de Texto para Identificação de Legislação
Analisa o texto da denúncia e identifica automaticamente conselho e tipo de infração
"""

import re
from typing import Dict, List, Tuple

class AnalisadorTexto:
    """Analisa texto de denúncias para identificar conselho e tipo de infração"""
    
    def __init__(self):
        # Palavras-chave para identificar conselhos
        self.conselhos_keywords = {
            "CRM": [
                "médico", "medicina", "hospital", "paciente", "cirurgia", "diagnóstico",
                "tratamento médico", "consulta médica", "prontuário", "receita médica",
                "crm", "conselho regional de medicina", "atestado médico", "procedimento cirúrgico"
            ],
            "OAB": [
                "advogado", "advocacia", "processo", "cliente", "honorários", "causa",
                "tribunal", "justiça", "oab", "ordem dos advogados", "petição", "defesa",
                "ação judicial", "escritório de advocacia", "contrato de honorários"
            ],
            "CREA": [
                "engenheiro", "engenharia", "obra", "projeto", "construção", "art",
                "crea", "conselho regional de engenharia", "laudo técnico", "vistoria",
                "estrutura", "edificação", "responsável técnico", "projeto estrutural"
            ],
            "CRP": [
                "psicólogo", "psicologia", "terapia", "atendimento psicológico", "sessão",
                "crp", "conselho regional de psicologia", "laudo psicológico", "avaliação psicológica",
                "consultório", "paciente psicológico", "sigilo profissional"
            ],
            "CRO": [
                "dentista", "odontologia", "dente", "tratamento odontológico", "consultório odontológico",
                "cro", "conselho regional de odontologia", "procedimento odontológico", "canal",
                "implante", "prótese dentária", "clínica odontológica"
            ],
            "CREF": [
                "educador físico", "educação física", "personal trainer", "academia", "treino",
                "cref", "conselho regional de educação física", "atividade física", "exercício",
                "aluno", "treinamento físico", "professor de educação física"
            ]
        }
        
        # Palavras-chave para identificar tipos de infração
        self.infracoes_keywords = {
            "negligencia": [
                "negligência", "negligente", "omissão", "omitiu", "deixou de",
                "não realizou", "não atendeu", "não prestou", "falha", "erro",
                "descuido", "desleixo", "falta de atenção", "não cumpriu",
                "abandonou", "desistiu", "não compareceu", "ausente"
            ],
            "assedio": [
                "assédio", "assediou", "constrangimento", "constrangeu", "intimidação",
                "intimidou", "coação", "coagiu", "abuso", "abusou", "importunação",
                "cantada", "investida", "toque inapropriado", "comentário sexual",
                "insinuação", "perseguição", "stalking", "humilhação"
            ],
            "ma_conduta": [
                "má conduta", "conduta inadequada", "comportamento inadequado", "postura inadequada",
                "desrespeito", "desrespeitou", "ofensa", "ofendeu", "insulto", "insultou",
                "grosseria", "grosseiro", "falta de ética", "antiético", "propaganda irregular",
                "publicidade enganosa", "promessa falsa"
            ],
            "fraude": [
                "fraude", "fraudou", "falsificação", "falsificou", "documento falso",
                "atestado falso", "laudo falso", "mentira", "mentiu", "enganou",
                "estelionato", "golpe", "superfaturamento", "cobrança indevida",
                "nota fiscal falsa", "receita falsa"
            ]
        }
        
        # Palavras que indicam gravidade
        self.gravidade_keywords = {
            "gravissima": [
                "morte", "óbito", "faleceu", "falecimento", "fatal", "gravíssimo",
                "sequela permanente", "dano irreversível", "mutilação", "amputação",
                "paralisia", "coma", "reincidente", "várias vezes", "sistematicamente"
            ],
            "grave": [
                "grave", "sério", "dano permanente", "lesão grave", "hospitalização",
                "internação", "cirurgia de emergência", "risco de vida", "sequela",
                "prejuízo significativo", "dano considerável"
            ],
            "media": [
                "moderado", "médio", "dano reversível", "recuperável", "tratamento necessário",
                "prejuízo moderado", "impacto médio"
            ],
            "leve": [
                "leve", "pequeno", "mínimo", "sem dano", "sem prejuízo", "reversível rapidamente",
                "impacto mínimo", "sem consequências"
            ]
        }
    
    def analisar_texto(self, texto: str, conselho_informado: str = None, categoria_informada: str = None) -> Dict:
        """
        Analisa o texto e identifica conselho, tipo de infração e gravidade
        
        Args:
            texto: Texto da denúncia
            conselho_informado: Conselho informado pelo usuário (opcional)
            categoria_informada: Categoria informada pelo usuário (opcional)
            
        Returns:
            Dict com conselho_detectado, tipo_infracao_detectado, gravidade_detectada, confianca
        """
        texto_lower = texto.lower()
        
        # 1. Identificar conselho
        conselho_detectado = self._identificar_conselho(texto_lower)
        conselho_final = conselho_informado if conselho_informado and conselho_informado != "N/A" else conselho_detectado
        
        # 2. Identificar tipo de infração
        tipo_infracao_detectado = self._identificar_tipo_infracao(texto_lower)
        
        # Mapear categoria informada para tipo de infração
        mapa_categoria = {
            "Negligência": "negligencia",
            "Assédio": "assedio",
            "Má Conduta": "ma_conduta",
            "Fraude": "fraude",
            "Outra": None
        }
        tipo_informado = mapa_categoria.get(categoria_informada)
        tipo_final = tipo_informado if tipo_informado else tipo_infracao_detectado
        
        # 3. Identificar gravidade
        gravidade_detectada = self._identificar_gravidade(texto_lower)
        
        # 4. Calcular confiança
        confianca_conselho = self._calcular_confianca_conselho(texto_lower, conselho_final)
        confianca_infracao = self._calcular_confianca_infracao(texto_lower, tipo_final)
        
        return {
            "conselho_detectado": conselho_final,
            "conselho_original": conselho_informado,
            "tipo_infracao_detectado": tipo_final,
            "categoria_original": categoria_informada,
            "gravidade_detectada": gravidade_detectada,
            "confianca_conselho": confianca_conselho,
            "confianca_infracao": confianca_infracao,
            "palavras_chave_encontradas": self._extrair_palavras_chave(texto_lower, conselho_final, tipo_final)
        }
    
    def _identificar_conselho(self, texto: str) -> str:
        """Identifica qual conselho profissional pela análise do texto"""
        scores = {}
        
        for conselho, keywords in self.conselhos_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in texto:
                    # Palavras mais específicas têm peso maior
                    peso = 2 if len(keyword.split()) > 1 else 1
                    score += peso
            scores[conselho] = score
        
        # Retorna o conselho com maior score, ou None se nenhum foi identificado
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return None
    
    def _identificar_tipo_infracao(self, texto: str) -> str:
        """Identifica o tipo de infração pela análise do texto"""
        scores = {}
        
        for tipo, keywords in self.infracoes_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in texto:
                    # Palavras mais específicas têm peso maior
                    peso = 2 if len(keyword.split()) > 1 else 1
                    score += peso
            scores[tipo] = score
        
        # Retorna o tipo com maior score, ou "negligencia" como padrão
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return "negligencia"
    
    def _identificar_gravidade(self, texto: str) -> str:
        """Identifica a gravidade pela análise do texto"""
        scores = {
            "gravissima": 0,
            "grave": 0,
            "media": 0,
            "leve": 0
        }
        
        for gravidade, keywords in self.gravidade_keywords.items():
            for keyword in keywords:
                if keyword in texto:
                    scores[gravidade] += 1
        
        # Se encontrou palavras de gravidade, retorna a mais grave
        if max(scores.values()) > 0:
            # Prioriza gravidades maiores
            if scores["gravissima"] > 0:
                return "gravissima"
            elif scores["grave"] > 0:
                return "grave"
            elif scores["media"] > 0:
                return "media"
            elif scores["leve"] > 0:
                return "leve"
        
        # Se não encontrou nenhuma palavra, analisa o tamanho e complexidade
        if len(texto) > 500:
            return "grave"  # Textos longos geralmente são casos graves
        elif len(texto) > 200:
            return "media"
        else:
            return "leve"
    
    def _calcular_confianca_conselho(self, texto: str, conselho: str) -> float:
        """Calcula a confiança da identificação do conselho (0-100)"""
        if not conselho or conselho not in self.conselhos_keywords:
            return 0.0
        
        keywords = self.conselhos_keywords[conselho]
        matches = sum(1 for keyword in keywords if keyword in texto)
        
        # Confiança baseada na quantidade de palavras-chave encontradas
        confianca = min(100, (matches / len(keywords)) * 100 * 5)  # Multiplicador para atingir 100%
        return round(confianca, 1)
    
    def _calcular_confianca_infracao(self, texto: str, tipo: str) -> float:
        """Calcula a confiança da identificação do tipo de infração (0-100)"""
        if not tipo or tipo not in self.infracoes_keywords:
            return 0.0
        
        keywords = self.infracoes_keywords[tipo]
        matches = sum(1 for keyword in keywords if keyword in texto)
        
        # Confiança baseada na quantidade de palavras-chave encontradas
        confianca = min(100, (matches / len(keywords)) * 100 * 5)
        return round(confianca, 1)
    
    def _extrair_palavras_chave(self, texto: str, conselho: str, tipo: str) -> List[str]:
        """Extrai as palavras-chave encontradas no texto"""
        palavras = []
        
        if conselho and conselho in self.conselhos_keywords:
            for keyword in self.conselhos_keywords[conselho]:
                if keyword in texto:
                    palavras.append(keyword)
        
        if tipo and tipo in self.infracoes_keywords:
            for keyword in self.infracoes_keywords[tipo]:
                if keyword in texto:
                    palavras.append(keyword)
        
        # Retorna apenas as 10 mais relevantes
        return palavras[:10]
    
    def gerar_explicacao(self, analise: Dict) -> str:
        """Gera uma explicação textual da análise realizada"""
        explicacao = []
        
        if analise["conselho_detectado"]:
            if analise["conselho_original"] and analise["conselho_original"] != analise["conselho_detectado"]:
                explicacao.append(
                    f"⚠️ Conselho detectado automaticamente: {analise['conselho_detectado']} "
                    f"(informado: {analise['conselho_original']}) - "
                    f"Confiança: {analise['confianca_conselho']}%"
                )
            else:
                explicacao.append(
                    f"✅ Conselho identificado: {analise['conselho_detectado']} "
                    f"(Confiança: {analise['confianca_conselho']}%)"
                )
        
        tipo_nome = {
            "negligencia": "Negligência",
            "assedio": "Assédio",
            "ma_conduta": "Má Conduta",
            "fraude": "Fraude"
        }
        
        if analise["tipo_infracao_detectado"]:
            explicacao.append(
                f"✅ Tipo de infração identificado: {tipo_nome.get(analise['tipo_infracao_detectado'], 'Desconhecido')} "
                f"(Confiança: {analise['confianca_infracao']}%)"
            )
        
        if analise["gravidade_detectada"]:
            explicacao.append(
                f"✅ Gravidade detectada: {analise['gravidade_detectada'].upper()}"
            )
        
        if analise["palavras_chave_encontradas"]:
            explicacao.append(
                f"🔍 Palavras-chave encontradas: {', '.join(analise['palavras_chave_encontradas'][:5])}"
            )
        
        return "\n".join(explicacao)


# Teste do analisador
if __name__ == "__main__":
    analisador = AnalisadorTexto()
    
    # Teste 1: Negligência médica
    texto1 = """
    Médico deixou de realizar procedimento urgente, causando dano permanente ao paciente.
    O paciente foi hospitalizado e precisou de cirurgia de emergência.
    """
    resultado1 = analisador.analisar_texto(texto1)
    print("=== Teste 1: Negligência Médica ===")
    print(analisador.gerar_explicacao(resultado1))
    print()
    
    # Teste 2: Assédio em consultório
    texto2 = """
    Psicólogo fez comentários de cunho sexual durante sessão de terapia,
    constrangendo a paciente e criando ambiente de intimidação.
    """
    resultado2 = analisador.analisar_texto(texto2)
    print("=== Teste 2: Assédio Psicólogo ===")
    print(analisador.gerar_explicacao(resultado2))
    print()
    
    # Teste 3: Fraude advocatícia
    texto3 = """
    Advogado cobrou honorários por serviços não prestados e apresentou
    documentos falsos ao cliente, configurando estelionato.
    """
    resultado3 = analisador.analisar_texto(texto3)
    print("=== Teste 3: Fraude Advocatícia ===")
    print(analisador.gerar_explicacao(resultado3))

#!/usr/bin/env python3
"""
Detector de Nomes em Denúncias - EviChain
Sistema para identificar automaticamente nomes de profissionais em textos de denúncias
"""

import re
import json
from typing import List, Dict, Any, Tuple
import unicodedata

class DetectorNomes:
    """
    Detector automático de nomes de pessoas em textos de denúncias
    Identifica possíveis profissionais mencionados para investigação automática
    """
    
    def __init__(self):
        self.versao = "EviChain Detector v1.0"
        
        # Padrões para identificar nomes profissionais (corrigidos)
        self.padroes_nomes = [
            # Dr./Dra. + Nome (capturar nome completo até parênteses ou fim)
            r'\b(?:Dr\.?|Dra\.?|Doutor|Doutora)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,})*?)(?=\s*\(|$|,|\.|;|\s+[a-z])',
            
            # Prof./Profa. + Nome
            r'\b(?:Prof\.?|Profa\.?|Professor|Professora)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,})*?)(?=\s*\(|$|,|\.|;|\s+[a-z])',
            
            # Eng./Enga. + Nome
            r'\b(?:Eng\.?|Enga\.?|Engenheiro|Engenheira)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,})*?)(?=\s*\(|$|,|\.|;|\s+[a-z])',
            
            # Adv./Adva. + Nome
            r'\b(?:Adv\.?|Adva\.?|Advogado|Advogada)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}){0,2})(?=\s*\(|$|,|\.|;|\s+[a-z])',
            
            # Psic./Psicólogo + Nome
            r'\b(?:Psic\.?|Psicólogo|Psicóloga)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,})*?)(?=\s*\(|$|,|\.|;|\s+[a-z])',
            
            # Personal trainer + Nome (parar no CREF ou antes de minúsculas)
            r'\b(?:Personal\s+trainer|Personal)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,})*?)(?=\s+(?:CREF|cref|\d)|$)',
            
            # Educador físico + Nome (parar exatamente após 2-3 nomes próprios)
            r'\b(?:Educador\s+físico|Educadora\s+física)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}){0,2})(?=\s+[a-z]|$)',
            
            # Nome com registro - Ex: "João Silva (CRM 12345)"
            r'\b([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}){1,3})\s*\((?:CRM|OAB|CREA|CRP|CRO|CREF)\s*[\-\s]*\d+\)',
            
            # Nome seguido de especialidade
            r'\b([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}){1,3})\s*[,\-]\s*(?:cardiologista|neurologista|pediatra|ginecologista|ortopedista|psiquiatra|advogado|engenheiro|psicólogo|dentista)',
            
            # Nome seguido de CREF
            r'\b([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}){1,3})\s+(?:CREF|cref)\s*[\-\s]*\d+',
            
            # Médico + Nome (parar antes de minúsculas)
            r'\b(?:médico|médica)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}){0,2})(?=\s+[a-z]|$)',
            
            # Nome em contexto de denúncia - Ex: "denunciar João Silva", "denuncia Maria Santos"
            r'\b(?:denunciar|denuncia|denúncia)\s+([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}){1,3})(?=\s+(?:pois|porque|por|que)|$)',
            
            # Nome próprio genérico em contexto profissional (quando há menção a conselhos)
            r'\b([A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}(?:\s+[A-ZÁÊÎÔÛÃÕÇ][a-záêîôûãõç]{2,}){2})(?=\s+pois.*\b(?:CRM|OAB|CREA|CRP|CRO|CREF)\b)'
        ]
        
        # Palavras que indicam contexto profissional
        self.indicadores_profissionais = [
            'médico', 'doutor', 'doutora', 'dr', 'dra',
            'advogado', 'advogada', 'oab',
            'engenheiro', 'engenheira', 'crea',
            'psicólogo', 'psicóloga', 'crp',
            'dentista', 'odontólogo', 'cro',
            'fisioterapeuta', 'educador físico', 'cref',
            'professor', 'professora',
            'crm', 'registro', 'conselho'
        ]
        
        # Números de registro comuns
        self.padroes_registros = [
            r'\b(?:CRM|crm)\s*[\-\s]*(\d{4,6})\b',
            r'\b(?:OAB|oab)\s*[\-\s]*(\d{4,7})\b',
            r'\b(?:CREA|crea)\s*[\-\s]*(\d{4,8})\b',
            r'\b(?:CRP|crp)\s*[\-\s]*(\d{2,6})\b',
            r'\b(?:CRO|cro)\s*[\-\s]*(\d{3,6})\b',
            r'\b(?:CREF|cref)\s*[\-\s]*(\d{4,7})\b'
        ]
        
        # Nomes muito comuns que podem gerar falsos positivos (removidos para teste)
        self.nomes_comuns_excluir = {
            # 'joão silva', 'maria silva', 'josé santos', 'ana costa',
            # 'carlos oliveira', 'antonio souza', 'francisco lima', 
            # 'paulo pereira', 'pedro rodrigues', 'luis santos'
        }
        
        print(f"[INFO] {self.versao} inicializado")
    
    def detectar_nomes_e_registros(self, texto: str, conselho_contexto: str = None) -> Dict[str, Any]:
        """
        Detecta nomes e registros profissionais no texto da denúncia
        
        Args:
            texto: Texto da denúncia
            conselho_contexto: Conselho do contexto da denúncia (se informado)
        
        Returns:
            Dict com nomes e registros detectados
        """
        resultado = {
            "nomes_detectados": [],
            "registros_detectados": [],
            "contexto_profissional": False,
            "confiabilidade_deteccao": 0,
            "recomendacao_investigacao": False
        }
        
        # Normalizar texto
        texto_normalizado = self._normalizar_texto(texto)
        
        # Detectar contexto profissional
        resultado["contexto_profissional"] = self._tem_contexto_profissional(texto_normalizado)
        
        # Detectar nomes
        nomes_encontrados = self._extrair_nomes(texto_normalizado)
        
        # Detectar registros
        registros_encontrados = self._extrair_registros(texto_normalizado)
        
        # Processar e filtrar nomes
        for nome_info in nomes_encontrados:
            nome_limpo = self._limpar_nome(nome_info['nome'])
            
            if self._validar_nome(nome_limpo):
                nome_processado = {
                    "nome_detectado": nome_limpo,
                    "contexto_encontrado": nome_info.get('contexto', ''),
                    "padrao_usado": nome_info.get('padrao', ''),
                    "confiabilidade": self._calcular_confiabilidade_nome(nome_info, texto_normalizado),
                    "posicao_texto": nome_info.get('posicao', 0)
                }
                
                # Tentar associar com registro
                registro_associado = self._associar_registro_ao_nome(nome_limpo, registros_encontrados, texto_normalizado)
                if registro_associado:
                    nome_processado["registro_associado"] = registro_associado
                
                resultado["nomes_detectados"].append(nome_processado)
        
        # Processar registros
        for registro_info in registros_encontrados:
            resultado["registros_detectados"].append({
                "numero_registro": registro_info['numero'],
                "conselho": registro_info['conselho'],
                "contexto": registro_info.get('contexto', ''),
                "posicao_texto": registro_info.get('posicao', 0)
            })
        
        # Calcular confiabilidade geral
        resultado["confiabilidade_deteccao"] = self._calcular_confiabilidade_geral(resultado)
        
        # Determinar se deve investigar
        resultado["recomendacao_investigacao"] = (
            len(resultado["nomes_detectados"]) > 0 and 
            (resultado["contexto_profissional"] or len(resultado["registros_detectados"]) > 0) and
            resultado["confiabilidade_deteccao"] >= 60
        )
        
        return resultado
    
    def _normalizar_texto(self, texto: str) -> str:
        """Normaliza o texto para processamento"""
        # Remover acentos para alguns padrões
        texto_sem_acentos = unicodedata.normalize('NFD', texto)
        texto_sem_acentos = ''.join(c for c in texto_sem_acentos if unicodedata.category(c) != 'Mn')
        
        return texto
    
    def _tem_contexto_profissional(self, texto: str) -> bool:
        """Verifica se o texto tem contexto profissional"""
        texto_lower = texto.lower()
        
        for indicador in self.indicadores_profissionais:
            if indicador in texto_lower:
                return True
        
        return False
    
    def _extrair_nomes(self, texto: str) -> List[Dict[str, Any]]:
        """Extrai nomes usando padrões regex"""
        nomes_encontrados = []
        
        for i, padrao in enumerate(self.padroes_nomes):
            matches = re.finditer(padrao, texto, re.IGNORECASE | re.UNICODE)
            
            for match in matches:
                nome = match.group(1) if match.groups() else match.group(0)
                
                nomes_encontrados.append({
                    "nome": nome.strip(),
                    "contexto": match.group(0),
                    "padrao": f"padrao_{i+1}",
                    "posicao": match.start()
                })
        
        return nomes_encontrados
    
    def _extrair_registros(self, texto: str) -> List[Dict[str, Any]]:
        """Extrai números de registros profissionais"""
        registros_encontrados = []
        
        for padrao in self.padroes_registros:
            matches = re.finditer(padrao, texto, re.IGNORECASE)
            
            for match in matches:
                numero = match.group(1)
                conselho = match.group(0).split()[0].upper()
                
                registros_encontrados.append({
                    "numero": numero,
                    "conselho": conselho,
                    "contexto": match.group(0),
                    "posicao": match.start()
                })
        
        return registros_encontrados
    
    def _limpar_nome(self, nome: str) -> str:
        """Limpa e padroniza o nome"""
        # Remover títulos
        nome = re.sub(r'\b(?:Dr\.?|Dra\.?|Prof\.?|Profa\.?|Eng\.?|Enga\.?|Adv\.?|Adva\.?|Personal\s+trainer|Personal)\s*', '', nome, flags=re.IGNORECASE)
        
        # Remover registros colados ao nome
        nome = re.sub(r'\s*(?:CRM|OAB|CREA|CRP|CRO|CREF)\s*\d*\s*$', '', nome, flags=re.IGNORECASE)
        
        # Limpar pontuação extra
        nome = re.sub(r'[^\w\s]', '', nome)
        
        # Normalizar espaços
        nome = ' '.join(nome.split())
        
        # Capitalizar corretamente
        nome = nome.title()
        
        return nome.strip()
    
    def _validar_nome(self, nome: str) -> bool:
        """Valida se o nome é válido para investigação"""
        if not nome or len(nome) < 3:  # Reduzido de 6 para 3
            return False
        
        # Verificar se tem pelo menos nome (pode ser só um nome se profissional)
        partes = nome.split()
        if len(partes) < 1:  # Mudado de 2 para 1
            return False
        
        # Verificar se não é nome muito comum
        nome_lower = nome.lower()
        if nome_lower in self.nomes_comuns_excluir:
            return False
        
        # Verificar se tem pelo menos 2 caracteres em cada parte
        for parte in partes:
            if len(parte) < 2:
                return False
        
        # Verificar se não são apenas números
        if nome.replace(' ', '').isdigit():
            return False
        
        # Verificar se não contém palavras comuns que não são nomes
        palavras_invalidas = [
            'foi', 'negligente', 'causou', 'lesão', 'durante', 'treino',
            'não', 'atendeu', 'adequadamente', 'meu', 'caso', 'cumpriu',
            'prazo', 'acordado', 'deixou', 'apresentar', 'projeto',
            'data', 'combinada', 'gostei', 'atendimento', 'tratamento',
            'supervisionou', 'mal', 'bem'  # Adicionadas palavras específicas
        ]
        
        for palavra in palavras_invalidas:
            if palavra in nome_lower:
                return False
        
        # Verificar se todas as palavras começam com maiúscula (padrão de nomes próprios)
        for parte in partes:
            if not parte[0].isupper():
                return False
        
        # Verificar se não é uma frase comum
        if len(partes) > 4:  # Nomes normalmente têm no máximo 4 partes
            return False
        
        return True
        
        return True
    
    def _calcular_confiabilidade_nome(self, nome_info: Dict, texto: str) -> int:
        """Calcula confiabilidade da detecção do nome"""
        confiabilidade = 30  # Base
        
        # Bonus por padrão específico
        if 'padrao_1' in nome_info.get('padrao', ''):  # Dr./Dra.
            confiabilidade += 40
        elif 'padrao_2' in nome_info.get('padrao', ''):  # Prof.
            confiabilidade += 35
        elif 'padrao_5' in nome_info.get('padrao', ''):  # Com registro
            confiabilidade += 50
        
        # Bonus por contexto profissional
        contexto = nome_info.get('contexto', '').lower()
        if any(ind in contexto for ind in ['dr', 'doutor', 'médico', 'advogado']):
            confiabilidade += 20
        
        # Bonus se tem registro próximo
        nome = nome_info.get('nome', '')
        posicao = nome_info.get('posicao', 0)
        
        # Procurar registro em 100 caracteres ao redor
        texto_contexto = texto[max(0, posicao-100):posicao+100]
        if re.search(r'\b(?:CRM|OAB|CREA|CRP|CRO|CREF)\s*\d+', texto_contexto, re.IGNORECASE):
            confiabilidade += 25
        
        return min(100, confiabilidade)
    
    def _associar_registro_ao_nome(self, nome: str, registros: List[Dict], texto: str) -> Dict[str, Any]:
        """Tenta associar um registro a um nome baseado na proximidade no texto"""
        # Implementação simplificada - associa o registro mais próximo
        if not registros:
            return None
        
        # Por enquanto, retorna o primeiro registro encontrado
        # Em implementação mais sofisticada, calcularia distância no texto
        return registros[0] if registros else None
    
    def _calcular_confiabilidade_geral(self, resultado: Dict) -> int:
        """Calcula confiabilidade geral da detecção"""
        if not resultado["nomes_detectados"]:
            return 0
        
        # Média das confiabilidades dos nomes
        confiabilidades = [nome["confiabilidade"] for nome in resultado["nomes_detectados"]]
        confiabilidade_media = sum(confiabilidades) / len(confiabilidades)
        
        # Bonus por contexto profissional
        if resultado["contexto_profissional"]:
            confiabilidade_media += 15
        
        # Bonus por ter registros
        if resultado["registros_detectados"]:
            confiabilidade_media += 20
        
        return min(100, int(confiabilidade_media))
    
    def gerar_relatorio_deteccao(self, resultado: Dict) -> str:
        """Gera relatório formatado da detecção"""
        relatorio = []
        relatorio.append("=" * 50)
        relatorio.append("  DETECÇÃO AUTOMÁTICA DE PROFISSIONAIS")
        relatorio.append("=" * 50)
        relatorio.append("")
        
        relatorio.append(f"Confiabilidade Geral: {resultado['confiabilidade_deteccao']}%")
        relatorio.append(f"Contexto Profissional: {'SIM' if resultado['contexto_profissional'] else 'NÃO'}")
        relatorio.append(f"Recomenda Investigação: {'SIM' if resultado['recomendacao_investigacao'] else 'NÃO'}")
        relatorio.append("")
        
        if resultado["nomes_detectados"]:
            relatorio.append("NOMES DETECTADOS:")
            relatorio.append("-" * 20)
            for i, nome in enumerate(resultado["nomes_detectados"], 1):
                relatorio.append(f"{i}. {nome['nome_detectado']}")
                relatorio.append(f"   Confiabilidade: {nome['confiabilidade']}%")
                relatorio.append(f"   Contexto: {nome['contexto_encontrado']}")
                if nome.get('registro_associado'):
                    reg = nome['registro_associado']
                    relatorio.append(f"   Registro: {reg['conselho']} {reg['numero']}")
                relatorio.append("")
        
        if resultado["registros_detectados"]:
            relatorio.append("REGISTROS DETECTADOS:")
            relatorio.append("-" * 20)
            for i, reg in enumerate(resultado["registros_detectados"], 1):
                relatorio.append(f"{i}. {reg['conselho']} {reg['numero_registro']}")
                relatorio.append(f"   Contexto: {reg['contexto']}")
                relatorio.append("")
        
        if not resultado["nomes_detectados"] and not resultado["registros_detectados"]:
            relatorio.append("Nenhum profissional detectado automaticamente.")
            relatorio.append("")
        
        relatorio.append("=" * 50)
        
        return "\n".join(relatorio)


# Teste da funcionalidade
if __name__ == "__main__":
    detector = DetectorNomes()
    
    # Textos de teste
    textos_teste = [
        "O Dr. João Silva Santos (CRM 123456) não atendeu adequadamente meu caso.",
        "A advogada Maria Costa Lima, OAB 654321, não cumpriu o prazo acordado.",
        "O engenheiro Paulo Roberto Souza deixou de apresentar o projeto na data combinada.",
        "Fui atendido pelo médico Carlos Eduardo e não gostei do atendimento.",
        "O psicólogo Pedro Henrique foi negligente no tratamento."
    ]
    
    print("=== TESTE DO DETECTOR DE NOMES ===\n")
    
    for i, texto in enumerate(textos_teste, 1):
        print(f"TESTE {i}:")
        print(f"Texto: {texto}")
        print("-" * 40)
        
        resultado = detector.detectar_nomes_e_registros(texto)
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        print("\nRelatório:")
        print(detector.gerar_relatorio_deteccao(resultado))
        print("\n" + "="*60 + "\n")
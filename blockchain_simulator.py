#!/usr/bin/env python3
"""
EviChain - Simulador de Blockchain para Validação de Evidências (Versão Corrigida)
Este módulo simula um sistema blockchain simplificado.
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import os

class Block:
    """Representa um bloco na blockchain"""
    
    def __init__(self, index: int, timestamp: float, data: Dict, previous_hash: str):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """
        Calcula o hash SHA-256 do bloco de forma determinística.
        Esta é a correção crítica para evitar erros de validação.
        """
        # Garante que os dados internos (como transações) também sejam ordenados
        block_data_string = json.dumps(self.data, sort_keys=True)

        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": block_data_string,  # Usa a string de dados já ordenada
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int = 4):
        """Simula o processo de mineração (Proof of Work simplificado)"""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

class EviChainBlockchain:
    """Simulador da blockchain EviChain"""
    
    def __init__(self, data_file: str = "blockchain_data.json"):
        self.data_file = data_file
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict] = []
        self.difficulty = 4
        self.load_chain()

    def load_chain(self):
        """Carrega a blockchain de um arquivo JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.chain = [self._create_block_from_dict(block_data) for block_data in data.get('blocks', [])]
                if not self.chain or not self.is_chain_valid():
                    print("⚠️ Blockchain inválida ou corrompida. Criando uma nova.")
                    self._create_genesis_block()
                else:
                    print(f"✅ Blockchain carregada de {self.data_file} com {len(self.chain)} blocos.")
            else:
                self._create_genesis_block()
                print("🌱 Nova blockchain criada com o bloco gênesis.")
        except (json.JSONDecodeError, KeyError, TypeError):
            print("⚠️ Erro ao ler o arquivo da blockchain. Criando uma nova.")
            self._create_genesis_block()

    def _create_block_from_dict(self, data: Dict) -> Block:
        """Cria um objeto Block a partir de um dicionário"""
        block = Block(
            index=data['index'],
            timestamp=data['timestamp'],
            data=json.loads(data['data']) if isinstance(data['data'], str) else data['data'], # Lida com o dado como string
            previous_hash=data['previous_hash']
        )
        block.nonce = data['nonce']
        # Recalcula o hash para garantir que está correto com a lógica atual
        block.hash = block.calculate_hash() 
        return block

    def _create_genesis_block(self):
        """Cria o primeiro bloco (gênesis) e salva"""
        self.chain = [] # Limpa a chain antes de criar
        genesis_data = {
            "type": "genesis",
            "message": "EviChain Genesis Block",
            "version": "1.0.0"
        }
        genesis_block = Block(0, time.time(), genesis_data, "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        self.save_chain()

    def save_chain(self):
        """Salva a blockchain em um arquivo JSON de forma compatível"""
        chain_data_to_save = []
        for block in self.chain:
            block_dict = vars(block).copy()
            # Converte o dicionário de dados para uma string JSON, como no cálculo do hash
            block_dict['data'] = json.dumps(block_dict['data'], sort_keys=True)
            chain_data_to_save.append(block_dict)

        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({"blocks": chain_data_to_save}, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"❌ Erro ao salvar a blockchain: {e}")

    @property
    def last_block(self) -> Block:
        """Retorna o último bloco da chain"""
        return self.chain[-1]

   
    def add_evidence_transaction(self, evidence_data: Dict) -> str:
        """Adiciona uma nova transação de evidência, incluindo a análise da IA."""
        transaction = {
            "id": generate_complaint_id(),
            "type": "evidence_transaction",
            "timestamp": time.time(),
            "evidence_hash": hashlib.sha256(json.dumps(evidence_data.get("file_hashes", [])).encode()).hexdigest(),
            "metadata": {
                "titulo": evidence_data.get("titulo"),
                "descricao": evidence_data.get("descricao"),
                "conselho": evidence_data.get("conselho"),
                "categoria": evidence_data.get("categoria"),
                "anonymous": evidence_data.get("anonymous", False),
                "ouvidoriaAnonima": evidence_data.get("ouvidoriaAnonima", False),
                "assunto": evidence_data.get("assunto"),
                "prioridade": evidence_data.get("prioridade"),
                "finalidade": evidence_data.get("finalidade"),
                "codigosAnteriores": evidence_data.get("codigosAnteriores")
            },
            # CORREÇÃO APLICADA AQUI:
            # Usar a análise de IA recebida em vez de um dicionário vazio.
            "ia_analysis": evidence_data.get("ia_analysis", {})
        }
        self.pending_transactions.append(transaction)
        return transaction['id']













    def mine_pending_transactions(self) -> Optional[Block]:
        """Minera um novo bloco com todas as transações pendentes"""
        if not self.pending_transactions:
            return None

        new_block = Block(
            index=self.last_block.index + 1,
            timestamp=time.time(),
            data={"transactions": self.pending_transactions},
            previous_hash=self.last_block.hash
        )
        
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        self.pending_transactions = []
        self.save_chain()
        return new_block

    def is_chain_valid(self) -> bool:
        """Verifica a integridade da blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            if current_block.hash != current_block.calculate_hash():
                print(f"❌ Corrupção! Hash calculado do bloco {current_block.index} é inválido.")
                return False
            
            if current_block.previous_hash != previous_block.hash:
                print(f"❌ Corrupção! Elo quebrado entre bloco {previous_block.index} e {current_block.index}.")
                return False
        
        return True

    def get_chain_info(self) -> Dict:
        """Retorna informações gerais sobre a blockchain"""
        return {
            "total_blocks": len(self.chain),
            "last_block_hash": self.last_block.hash,
            "difficulty": self.difficulty,
            "is_valid": self.is_chain_valid()
        }

    def get_all_complaints(self) -> List[Dict]:
        """Extrai todas as denúncias da blockchain, pulando o bloco gênesis."""
        all_complaints = []
        for block in self.chain[1:]:
            transactions = block.data.get("transactions", [])
            for tx in transactions:
                metadata = tx.get("metadata", {})
                details = {
                    "id": tx.get("id"),
                    "titulo": metadata.get("titulo"),
                    "descricao": metadata.get("descricao"),
                    "conselho": metadata.get("conselho"),
                    "categoria": metadata.get("categoria"),
                    "anonymous": metadata.get("anonymous", False),
                    "ouvidoriaAnonima": metadata.get("ouvidoriaAnonima", False),
                    "assunto": metadata.get("assunto"),
                    "prioridade": metadata.get("prioridade"),
                    "finalidade": metadata.get("finalidade"),
                    "codigosAnteriores": metadata.get("codigosAnteriores"),
                    "timestamp": tx.get("timestamp", 0),
                    "data": datetime.fromtimestamp(tx.get("timestamp", 0)).isoformat(),
                    "ia_analysis": tx.get("ia_analysis", {})
                }
                all_complaints.append(details)
        return all_complaints

# Funções Auxiliares
def generate_complaint_id() -> str:
    """Gera um ID único para a denúncia (EVC-ANO-TIMESTAMP)"""
    now = datetime.now()
    return f"EVC-{now.year}-{int(now.timestamp() % 1000000)}"

# Bloco de demonstração
if __name__ == "__main__":
    print("Executando demonstração do simulador de blockchain...")
    evichain = EviChainBlockchain(data_file="demo_blockchain.json")
    print("\nAdicionando nova denúncia...")
    evichain.add_evidence_transaction({
        "titulo": "Teste de Demonstração", "descricao": "Detalhes do teste.",
        "conselho": "N/A", "categoria": "Teste", "file_hashes": ["hash1", "hash2"]
    })
    print("Minerando novo bloco...")
    evichain.mine_pending_transactions()
    print("\nInformações da Chain:")
    print(json.dumps(evichain.get_chain_info(), indent=2))
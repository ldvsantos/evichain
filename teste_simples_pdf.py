import requests
import json

# Teste simples da API
url = "http://localhost:5000/api/generate_pdf"
data = {
    "complaint_id": "TEST-001",
    "titulo": "Teste PDF",
    "assunto": "Teste",
    "descricao": "Teste de PDF",
    "ia_analysis": {
        "analise_basica": {"resumo": "Teste"},
        "investigacao_automatica": {
            "relatorio_deteccao": "Teste de detecção",
            "deteccao_nomes": {"nomes_detectados": []},
            "investigacoes_realizadas": []
        }
    }
}

try:
    print("Enviando requisição...")
    response = requests.post(url, json=data, timeout=10)
    
    if response.status_code == 200:
        with open('teste_simples.pdf', 'wb') as f:
            f.write(response.content)
        print("✅ PDF criado: teste_simples.pdf")
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"❌ Erro de conexão: {e}")
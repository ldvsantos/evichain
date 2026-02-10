// =====================================================================
// EviChain - script.js (Versão Final Definitiva)
// =====================================================================

// Detecta o base URL da API
function getScriptApiBase() {
    if (window.location.hostname.includes('github.io')) return null;
    return window.location.origin;
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('EviChain - Página principal carregada.');

    const complaintForm = document.getElementById('complaintForm');
    
    if (!complaintForm) {
        console.error('ERRO CRÍTICO: Formulário com id="complaintForm" não foi encontrado no HTML.');
        return;
    }

    complaintForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const submitButton = complaintForm.querySelector('button[type="submit"]');
        const formMessage = document.getElementById('formMessage');

        if (!submitButton || !formMessage) {
            console.error('ERRO: Botão de envio (type="submit") ou área de mensagem (#formMessage) não encontrados.');
            return;
        }

        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
        formMessage.textContent = '';
        formMessage.className = 'form-message';

        const formData = {
            titulo: document.getElementById('titulo').value,
            nomeDenunciado: document.getElementById('nomeDenunciado').value,
            descricao: document.getElementById('descricao').value,
            conselho: document.getElementById('conselho').value,
            categoria: document.getElementById('categoria').value,
            anonymous: document.getElementById('anonymous').checked,
            ouvidoriaAnonima: document.getElementById('ouvidoriaAnonima').checked,
            assunto: document.getElementById('assunto').value,
            prioridade: document.getElementById('prioridade').value,
            finalidade: document.getElementById('finalidade').value,
            codigosAnteriores: document.getElementById('codigosAnteriores').value
        };

        if (!formData.descricao || formData.descricao.trim().length < 10) {
            showMessage(formMessage, 'error', 'O campo "Descrição Detalhada" é obrigatório (mínimo 10 caracteres).');
            resetButton(submitButton);
            return;
        }

        if (!formData.nomeDenunciado || formData.nomeDenunciado.trim().length < 2) {
            showMessage(formMessage, 'error', 'O campo "Nome do Profissional Denunciado" é obrigatório (mínimo 2 caracteres).');
            resetButton(submitButton);
            return;
        }

        if (!formData.assunto || formData.assunto.trim().length < 3) {
            showMessage(formMessage, 'error', 'O campo "Assunto" é obrigatório (mínimo 3 caracteres).');
            resetButton(submitButton);
            return;
        }

        if (!formData.finalidade) {
            showMessage(formMessage, 'error', 'O campo "Finalidade" é obrigatório.');
            resetButton(submitButton);
            return;
        }

        try {
            const apiBase = getScriptApiBase();
            if (!apiBase) {
                showMessage(formMessage, 'error', 'Envio de denúncias disponível apenas com o servidor ativo (EC2). Este ambiente é apenas demonstração.');
                resetButton(submitButton);
                return;
            }
            const response = await fetch(apiBase + '/api/submit-complaint', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });

            const result = await response.json();

            if (response.ok && result.success) {
                showMessage(formMessage, 'success', `Denúncia enviada com sucesso! ID: ${result.complaint_id}`);
                complaintForm.reset();
            } else {
                throw new Error(result.error || 'Ocorreu um erro desconhecido.');
            }

        } catch (error) {
            console.error('Erro ao enviar denúncia:', error);
            showMessage(formMessage, 'error', `Falha ao enviar. Verifique a conexão. Detalhe: ${error.message}`);
        } finally {
            resetButton(submitButton);
        }
    });
});

function showMessage(element, type, text) {
    if (element) {
        element.textContent = text;
        element.className = `form-message ${type}`;
    }
}

function resetButton(button) {
    if (button) {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-paper-plane"></i> Enviar Denúncia com Segurança';
    }
}

// =====================================================================
// Assistente de IA para Melhorar Denúncias
// =====================================================================

// Contador de caracteres
const descricaoTextarea = document.getElementById('descricao');
const contadorCaracteres = document.getElementById('contadorCaracteres');

if (descricaoTextarea && contadorCaracteres) {
    descricaoTextarea.addEventListener('input', function() {
        const count = this.value.length;
        contadorCaracteres.textContent = `${count} caracteres`;
        
        // Mudar cor baseado no tamanho
        if (count < 100) {
            contadorCaracteres.style.color = '#ef4444'; // Vermelho
        } else if (count < 200) {
            contadorCaracteres.style.color = '#ffc107'; // Amarelo
        } else {
            contadorCaracteres.style.color = '#10b981'; // Verde
        }
    });
}

// Botão de analisar texto
const btnAnalisarTexto = document.getElementById('btnAnalisarTexto');
const areaSugestoes = document.getElementById('areaSugestoes');
const conteudoSugestoes = document.getElementById('conteudoSugestoes');
const btnFecharSugestoes = document.getElementById('btnFecharSugestoes');

if (btnAnalisarTexto) {
    btnAnalisarTexto.addEventListener('click', async function() {
        const texto = descricaoTextarea.value.trim();
        const conselho = document.getElementById('conselho')?.value;
        const categoria = document.getElementById('categoria')?.value;
        
        if (!texto) {
            alert('Por favor, escreva uma descrição antes de analisar.');
            return;
        }
        
        // Mostrar loading
        btnAnalisarTexto.disabled = true;
        btnAnalisarTexto.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analisando...';
        
        try {
            // Chamar API do assistente no backend
            const apiBase = getScriptApiBase();
            if (!apiBase) {
                areaSugestoes.style.display = 'block';
                conteudoSugestoes.innerHTML = '<p style="color:#b45309;"><i class="fas fa-info-circle"></i> Assistente de IA disponível apenas com o servidor ativo.</p>';
                return;
            }
            const response = await fetch(apiBase + '/api/assistente/analisar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    texto: texto,
                    conselho: conselho,
                    categoria: categoria
                })
            });
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Erro ao analisar texto');
            }
            
            // Exibir relatório HTML gerado pelo backend
            conteudoSugestoes.innerHTML = data.relatorio_html;
            areaSugestoes.style.display = 'block';
            
            // Scroll suave até as sugestões
            areaSugestoes.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
        } catch (error) {
            console.error('Erro ao analisar texto:', error);
            alert('Erro ao analisar o texto. Tente novamente.');
        } finally {
            btnAnalisarTexto.disabled = false;
            btnAnalisarTexto.innerHTML = '<i class="fas fa-magic"></i> Analisar e Melhorar Texto';
        }
    });
}

if (btnFecharSugestoes) {
    btnFecharSugestoes.addEventListener('click', function() {
        areaSugestoes.style.display = 'none';
    });
}

// Função para analisar texto localmente (versão simplificada)
async function analisarTextoLocal(texto, conselho, categoria) {
    // Análise básica local
    const palavras = texto.split(/\s+/).length;
    const caracteres = texto.length;
    
    const elementos = {
        quem: /\b(dr\.|dra\.|nome|profissional|médico|advogado|engenheiro)\b/i.test(texto),
        quando: /\b(dia|data|em|durante|2024|2025|mês|ano)\b/i.test(texto),
        onde: /\b(hospital|consultório|clínica|escritório|obra|local)\b/i.test(texto),
        consequencias: /\b(dano|prejuízo|lesão|morte|sequela|perda|sofreu)\b/i.test(texto)
    };
    
    const elementosPresentes = Object.values(elementos).filter(v => v).length;
    const pontuacao = Math.min(100, (elementosPresentes / 4) * 100 + (caracteres > 200 ? 20 : 0));
    
    const sugestoes = [];
    if (!elementos.quem) sugestoes.push('📝 Identifique o profissional: nome completo, número de registro e local de trabalho.');
    if (!elementos.quando) sugestoes.push('📅 Informe a data ou período: dia/mês/ano ou período aproximado.');
    if (!elementos.onde) sugestoes.push('📍 Descreva o local: nome do hospital/consultório/escritório e endereço.');
    if (!elementos.consequencias) sugestoes.push('⚠️ Descreva as consequências: danos físicos, prejuízos financeiros, sequelas.');
    if (caracteres < 200) sugestoes.push('✍️ Amplie a descrição: quanto mais detalhes, melhor a análise.');
    sugestoes.push('📎 Se possível, mencione documentos, fotos ou testemunhas.');
    
    let textoMelhorado = texto;
    if (caracteres < 100) {
        textoMelhorado = `Denúncia contra profissional do ${conselho || '[CONSELHO]'} por ${categoria || '[CATEGORIA]'}.

FATOS:
${texto}

[ADICIONE AQUI: Quando ocorreu - data ou período]
[ADICIONE AQUI: Onde ocorreu - local específico]
[ADICIONE AQUI: Consequências - danos ou prejuízos causados]

DOCUMENTOS/PROVAS:
[Se houver, mencione: documentos, fotos, laudos, testemunhas, etc.]`;
    }
    
    return {
        pontuacao_qualidade: Math.round(pontuacao),
        tamanho: caracteres,
        palavras: palavras,
        elementos_presentes: elementosPresentes,
        elementos_faltantes: 4 - elementosPresentes,
        sugestoes: sugestoes,
        texto_melhorado: textoMelhorado
    };
}

// Função para gerar relatório HTML
function gerarRelatorioHTML(analise) {
    const pontuacao = analise.pontuacao_qualidade;
    let cor, nivel;
    
    if (pontuacao >= 80) {
        cor = '#10b981';
        nivel = 'Excelente';
    } else if (pontuacao >= 60) {
        cor = '#ffc107';
        nivel = 'Bom';
    } else if (pontuacao >= 40) {
        cor = '#ff9800';
        nivel = 'Regular';
    } else {
        cor = '#ef4444';
        nivel = 'Precisa melhorar';
    }
    
    return `
        <div class="analise-container">
            <div class="analise-card">
                <h4>📊 Qualidade do Texto</h4>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${pontuacao}%; background: ${cor};"></div>
                </div>
                <p class="pontuacao"><span style="color: ${cor}; font-weight: 700;">${pontuacao}/100</span> - ${nivel}</p>
                <p class="info-texto">${analise.palavras} palavras • ${analise.tamanho} caracteres</p>
            </div>
            
            <div class="analise-card">
                <h4>✅ Elementos da Denúncia</h4>
                <p>Presentes: <strong>${analise.elementos_presentes}/4</strong></p>
                ${analise.elementos_faltantes > 0 ? `<p style="color: #ef4444;">Faltantes: <strong>${analise.elementos_faltantes}</strong></p>` : ''}
            </div>
            
            <div class="analise-card">
                <h4>💡 Sugestões de Melhoria</h4>
                <ul class="lista-sugestoes">
                    ${analise.sugestoes.map(sug => `<li>${sug}</li>`).join('')}
                </ul>
            </div>
            
            <div class="analise-card">
                <h4>✨ Texto Melhorado Sugerido</h4>
                <div class="texto-melhorado">
                    <pre>${analise.texto_melhorado}</pre>
                </div>
                <button type="button" class="btn-copiar" onclick="copiarTextoMelhorado()">
                    <i class="fas fa-copy"></i> Copiar Texto Melhorado
                </button>
            </div>
        </div>
    `;
}

// Função para copiar texto melhorado
function copiarTextoMelhorado() {
    const textoMelhorado = document.querySelector('.texto-melhorado pre').textContent;
    navigator.clipboard.writeText(textoMelhorado).then(() => {
        const btnCopiar = document.querySelector('.btn-copiar');
        const textoOriginal = btnCopiar.innerHTML;
        btnCopiar.innerHTML = '<i class="fas fa-check"></i> Copiado!';
        btnCopiar.style.background = '#10b981';
        setTimeout(() => {
            btnCopiar.innerHTML = textoOriginal;
            btnCopiar.style.background = '';
        }, 2000);
    });
}

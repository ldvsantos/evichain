// Dashboard Principal - Sistema EviChain
let complaintsData = [];
let analyticsData = {};
let currentComplaint = null; // Armazena a denúncia atualmente aberta no modal

// Inicialização do dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    loadLatestComplaintAnalysis();
});

async function loadDashboardData() {
    showLoading(true);
    
    try {
        // Carregamento em paralelo de todas as informações
        const [complaintsResponse, analyticsResponse] = await Promise.all([
            fetch('api/complaints'),
            fetch('api/analytics')
        ]);
        
        if (!complaintsResponse.ok || !analyticsResponse.ok) {
            throw new Error('Servidor indisponível. No GitHub Pages, o backend não está ativo.');
        }
        
        const complaintsResult = await complaintsResponse.json();
        analyticsData = await analyticsResponse.json();
        
        // Extrai o array de denúncias da resposta
        if (complaintsResult.success && complaintsResult.complaints) {
            complaintsData = complaintsResult.complaints;
        } else {
            complaintsData = [];
        }
        
        // Atualiza todas as seções
        updateComplaintsTable();
        updateAnalytics();
        updateRecentTransactions();
        
    } catch (error) {
        showError('Erro ao carregar dados: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Atualiza a tabela de denúncias
function updateComplaintsTable() {
    const tbody = document.getElementById('complaintsTableBody');
    
    if (!tbody) {
        console.error('Elemento complaintsTableBody não encontrado!');
        return;
    }
    
    tbody.innerHTML = '';
    
    if (!complaintsData || complaintsData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhuma denúncia encontrada</td></tr>';
        return;
    }
    
    complaintsData.forEach((complaint, index) => {
        const row = document.createElement('tr');
        
        // Análise de IA
        const iaAnalysis = complaint.ia_analysis || {};
        const gravidade = iaAnalysis.analise_juridica?.gravidade || 'Não analisado';
        const gravidadeBadge = getGravidadeBadgeClass(gravidade);
        
        row.innerHTML = `
            <td><code>${complaint.id || 'N/A'}</code></td>
            <td>${complaint.titulo || complaint.assunto || 'Sem título'}</td>
            <td>
                <span class="badge ${gravidadeBadge}">${gravidade}</span>
            </td>
            <td>${complaint.categoria || 'N/A'}</td>
            <td>${formatDate(complaint.timestamp)}</td>
            <td>
                <span class="badge bg-primary">Registrada</span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="viewComplaintDetails('${complaint.id}')">
                    <i class="fas fa-eye"></i> Ver Detalhes
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Atualiza métricas analíticas
function updateAnalytics() {
    const elements = {
        'totalComplaints': document.getElementById('totalComplaints'),
        'pendingComplaints': document.getElementById('pendingComplaints'),
        'resolvedComplaints': document.getElementById('resolvedComplaints'),
        'averageResolutionTime': document.getElementById('averageResolutionTime')
    };
    
    Object.entries(elements).forEach(([key, element]) => {
        if (element) {
            element.textContent = analyticsData[key] || '0';
        }
    });
}

// Atualiza transações recentes
function updateRecentTransactions() {
    const container = document.getElementById('recentTransactions');
    if (!container) return;
    
    container.innerHTML = '';
    
    const recentComplaints = complaintsData.slice(0, 5);
    
    if (recentComplaints.length === 0) {
        container.innerHTML = '<p>Nenhuma transação encontrada</p>';
        return;
    }
    
    recentComplaints.forEach(complaint => {
        const div = document.createElement('div');
        div.className = 'transaction-item';
        div.innerHTML = `
            <div class="transaction-hash">${complaint.id || 'N/A'}</div>
            <div class="transaction-time">${formatDate(complaint.data)}</div>
        `;
        container.appendChild(div);
    });
}

// Funções utilitárias
function formatDate(timestamp) {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('pt-BR');
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';
    }
}

function showError(message) {
    console.error(message);
    // Exibir mensagem amigável no dashboard em vez de alert
    const container = document.querySelector('.dashboard-content') || document.querySelector('main') || document.body;
    const existingBanner = document.getElementById('errorBanner');
    if (existingBanner) existingBanner.remove();
    const banner = document.createElement('div');
    banner.id = 'errorBanner';
    banner.style.cssText = 'background:#fef2f2;border:1px solid #fca5a5;color:#991b1b;padding:20px;border-radius:12px;margin:20px auto;max-width:800px;text-align:center;font-family:Inter,sans-serif;';
    banner.innerHTML = `
        <p style="font-size:1.1rem;font-weight:600;margin-bottom:8px;"><i class="fas fa-exclamation-triangle" style="color:#dc2626;"></i> Dados indisponíveis</p>
        <p style="margin-bottom:12px;">O servidor backend não está acessível neste ambiente. Para visualizar dados reais, acesse via <a href="http://3.15.2.17/" target="_blank" style="color:#2563eb;text-decoration:underline;">servidor EC2</a>.</p>
        <button onclick="this.parentElement.remove()" style="background:#dc2626;color:white;border:none;padding:8px 20px;border-radius:6px;cursor:pointer;">Fechar</button>
    `;
    container.prepend(banner);
}

// Funções dos botões
function refreshData() {
    loadDashboardData();
}

function exportReport() {
    window.open('api/export-blockchain', '_blank');
}

function goBack() {
    window.location.href = 'index.html';
}

function openInvestigationPage() {
    window.location.href = 'investigador.html';
}

function viewComplaintDetails(complaintId) {
    const complaint = complaintsData.find(c => c.id === complaintId);
    if (!complaint) return;
    
    // Armazenar denúncia atual para geração de PDF
    currentComplaint = complaint;
    
    const modal = document.getElementById('complaintModal');
    const modalBody = document.getElementById('modalBody');
    
    const iaAnalysis = complaint.ia_analysis || {};
    const metadata = complaint.metadata || {};
    
    let legislacaoHtml = '';
    const legislacao = iaAnalysis.analise_juridica?.legislacao_especifica;
    if (legislacao) {
        legislacaoHtml = `
        <div class="legislacao-box">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                <span style="font-size:1.7em;">⚖️</span>
                <h4 style="color:#1976d2; margin:0;">Legislação Recomendada pela IA</h4>
            </div>
            <div style="font-size:0.98em; color:#444; margin-bottom:10px;">Abaixo estão os principais artigos e penalidades recomendados para este caso, conforme legislação treinada.</div>
            
            <div style="background:#e8f5e8; border-left:4px solid #4caf50; padding:10px; margin:10px 0; border-radius:4px;">
                <strong>📜 Legislação Sugerida:</strong> ${legislacao.legislacao_sugerida || 'N/A'}
            </div>
            
            <table style="width:100%; border-collapse:collapse; background:#f0f6ff; border-radius:8px;">
                <tr>
                    <td style="width:32%; font-weight:bold; color:#1976d2;">Conselho:</td>
                    <td>${legislacao.conselho || 'N/A'}</td>
                </tr>
                <tr>
                    <td style="font-weight:bold; color:#1976d2;">Tipo de Infração:</td>
                    <td>${legislacao.tipo || 'N/A'}</td>
                </tr>
                <tr>
                    <td style="font-weight:bold; color:#1976d2;">Descrição:</td>
                    <td>${legislacao.descricao || 'N/A'}</td>
                </tr>
                <tr>
                    <td style="font-weight:bold; color:#1976d2;">Artigos:</td>
                    <td>
                        ${legislacao.artigos && legislacao.artigos.length > 0 ? legislacao.artigos.map(a => `<span class='artigo-tag' title='Clique para ver detalhes do artigo'>${a}</span>`).join(' ') : 'N/A'}
                    </td>
                </tr>
                <tr>
                    <td style="font-weight:bold; color:#1976d2;">Penalidades:</td>
                    <td>
                        ${legislacao.penalidades && legislacao.penalidades.length > 0 ? legislacao.penalidades.map(p => `<span class='penalidade-tag' title='Penalidade prevista na legislação'>${p}</span>`).join(' ') : 'N/A'}
                    </td>
                </tr>
            </table>
        </div>
        <style>
            .legislacao-box { margin: 18px 0 10px 0; padding: 14px; background: #f0f6ff; border-radius: 10px; box-shadow: 0 2px 12px #0002; }
            .artigo-tag { display: inline-block; background: #d0eaff; color: #1976d2; border-radius: 4px; padding: 3px 10px; margin: 2px; font-size: 1em; cursor: pointer; transition: background 0.2s; }
            .artigo-tag:hover { background: #90caf9; }
            .penalidade-tag { display: inline-block; background: #ffd6d6; color: #c62828; border-radius: 4px; padding: 3px 10px; margin: 2px; font-size: 1em; cursor: pointer; transition: background 0.2s; }
            .penalidade-tag:hover { background: #ff8a80; }
        </style>
        `;
    }

    // Seção de Investigação Automática
    let investigacaoHtml = '';
    const investigacao = iaAnalysis.investigacao_automatica;
    if (investigacao) {
        const deteccao = investigacao.deteccao_nomes || {};
        const investigacoes = investigacao.investigacoes_realizadas || [];
        
        investigacaoHtml = `
        <div class="investigacao-automatica-box">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:15px;">
                <span style="font-size:1.8em;">🔍</span>
                <h4 style="color:#d32f2f; margin:0;">Investigação Automática Realizada</h4>
            </div>
            
            <div style="background:#fff3e0; border-left:4px solid #ff9800; padding:12px; margin:10px 0; border-radius:6px;">
                <strong>📋 Relatório de Detecção:</strong>
                <pre style="background:#f5f5f5; padding:10px; border-radius:4px; margin-top:8px; font-size:0.9em; white-space: pre-wrap;">${investigacao.relatorio_deteccao || 'Relatório não disponível'}</pre>
            </div>
            
            ${deteccao.nomes_detectados && deteccao.nomes_detectados.length > 0 ? `
            <div style="background:#e8f5e8; border-radius:8px; padding:12px; margin:10px 0;">
                <h5 style="color:#2e7d32; margin:0 0 10px 0;">👤 Profissionais Identificados</h5>
                ${deteccao.nomes_detectados.map(nome => `
                    <div style="background:#ffffff; border-radius:6px; padding:10px; margin:8px 0; border-left:3px solid #4caf50;">
                        <strong>${nome.nome_detectado}</strong>
                        <br><small>Confiabilidade: ${nome.confiabilidade}% | Contexto: ${nome.contexto_encontrado}</small>
                    </div>
                `).join('')}
            </div>
            ` : ''}
            
            ${investigacoes.length > 0 ? `
            <div style="margin-top:15px;">
                <h5 style="color:#1976d2; margin-bottom:12px;">📊 Resultados das Investigações</h5>
                ${investigacoes.map((inv, index) => {
                    const resultado = inv.resultado_investigacao || {};
                    const registros = resultado.registros_oficiais || {};
                    const dadosProf = registros.dados_profissional || {};
                    const resumo = resultado.resumo_investigacao || {};
                    
                    return `
                    <div class="investigacao-item" style="background:#f3f4f6; border-radius:8px; padding:15px; margin:10px 0; border:1px solid #e1e5e9;">
                        <div style="display:flex; justify-content:between; align-items:center; margin-bottom:10px;">
                            <h6 style="color:#1976d2; margin:0;">🔎 ${inv.nome_investigado}</h6>
                            <span class="badge" style="background:${registros.registro_encontrado ? '#4caf50' : '#ff9800'}; color:white; font-size:0.8em; padding:4px 8px; border-radius:4px;">
                                ${registros.registro_encontrado ? 'REGISTRO ENCONTRADO' : 'BUSCA REALIZADA'}
                            </span>
                        </div>
                        
                        ${registros.registro_encontrado && dadosProf.nome_completo_oficial ? `
                        <div style="background:#e8f5e8; border-radius:6px; padding:10px; margin:8px 0;">
                            <strong>📋 Nome Oficial:</strong> ${dadosProf.nome_completo_oficial}<br>
                            <strong>📄 Registro:</strong> ${dadosProf.registro_crm_completo || dadosProf.registro_completo || 'N/A'}<br>
                            <strong>⚖️ Situação:</strong> <span style="color:${dadosProf.situacao_registro && (dadosProf.situacao_registro.toLowerCase().includes('ativo') || dadosProf.situacao_registro.toLowerCase().includes('regular')) ? '#4caf50' : '#f44336'}">${dadosProf.situacao_registro || 'N/A'}</span><br>
                            <strong>🎓 Formação:</strong> ${dadosProf.tipo_formacao || 'N/A'}<br>
                            ${dadosProf.especialidades_registradas ? `<strong>🏥 Especialidades:</strong> ${Array.isArray(dadosProf.especialidades_registradas) ? dadosProf.especialidades_registradas.join(', ') : dadosProf.especialidades_registradas}<br>` : ''}
                            ${dadosProf.cidade_registro ? `<strong>📍 Cidade:</strong> ${dadosProf.cidade_registro}<br>` : ''}
                        </div>
                        ` : ''}
                        
                        ${resumo.pontuacao_confiabilidade !== undefined ? `
                        <div style="margin:8px 0;">
                            <strong>🎯 Confiabilidade da Investigação:</strong> 
                            <span style="color:#1976d2; font-weight:bold;">${resumo.pontuacao_confiabilidade}/100</span>
                        </div>
                        ` : ''}
                        
                        <button class="btn btn-sm btn-outline-primary" onclick="verDetalhesInvestigacao('${inv.nome_investigado}', ${index})" style="margin-top:8px;">
                            📄 Ver Relatório Completo
                        </button>
                    </div>
                    `;
                }).join('')}
            </div>
            ` : `
            <div style="background:#ffebee; border-radius:6px; padding:10px; margin:10px 0; color:#c62828;">
                <strong>ℹ️ Informação:</strong> Nenhuma investigação foi realizada automaticamente para esta denúncia.
            </div>
            `}
        </div>
        
        <style>
            .investigacao-automatica-box { 
                margin: 20px 0; 
                padding: 18px; 
                background: linear-gradient(135deg, #fff8e1 0%, #f3e5f5 100%); 
                border-radius: 12px; 
                box-shadow: 0 3px 15px rgba(0,0,0,0.1); 
                border: 1px solid #e1bee7;
            }
            .investigacao-item {
                transition: transform 0.2s ease;
            }
            .investigacao-item:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
        </style>
        `;
    }

    modalBody.innerHTML = `
        <div class="complaint-details">
            <h4>Informações Gerais</h4>
            <p><strong>ID:</strong> ${complaint.id}</p>
            <p><strong>Título:</strong> ${complaint.titulo || 'N/A'}</p>
            <p><strong>Assunto:</strong> ${complaint.assunto || 'N/A'}</p>
            <p><strong>Prioridade:</strong> ${complaint.prioridade || 'N/A'}</p>
            <p><strong>Finalidade:</strong> ${complaint.finalidade || 'N/A'}</p>
            <p><strong>Conselho:</strong> ${complaint.conselho || 'N/A'}</p>
            <p><strong>Categoria:</strong> ${complaint.categoria || 'N/A'}</p>
            <p><strong>Data:</strong> ${formatDate(complaint.timestamp)}</p>
            ${complaint.codigosAnteriores ? `<p><strong>Códigos Anteriores:</strong> ${complaint.codigosAnteriores}</p>` : ''}
            
            <h4>Configurações de Privacidade</h4>
            <p><strong>Ouvidoria Anônima:</strong> ${complaint.ouvidoriaAnonima ? 'Sim' : 'Não'}</p>
            <p><strong>Manter Anonimato:</strong> ${complaint.anonymous ? 'Sim' : 'Não'}</p>
            
            <h4>Descrição</h4>
            <p>${complaint.descricao || 'Não disponível'}</p>
            
            ${investigacaoHtml}
            
            <h4>🤖 Análise de IA</h4>
            <p><strong>Gravidade:</strong> ${iaAnalysis.analise_juridica?.gravidade || 'N/A'}</p>
            <p><strong>Tipificação:</strong> ${iaAnalysis.analise_juridica?.tipificacao || 'N/A'}</p>
            <p><strong>Nível de Risco:</strong> ${iaAnalysis.classificacao_risco?.nivel || 'N/A'} (${iaAnalysis.classificacao_risco?.pontuacao || 0}/100)</p>
            <p><strong>Ação Recomendada:</strong> ${iaAnalysis.classificacao_risco?.acao_recomendada || 'N/A'}</p>
            <p><strong>Resumo:</strong> ${iaAnalysis.analise_basica?.resumo || 'Não disponível'}</p>
            <p><strong>Legislação possível:</strong> ${iaAnalysis.analise_juridica?.legislacao_especifica?.legislacao_sugerida || 'N/A'}</p>
            ${legislacaoHtml}
            ${iaAnalysis.analise_basica?.palavras_chave?.length > 0 ? `
            <h4>🔍 Palavras-Chave Identificadas</h4>
            <p>${iaAnalysis.analise_basica.palavras_chave.join(', ')}</p>
            ` : ''}
            ${iaAnalysis.recomendacoes?.length > 0 ? `
            <h4>💡 Recomendações</h4>
            <ul>
                ${iaAnalysis.recomendacoes.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
            ` : ''}
        </div>
    `;
    
    modal.style.display = 'flex';
}

function closeModal() {
    const modal = document.getElementById('complaintModal');
    modal.style.display = 'none';
}

// Fechar modal clicando fora dele
window.onclick = function(event) {
    const modal = document.getElementById('complaintModal');
    if (event.target === modal) {
        closeModal();
    }
}

// Função para ver detalhes da investigação (será implementada quando necessário)
function verDetalhesInvestigacao(nomeInvestigado, index) {
    alert(`Ver detalhes completos da investigação para: ${nomeInvestigado}\nÍndice: ${index}`);
    // Aqui você pode implementar um modal adicional ou expandir a seção
}

// Carrega análise inteligente da última denúncia
async function loadLatestComplaintAnalysis() {
    const analysisContainer = document.getElementById('analysisContainer');
    if (!analysisContainer) return;

    try {
        const response = await fetch('api/latest-analysis');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (!data || !data.full_analysis) {
            analysisContainer.innerHTML = '<p>Nenhuma análise de denúncia encontrada.</p>';
            return;
        }

        const complaint_id = data.complaint_id;
        const analise = data.full_analysis;
        
        const analiseBasica = analise.analise_basica || {};
        const analiseJuridica = analise.analise_juridica || {};
        const classificacaoRisco = analise.classificacao_risco || {};
        
        const nivelRisco = classificacaoRisco.nivel || 'MÉDIO';
        const corRisco = classificacaoRisco.cor || '#ffc107';
        const pontuacaoRisco = classificacaoRisco.pontuacao || 50;
        
        analysisContainer.innerHTML = `
            <div class="analysis-header mb-4">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">
                        <i class="fas fa-brain text-primary me-2"></i>
                        Análise Inteligente - ${complaint_id}
                    </h5>
                    <span class="badge" style="background-color: ${corRisco}; color: white;">
                        Risco ${nivelRisco}
                    </span>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card border-0 shadow-sm mb-3">
                        <div class="card-body">
                            <h6 class="card-title">
                                <i class="fas fa-file-alt text-info me-2"></i>
                                Resumo Executivo
                            </h6>
                            <p class="card-text">${analiseBasica.resumo || 'Resumo não disponível'}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card border-0 shadow-sm mb-3">
                        <div class="card-body">
                            <h6 class="card-title">
                                <i class="fas fa-exclamation-triangle text-danger me-2"></i>
                                Classificação de Risco
                            </h6>
                            <div class="risk-analysis">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <span>Pontuação de Risco</span>
                                    <strong>${pontuacaoRisco}/100</strong>
                                </div>
                                <div class="progress mb-3">
                                    <div class="progress-bar" style="width: ${pontuacaoRisco}%; background-color: ${corRisco}"></div>
                                </div>
                                <p><strong>Ação Recomendada:</strong></p>
                                <p class="text-muted">${classificacaoRisco.acao_recomendada || 'Análise padrão'}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Erro ao carregar análise:', error);
        if (analysisContainer) {
            analysisContainer.innerHTML = `
                <div class="analysis-error">
                    <i class="fas fa-exclamation-circle fa-3x text-danger mb-3"></i>
                    <p class="text-danger">Erro ao carregar análise da IA</p>
                    <small class="text-muted">${error.message}</small>
                </div>
            `;
        }
    }
}

// Determina a classe CSS para o badge de gravidade
function getGravidadeBadgeClass(gravidade) {
    switch(gravidade?.toLowerCase()) {
        case 'grave': return 'bg-danger';
        case 'média': case 'media': return 'bg-warning';
        case 'leve': return 'bg-success';
        default: return 'bg-secondary';
    }
}

// ============================================================================
// GERAÇÃO DE PDF
// ============================================================================

function exportToPDF() {
    if (!currentComplaint) {
        alert('Nenhuma denúncia selecionada para exportar.');
        return;
    }
    
    // Perguntar ao usuário qual método usar
    const useBackend = confirm(
        'Escolha o método para gerar o PDF:\n\n' +
        'OK - Usar servidor (PDF profissional com formatação avançada)\n' +
        'Cancelar - Usar navegador (PDF simples, sem necessidade do servidor)'
    );
    
    if (useBackend) {
        exportPDFViaBackend();
    } else {
        exportPDFViaFrontend();
    }
}

function exportPDFViaBackend() {
    try {
        // Preparar dados completos para envio ao backend
        const pdfData = {
            // Informações básicas
            complaint_id: currentComplaint.id || 'sem_id',
            titulo: currentComplaint.titulo || 'N/A',
            assunto: currentComplaint.assunto || 'N/A',
            prioridade: currentComplaint.prioridade || 'N/A',
            finalidade: currentComplaint.finalidade || 'N/A',
            conselho: currentComplaint.conselho || 'N/A',
            categoria: currentComplaint.categoria || 'N/A',
            timestamp: currentComplaint.timestamp || new Date().toISOString(),
            codigosAnteriores: currentComplaint.codigosAnteriores || null,
            
            // Configurações de privacidade
            ouvidoriaAnonima: currentComplaint.ouvidoriaAnonima || false,
            anonymous: currentComplaint.anonymous || false,
            
            // Descrição
            descricao: currentComplaint.descricao || 'Não disponível',
            
            // Análise completa da IA
            ia_analysis: currentComplaint.ia_analysis || {},
            
            // Metadados adicionais
            metadata: currentComplaint.metadata || {}
        };
        
        showSuccessMessage('Gerando PDF no servidor...');
        
        // Fazer requisição para o backend
        fetch('api/generate_pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(pdfData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            return response.blob();
        })
        .then(blob => {
            // Criar URL para download
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `EviChain_Denuncia_${currentComplaint.id || 'sem_id'}_${getCurrentDateString()}.pdf`;
            
            // Adicionar ao DOM, clicar e remover
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            // Limpar URL
            window.URL.revokeObjectURL(url);
            
            showSuccessMessage('PDF baixado com sucesso!');
        })
        .catch(error => {
            console.error('Erro ao gerar PDF via backend:', error);
            showError('Erro ao gerar PDF via servidor: ' + error.message + '\nTentando método alternativo...');
            
            // Fallback para frontend
            setTimeout(() => {
                exportPDFViaFrontend();
            }, 2000);
        });
        
    } catch (error) {
        console.error('Erro ao preparar dados para PDF:', error);
        showError('Erro ao preparar dados: ' + error.message);
        
        // Fallback para frontend
        exportPDFViaFrontend();
    }
}

function exportPDFViaFrontend() {
function exportPDFViaFrontend() {
    if (!currentComplaint) {
        alert('Nenhuma denúncia selecionada para exportar.');
        return;
    }
    
    try {
        // Verificar se jsPDF está disponível
        if (!window.jspdf) {
            showError('Biblioteca jsPDF não carregada. Recarregue a página e tente novamente.');
            return;
        }
        
        // Inicializar jsPDF
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        
        // Configurações
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        const margin = 20;
        const maxWidth = pageWidth - (margin * 2);
        let yPosition = margin;
        
        showSuccessMessage('Gerando PDF no navegador...');
        
        // Header do documento
        addPDFHeader(doc, yPosition, maxWidth);
        yPosition += 30;
        
        // Informações básicas da denúncia
        yPosition = addBasicInfo(doc, yPosition, maxWidth);
        yPosition += 10;
        
        // Análise da IA
        yPosition = addIAAnalysis(doc, yPosition, maxWidth);
        
        // Investigação automática
        yPosition = addInvestigationResults(doc, yPosition, maxWidth);
        
        // Footer
        addPDFFooter(doc, pageHeight);
        
        // Salvar PDF
        const fileName = `EviChain_Denuncia_${currentComplaint.id || 'sem_id'}_${getCurrentDateString()}.pdf`;
        doc.save(fileName);
        
        showSuccessMessage(`PDF exportado com sucesso: ${fileName}`);
        
    } catch (error) {
        console.error('Erro ao gerar PDF via frontend:', error);
        showError('Erro ao gerar PDF no navegador: ' + error.message);
    }
}
}

function addPDFHeader(doc, yPos, maxWidth) {
    const margin = 20;
    const pageWidth = doc.internal.pageSize.getWidth();
    
    // Logo/Título
    doc.setFontSize(20);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(30, 64, 175); // Azul EviChain
    doc.text('EVICHAIN - SISTEMA DE ANÁLISE DE DENÚNCIAS', margin, yPos);
    
    // Linha separadora
    doc.setDrawColor(200, 200, 200);
    doc.line(margin, yPos + 5, pageWidth - margin, yPos + 5);
    
    // Data e hora do relatório
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(100, 100, 100);
    doc.text(`Relatório gerado em: ${getCurrentDateTime()}`, margin, yPos + 15);
}

function addBasicInfo(doc, yPos, maxWidth) {
    const margin = 20;
    let currentY = yPos;
    
    // Título da seção
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 0, 0);
    doc.text('INFORMAÇÕES BÁSICAS DA DENÚNCIA', margin, currentY);
    currentY += 10;
    
    // Informações básicas completas
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    
    const basicInfo = [
        ['ID da Denúncia:', currentComplaint.id || 'N/A'],
        ['Título:', currentComplaint.titulo || 'N/A'],
        ['Assunto:', currentComplaint.assunto || 'N/A'],
        ['Prioridade:', currentComplaint.prioridade || 'N/A'],
        ['Finalidade:', currentComplaint.finalidade || 'N/A'],
        ['Conselho:', currentComplaint.conselho || 'N/A'],
        ['Categoria:', currentComplaint.categoria || 'N/A'],
        ['Data de Registro:', formatDate(currentComplaint.timestamp)],
        ['Status:', 'Registrada']
    ];

    // Adicionar códigos anteriores se existir
    if (currentComplaint.codigosAnteriores) {
        basicInfo.push(['Códigos Anteriores:', currentComplaint.codigosAnteriores]);
    }
    
    basicInfo.forEach(([label, value]) => {
        doc.setFont('helvetica', 'bold');
        doc.text(label, margin, currentY);
        doc.setFont('helvetica', 'normal');
        const wrappedText = doc.splitTextToSize(value, maxWidth - 60);
        doc.text(wrappedText, margin + 60, currentY);
        currentY += wrappedText.length * 5;
    });
    
    // Configurações de Privacidade
    currentY += 5;
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(50, 50, 50);
    doc.text('CONFIGURAÇÕES DE PRIVACIDADE', margin, currentY);
    currentY += 8;
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0, 0, 0);
    
    const privacyInfo = [
        ['Ouvidoria Anônima:', currentComplaint.ouvidoriaAnonima ? 'Sim' : 'Não'],
        ['Manter Anonimato:', currentComplaint.anonymous ? 'Sim' : 'Não']
    ];
    
    privacyInfo.forEach(([label, value]) => {
        doc.setFont('helvetica', 'bold');
        doc.text(label, margin, currentY);
        doc.setFont('helvetica', 'normal');
        doc.text(value, margin + 60, currentY);
        currentY += 5;
    });
    
    // Descrição da denúncia
    if (currentComplaint.descricao) {
        currentY += 8;
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(50, 50, 50);
        doc.text('DESCRIÇÃO DA DENÚNCIA', margin, currentY);
        currentY += 8;
        
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(0, 0, 0);
        const descriptionText = doc.splitTextToSize(currentComplaint.descricao, maxWidth);
        doc.text(descriptionText, margin, currentY);
        currentY += descriptionText.length * 5;
    }
    
    return currentY;
}

function addIAAnalysis(doc, yPos, maxWidth) {
    const margin = 20;
    let currentY = yPos;
    const iaAnalysis = currentComplaint.ia_analysis || {};
    
    if (!Object.keys(iaAnalysis).length) {
        return currentY;
    }
    
    // Verificar se precisa de nova página
    if (currentY > 200) {
        doc.addPage();
        currentY = margin;
    }
    
    // Título da seção
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 0, 0);
    doc.text('ANÁLISE INTELIGENTE (IA)', margin, currentY);
    currentY += 12;
    
    // Análise básica da IA
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(50, 50, 50);
    doc.text('Análise Básica', margin, currentY);
    currentY += 8;
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0, 0, 0);
    
    const basicIAInfo = [
        ['Gravidade:', iaAnalysis.analise_juridica?.gravidade || 'N/A'],
        ['Tipificação:', iaAnalysis.analise_juridica?.tipificacao || 'N/A'],
        ['Nível de Risco:', `${iaAnalysis.classificacao_risco?.nivel || 'N/A'} (${iaAnalysis.classificacao_risco?.pontuacao || 0}/100)`],
        ['Ação Recomendada:', iaAnalysis.classificacao_risco?.acao_recomendada || 'N/A'],
        ['Legislação Possível:', iaAnalysis.analise_juridica?.legislacao_especifica?.legislacao_sugerida || 'N/A']
    ];
    
    basicIAInfo.forEach(([label, value]) => {
        doc.setFont('helvetica', 'bold');
        doc.text(label, margin, currentY);
        doc.setFont('helvetica', 'normal');
        const wrappedText = doc.splitTextToSize(value, maxWidth - 65);
        doc.text(wrappedText, margin + 65, currentY);
        currentY += wrappedText.length * 5;
    });
    
    // Resumo da IA
    if (iaAnalysis.analise_basica?.resumo) {
        currentY += 5;
        doc.setFont('helvetica', 'bold');
        doc.text('Resumo:', margin, currentY);
        currentY += 7;
        
        doc.setFont('helvetica', 'normal');
        const resumoText = doc.splitTextToSize(iaAnalysis.analise_basica.resumo, maxWidth);
        doc.text(resumoText, margin, currentY);
        currentY += resumoText.length * 5;
    }
    
    // Palavras-chave
    if (iaAnalysis.analise_basica?.palavras_chave?.length > 0) {
        currentY += 5;
        doc.setFont('helvetica', 'bold');
        doc.text('Palavras-Chave Identificadas:', margin, currentY);
        currentY += 7;
        
        doc.setFont('helvetica', 'normal');
        const palavrasText = iaAnalysis.analise_basica.palavras_chave.join(', ');
        const wrappedPalavras = doc.splitTextToSize(palavrasText, maxWidth);
        doc.text(wrappedPalavras, margin, currentY);
        currentY += wrappedPalavras.length * 5;
    }
    
    // Recomendações
    if (iaAnalysis.recomendacoes?.length > 0) {
        currentY += 8;
        doc.setFont('helvetica', 'bold');
        doc.text('Recomendações:', margin, currentY);
        currentY += 7;
        
        doc.setFont('helvetica', 'normal');
        iaAnalysis.recomendacoes.forEach(rec => {
            const recText = doc.splitTextToSize(`• ${rec}`, maxWidth - 5);
            doc.text(recText, margin, currentY);
            currentY += recText.length * 5;
        });
    }
    
    // Legislação específica detalhada
    const legislacao = iaAnalysis.analise_juridica?.legislacao_especifica;
    if (legislacao) {
        currentY += 10;
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(30, 64, 175);
        doc.text('LEGISLAÇÃO RECOMENDADA PELA IA', margin, currentY);
        currentY += 10;
        
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(0, 0, 0);
        
        const legislacaoInfo = [
            ['Legislação Sugerida:', legislacao.legislacao_sugerida || 'N/A'],
            ['Conselho:', legislacao.conselho || 'N/A'],
            ['Tipo de Infração:', legislacao.tipo || 'N/A'],
            ['Descrição:', legislacao.descricao || 'N/A']
        ];
        
        legislacaoInfo.forEach(([label, value]) => {
            doc.setFont('helvetica', 'bold');
            doc.text(label, margin, currentY);
            doc.setFont('helvetica', 'normal');
            const wrappedText = doc.splitTextToSize(value, maxWidth - 70);
            doc.text(wrappedText, margin + 70, currentY);
            currentY += wrappedText.length * 5;
        });
        
        // Artigos
        if (legislacao.artigos && legislacao.artigos.length > 0) {
            currentY += 5;
            doc.setFont('helvetica', 'bold');
            doc.text('Artigos:', margin, currentY);
            currentY += 7;
            
            doc.setFont('helvetica', 'normal');
            const artigosText = legislacao.artigos.join(', ');
            const wrappedArtigos = doc.splitTextToSize(artigosText, maxWidth);
            doc.text(wrappedArtigos, margin, currentY);
            currentY += wrappedArtigos.length * 5;
        }
        
        // Penalidades
        if (legislacao.penalidades && legislacao.penalidades.length > 0) {
            currentY += 5;
            doc.setFont('helvetica', 'bold');
            doc.text('Penalidades:', margin, currentY);
            currentY += 7;
            
            doc.setFont('helvetica', 'normal');
            const penalidadesText = legislacao.penalidades.join(', ');
            const wrappedPenalidades = doc.splitTextToSize(penalidadesText, maxWidth);
            doc.text(wrappedPenalidades, margin, currentY);
            currentY += wrappedPenalidades.length * 5;
        }
    }
    
    return currentY;
}

function addInvestigationResults(doc, yPos, maxWidth) {
    const margin = 20;
    let currentY = yPos;
    const iaAnalysis = currentComplaint.ia_analysis || {};
    const investigacao = iaAnalysis.investigacao_automatica;
    
    if (!investigacao) {
        return currentY;
    }
    
    // Verificar se precisa de nova página
    if (currentY > 180) {
        doc.addPage();
        currentY = margin;
    }
    
    // Título da seção
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 0, 0);
    doc.text('INVESTIGAÇÃO AUTOMÁTICA REALIZADA', margin, currentY);
    currentY += 12;
    
    // Relatório de detecção
    if (investigacao.relatorio_deteccao) {
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(50, 50, 50);
        doc.text('Relatório de Detecção:', margin, currentY);
        currentY += 8;
        
        doc.setFontSize(9);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(0, 0, 0);
        const relatorioText = doc.splitTextToSize(investigacao.relatorio_deteccao, maxWidth);
        doc.text(relatorioText, margin, currentY);
        currentY += relatorioText.length * 4.5;
    }
    
    // Profissionais identificados
    const deteccao = investigacao.deteccao_nomes || {};
    if (deteccao.nomes_detectados && deteccao.nomes_detectados.length > 0) {
        currentY += 8;
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(46, 125, 50);
        doc.text('PROFISSIONAIS IDENTIFICADOS', margin, currentY);
        currentY += 8;
        
        deteccao.nomes_detectados.forEach(nome => {
            doc.setFontSize(10);
            doc.setFont('helvetica', 'bold');
            doc.setTextColor(0, 0, 0);
            doc.text(`• ${nome.nome_detectado}`, margin, currentY);
            currentY += 6;
            
            doc.setFontSize(9);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(80, 80, 80);
            doc.text(`Confiabilidade: ${nome.confiabilidade}%`, margin + 5, currentY);
            currentY += 5;
            
            const contextoText = doc.splitTextToSize(`Contexto: ${nome.contexto_encontrado}`, maxWidth - 10);
            doc.text(contextoText, margin + 5, currentY);
            currentY += contextoText.length * 4.5 + 5;
        });
    }
    
    // Resultados das investigações realizadas
    const investigacoes = investigacao.investigacoes_realizadas || [];
    if (investigacoes.length > 0) {
        currentY += 10;
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(25, 118, 210);
        doc.text('RESULTADOS DAS INVESTIGAÇÕES', margin, currentY);
        currentY += 10;
        
        investigacoes.forEach((inv, index) => {
            // Verificar se precisa de nova página
            if (currentY > 220) {
                doc.addPage();
                currentY = margin;
            }
            
            const resultado = inv.resultado_investigacao || {};
            const registros = resultado.registros_oficiais || {};
            const dadosProf = registros.dados_profissional || {};
            const resumo = resultado.resumo_investigacao || {};
            
            // Nome do investigado
            doc.setFontSize(10);
            doc.setFont('helvetica', 'bold');
            doc.setTextColor(0, 0, 0);
            doc.text(`🔎 ${inv.nome_investigado}`, margin, currentY);
            currentY += 8;
            
            // Status da investigação
            const statusText = registros.registro_encontrado ? 'REGISTRO ENCONTRADO' : 'BUSCA REALIZADA';
            const statusColor = registros.registro_encontrado ? [76, 175, 80] : [255, 152, 0];
            
            doc.setFontSize(9);
            doc.setFont('helvetica', 'bold');
            doc.setTextColor(...statusColor);
            doc.text(`Status: ${statusText}`, margin + 5, currentY);
            currentY += 8;
            
            // Dados do profissional (se encontrado)
            if (registros.registro_encontrado && dadosProf.nome_completo_oficial) {
                doc.setFontSize(9);
                doc.setFont('helvetica', 'bold');
                doc.setTextColor(46, 125, 50);
                doc.text('DADOS OFICIAIS ENCONTRADOS:', margin + 5, currentY);
                currentY += 6;
                
                doc.setFont('helvetica', 'normal');
                doc.setTextColor(0, 0, 0);
                
                const dadosOficiais = [
                    ['Nome Oficial:', dadosProf.nome_completo_oficial],
                    ['Registro:', dadosProf.registro_crm_completo || dadosProf.registro_completo || 'N/A'],
                    ['Situação:', dadosProf.situacao_registro || 'N/A'],
                    ['Formação:', dadosProf.tipo_formacao || 'N/A']
                ];
                
                if (dadosProf.especialidades_registradas) {
                    const especialidades = Array.isArray(dadosProf.especialidades_registradas) 
                        ? dadosProf.especialidades_registradas.join(', ') 
                        : dadosProf.especialidades_registradas;
                    dadosOficiais.push(['Especialidades:', especialidades]);
                }
                
                if (dadosProf.cidade_registro) {
                    dadosOficiais.push(['Cidade:', dadosProf.cidade_registro]);
                }
                
                dadosOficiais.forEach(([label, value]) => {
                    doc.setFont('helvetica', 'bold');
                    doc.text(label, margin + 10, currentY);
                    doc.setFont('helvetica', 'normal');
                    const valueText = doc.splitTextToSize(value, maxWidth - 80);
                    doc.text(valueText, margin + 50, currentY);
                    currentY += valueText.length * 4.5;
                });
            }
            
            // Pontuação de confiabilidade
            if (resumo.pontuacao_confiabilidade !== undefined) {
                currentY += 3;
                doc.setFont('helvetica', 'bold');
                doc.setTextColor(25, 118, 210);
                doc.text(`Confiabilidade da Investigação: ${resumo.pontuacao_confiabilidade}/100`, margin + 5, currentY);
                currentY += 6;
            }
            
            currentY += 8; // Espaçamento entre investigações
        });
    } else {
        currentY += 8;
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(150, 150, 150);
        doc.text('Nenhuma investigação foi realizada automaticamente para esta denúncia.', margin, currentY);
        currentY += 8;
    }
    
    return currentY;
}

function addSubSection(doc, yPos, maxWidth, title, dataArray) {
    const margin = 20;
    let currentY = yPos;
    
    // Título da subseção
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(50, 50, 50);
    doc.text(title, margin, currentY);
    currentY += 8;
    
    // Dados
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0, 0, 0);
    
    if (Array.isArray(dataArray[0])) {
        // Array de pares [label, value]
        dataArray.forEach(([label, value]) => {
            if (currentY > 280) {
                doc.addPage();
                currentY = margin;
            }
            
            doc.setFont('helvetica', 'bold');
            doc.text(`${label}`, margin + 5, currentY);
            doc.setFont('helvetica', 'normal');
            const wrappedText = doc.splitTextToSize(value, maxWidth - 70);
            doc.text(wrappedText, margin + 65, currentY);
            currentY += wrappedText.length * 4 + 2;
        });
    } else {
        // Array simples de strings
        dataArray.forEach(item => {
            if (currentY > 280) {
                doc.addPage();
                currentY = margin;
            }
            
            const wrappedText = doc.splitTextToSize(item, maxWidth - 10);
            doc.text(wrappedText, margin + 5, currentY);
            currentY += wrappedText.length * 4 + 2;
        });
    }
    
    return currentY + 5;
}

function addPDFFooter(doc, pageHeight) {
    const margin = 20;
    const pageWidth = doc.internal.pageSize.getWidth();
    const totalPages = doc.internal.getNumberOfPages();
    
    for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        
        // Linha separadora
        doc.setDrawColor(200, 200, 200);
        doc.line(margin, pageHeight - 20, pageWidth - margin, pageHeight - 20);
        
        // Texto do footer
        doc.setFontSize(8);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(100, 100, 100);
        doc.text('EviChain - Sistema de Análise Inteligente de Denúncias', margin, pageHeight - 10);
        doc.text(`Página ${i} de ${totalPages}`, pageWidth - margin - 30, pageHeight - 10);
    }
}

// Funções auxiliares
function getCurrentDateTime() {
    return new Date().toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function getCurrentDateString() {
    return new Date().toISOString().split('T')[0];
}

function showSuccessMessage(message) {
    // Criar notificação de sucesso
    const notification = document.createElement('div');
    notification.className = 'pdf-notification success';
    notification.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Remover após 3 segundos
    setTimeout(() => {
        notification.remove();
    }, 3000);
}
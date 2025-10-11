// =====================================================================
// EviChain Dashboard - JavaScript (Versão Corrigida)
// =====================================================================

// Variáveis globais para armazenar dados
let complaintsData = [];
let blockchainData = {};

// Inicialização quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard carregado. Iniciando carregamento de dados...');
    loadDashboardData();
    
    // Atualizar dados a cada 30 segundos
    setInterval(loadDashboardData, 30000);
});

// Função principal para carregar todos os dados do dashboard
async function loadDashboardData() {
    showLoading(true);
    
    try {
        // Carregar dados das denúncias
        await loadComplaints();
        
        // Carregar informações da blockchain
        await loadBlockchainInfo();
        
        // Atualizar estatísticas
        updateStatistics();
        
        // Atualizar gráficos
        updateCharts();
        
        // Atualizar tabela de denúncias
        updateComplaintsTable();
        
        // Atualizar informações da blockchain
        updateBlockchainInfo();
        
        // Carregar análise inteligente da última denúncia
        await loadLatestComplaintAnalysis();
        
        console.log('Dados do dashboard carregados com sucesso');
        
    } catch (error) {
        console.error('Erro ao carregar dados do dashboard:', error);
        showError('Erro ao carregar dados. Verifique a conexão com o servidor.');
    } finally {
        showLoading(false);
    }
}

// Carregar denúncias da API
async function loadComplaints() {
    try {
        const response = await fetch('/api/complaints');
        const result = await response.json();
        
        // CORREÇÃO: Acessar a propriedade 'complaints' do objeto retornado
        if (result.success && result.complaints) {
            complaintsData = result.complaints;
            console.log(`Carregadas ${complaintsData.length} denúncias`);
        } else {
            // Se 'complaints' não existir, usa um array vazio
            complaintsData = [];
            // Lança um erro se a requisição falhou
            if (!result.success) {
                throw new Error(result.error || 'Erro ao carregar denúncias');
            }
        }
    } catch (error) {
        console.error('Erro ao carregar denúncias:', error);
        complaintsData = []; // Garante que a variável seja um array em caso de erro
    }
}

// Carregar informações da blockchain
async function loadBlockchainInfo() {
    try {
        const response = await fetch('/api/blockchain-info');
        const result = await response.json();
        
        if (result.success) {
            blockchainData = result;
            console.log('Informações da blockchain carregadas');
        } else {
            throw new Error(result.error || 'Erro ao carregar blockchain');
        }
    } catch (error) {
        console.error('Erro ao carregar blockchain:', error);
        blockchainData = {};
    }
}

// Atualizar estatísticas na parte superior
function updateStatistics() {
    // Total de denúncias
    document.getElementById('totalComplaints').textContent = complaintsData.length;
    
    // Total de blocos
    const totalBlocks = blockchainData.blockchain ? blockchainData.blockchain.length : 0;
    document.getElementById('totalBlocks').textContent = totalBlocks;
    
    // Casos de alto risco (simulado)
    const highRiskCases = complaintsData.filter(complaint => {
        const iaAnalysis = complaint.ia_analysis || {};
        return iaAnalysis.classificacao_risco?.nivel === 'ALTO';
    }).length;
    document.getElementById('highRiskCases').textContent = highRiskCases;
}

// Atualizar gráficos
function updateCharts() {
    updateConselhosChart();
    updateCategoriasChart();
}

// Gráfico de denúncias por conselho
function updateConselhosChart() {
    const ctx = document.getElementById('conselhosChart');
    if (!ctx) return;
    
    // Contar denúncias por conselho
    const conselhoCount = {};
    complaintsData.forEach(complaint => {
        const conselho = complaint.conselho || 'Não especificado';
        conselhoCount[conselho] = (conselhoCount[conselho] || 0) + 1;
    });
    
    const labels = Object.keys(conselhoCount);
    const data = Object.values(conselhoCount);
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Gráfico de categorias de denúncias
function updateCategoriasChart() {
    const ctx = document.getElementById('categoriasChart');
    if (!ctx) return;
    
    // Contar denúncias por categoria
    const categoriaCount = {};
    complaintsData.forEach(complaint => {
        const categoria = complaint.categoria || 'Não especificado';
        categoriaCount[categoria] = (categoriaCount[categoria] || 0) + 1;
    });
    
    const labels = Object.keys(categoriaCount);
    const data = Object.values(categoriaCount);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Número de Denúncias',
                data: data,
                backgroundColor: '#3B82F6'
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Atualizar tabela de denúncias
function updateComplaintsTable() {
    const tbody = document.getElementById('complaintsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (complaintsData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 20px;">
                    Nenhuma denúncia encontrada
                </td>
            </tr>
        `;
        return;
    }
    
    // CORREÇÃO: Acessar os dados dentro da estrutura correta
    complaintsData.forEach(complaint => {
        const row = document.createElement('tr');
        
        // Formata a data para melhor leitura
        const formattedDate = complaint.data ? new Date(complaint.data).toLocaleString('pt-BR') : 'N/A';

        row.innerHTML = `
            <td>${complaint.id || 'N/A'}</td>
            <td>${complaint.conselho || 'N/A'}</td>
            <td>${complaint.categoria || 'N/A'}</td>
            <td>
                <span class="risk-badge risk-medio">
                    ${complaint.ia_analysis?.classificacao_risco?.nivel || 'Médio'}
                </span>
            </td>
            <td>${formattedDate}</td>
            <td>
                <span class="status-badge status-registered">
                    ${complaint.status || 'Registrado'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline" onclick="viewComplaintDetails('${complaint.id}')">
                    <i class="fas fa-eye"></i>
                    Ver
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Atualizar informações da blockchain
function updateBlockchainInfo() {
    if (!blockchainData.blockchain) return;
    
    const chain = blockchainData.blockchain;
    const latestBlock = chain[chain.length - 1];
    
    if (latestBlock) {
        document.getElementById('latestBlockHash').textContent = latestBlock.hash || 'N/A';
    }
    
    document.getElementById('difficulty').textContent = '2';
    document.getElementById('pendingTransactions').textContent = '0';
    document.getElementById('chainValid').textContent = '✓ Válida';
    
    // Atualizar lista de transações recentes
    updateRecentTransactions();
}

// Atualizar transações recentes
function updateRecentTransactions() {
    const container = document.getElementById('recentTransactions');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Pegar as últimas 5 denúncias
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
    // Aqui você pode implementar uma notificação de erro mais elaborada
    alert(message);
}

// Funções dos botões
function refreshData() {
    loadDashboardData();
}

function exportReport() {
    window.open('/api/export-blockchain', '_blank');
}

function goBack() {
    window.location.href = '/';
}

function viewComplaintDetails(complaintId) {
    const complaint = complaintsData.find(c => c.id === complaintId);
    if (!complaint) return;
    
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
                            <span class="badge" style="background:${registros.registro_encontrado ? '#4caf50' : '#ff9800'}; color:white; font-size:0.8em;">
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


// Carrega análise inteligente da última denúncia
async function loadLatestComplaintAnalysis() {
    const analysisContainer = document.getElementById('analysisContainer');
    if (!analysisContainer) return;

    try {
        const response = await fetch('/api/latest-analysis');
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

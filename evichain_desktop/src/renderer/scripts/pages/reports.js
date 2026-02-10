/* ============================================================
   EviChain Desktop — Relatórios Page
   ============================================================ */

Router.register('reports', async (container) => {
    container.innerHTML = `
        ${Components.pageHeader('Relatórios', 'Gere relatórios e exporte dados do sistema')}

        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:16px">
            ${reportCard('complaint-pdf', '📋 Relatório de Denúncia',
                'Gere um PDF detalhado de uma denúncia específica, incluindo análise de IA e dados da blockchain.',
                'Selecionar denúncia e gerar PDF'
            )}
            ${reportCard('blockchain-pdf', '🔗 Relatório da Blockchain',
                'Exporte o estado completo da blockchain em PDF com todos os blocos e hashes.',
                'Gerar PDF da blockchain'
            )}
            ${reportCard('csv-export', '📊 Exportar CSV',
                'Exporte todas as denúncias em formato CSV para análise em planilhas.',
                'Exportar CSV'
            )}
            ${reportCard('audit-pdf', '📝 Relatório de Auditoria',
                'Gere um relatório com todo o log de auditoria do sistema.',
                'Gerar relatório'
            )}
        </div>

        <div id="report-output" style="margin-top:24px"></div>
    `;

    // Complaint PDF
    document.getElementById('btn-complaint-pdf')?.addEventListener('click', async () => {
        const output = document.getElementById('report-output');
        try {
            const list = await window.evichainAPI.complaints.list();
            if (!list.length) { Toast.show('Nenhuma denúncia para exportar.', 'warning'); return; }

            output.innerHTML = `
                <div class="card">
                    <div class="card-header"><h3>Selecionar Denúncia</h3></div>
                    <div class="card-body">
                        <select id="report-complaint-select" class="form-select" style="max-width:400px">
                            ${list.map(c => `<option value="${c.id}">#${c.id} - ${escapeHtml(truncate(c.titulo || c.descricao, 50))}</option>`).join('')}
                        </select>
                        <button class="btn btn-primary btn-sm" id="btn-gen-complaint-pdf" style="margin-top:8px">Gerar PDF</button>
                    </div>
                </div>
            `;

            document.getElementById('btn-gen-complaint-pdf')?.addEventListener('click', async () => {
                const id = document.getElementById('report-complaint-select').value;
                Toast.show('Gerando PDF…', 'info');
                try {
                    const res = await window.evichainAPI.reports.complaintPDF(id);
                    Toast.show('PDF gerado: ' + (res?.path?.split(/[/\\]/).pop() || ''), 'success');
                } catch (e) { Toast.show('Erro: ' + e.message, 'error'); }
            });
        } catch (e) { Toast.show('Erro: ' + e.message, 'error'); }
    });

    // Blockchain PDF
    document.getElementById('btn-blockchain-pdf')?.addEventListener('click', async () => {
        Toast.show('Gerando PDF da blockchain…', 'info');
        try {
            const res = await window.evichainAPI.reports.blockchainPDF();
            Toast.show('PDF gerado: ' + (res?.path?.split(/[/\\]/).pop() || ''), 'success');
        } catch (e) { Toast.show('Erro: ' + e.message, 'error'); }
    });

    // CSV Export
    document.getElementById('btn-csv-export')?.addEventListener('click', async () => {
        Toast.show('Exportando CSV…', 'info');
        try {
            const res = await window.evichainAPI.reports.exportCSV();
            Toast.show('CSV exportado: ' + (res?.path?.split(/[/\\]/).pop() || ''), 'success');
        } catch (e) { Toast.show('Erro: ' + e.message, 'error'); }
    });

    // Audit report
    document.getElementById('btn-audit-pdf')?.addEventListener('click', async () => {
        Toast.show('Este recurso será implementado em breve.', 'info');
    });
});

function reportCard(id, title, description, actionText) {
    return `
        <div class="card">
            <div class="card-body" style="display:flex;flex-direction:column;min-height:160px">
                <h3 style="font-size:15px;color:var(--text);margin-bottom:8px">${title}</h3>
                <p style="font-size:12px;color:var(--text-dim);flex:1">${description}</p>
                <button class="btn btn-primary btn-sm" id="btn-${id}" style="align-self:flex-start;margin-top:12px">
                    ${escapeHtml(actionText)}
                </button>
            </div>
        </div>
    `;
}

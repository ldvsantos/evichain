/* ============================================================
   EviChain Desktop — Blockchain Page
   ============================================================ */

Router.register('blockchain', async (container) => {
    container.innerHTML = Components.loading('Carregando blockchain…');

    try {
        const info = await window.evichainAPI.blockchain.info();

        container.innerHTML = `
            ${Components.pageHeader('Blockchain', 'Visualização da cadeia de evidências imutável')}

            <div class="stats-grid">
                ${Components.statCard({ label: 'Total de Blocos', value: info.totalBlocks || 0, icon: '🔗', color: 'var(--primary)' })}
                ${Components.statCard({ label: 'Chain Válida', value: info.isValid ? 'Sim ✓' : 'Não ✕', icon: info.isValid ? '🟢' : '🔴', color: info.isValid ? 'var(--success)' : 'var(--danger)' })}
                ${Components.statCard({ label: 'Dificuldade', value: info.difficulty || 4, icon: '⚙️', color: 'var(--accent)' })}
                ${Components.statCard({ label: 'Último Bloco', value: info.lastBlockTime ? formatDateShort(info.lastBlockTime) : '—', icon: '🕐', color: 'var(--text-muted)' })}
            </div>

            <div style="display:flex;gap:8px;margin:16px 0">
                <button class="btn btn-primary btn-sm" id="btn-validate-chain">🔍 Validar Chain</button>
                <button class="btn btn-secondary btn-sm" id="btn-export-chain">📥 Exportar PDF</button>
            </div>

            <div class="card">
                <div class="card-header"><h3>Blocos Recentes</h3></div>
                <div class="card-body">
                    <div class="blockchain-visual" id="blocks-list">
                        ${renderBlocks(info.recentBlocks || [])}
                    </div>
                </div>
            </div>
        `;

        // Validate
        document.getElementById('btn-validate-chain')?.addEventListener('click', async () => {
            Toast.show('Validando integridade da chain…', 'info');
            try {
                const result = await window.evichainAPI.blockchain.validate();
                if (result.valid) {
                    Toast.show(`Chain válida! ${result.totalBlocks} blocos verificados.`, 'success');
                } else {
                    Toast.show(`Chain INVÁLIDA! Problema no bloco ${result.invalidAt || '?'}.`, 'error');
                }
            } catch (e) { Toast.show('Erro: ' + e.message, 'error'); }
        });

        // Export PDF
        document.getElementById('btn-export-chain')?.addEventListener('click', async () => {
            try {
                const result = await window.evichainAPI.reports.blockchainPDF();
                if (result?.path) Toast.show('PDF exportado: ' + result.path.split(/[/\\]/).pop(), 'success');
            } catch (e) { Toast.show('Erro ao exportar: ' + e.message, 'error'); }
        });

    } catch (err) {
        container.innerHTML = Components.pageHeader('Blockchain') +
            `<div class="card" style="padding:20px;color:var(--danger)">Erro: ${escapeHtml(err.message)}</div>`;
    }
});

function renderBlocks(blocks) {
    if (!blocks.length) return '<p style="color:var(--text-dim);font-size:13px">Nenhum bloco encontrado.</p>';

    return blocks.map(b => `
        <div class="block-card">
            <div class="block-header">
                <span class="block-index">Bloco #${b.block_index ?? b.id ?? '?'}</span>
                <span class="block-time">${formatDate(b.timestamp || b.created_at)}</span>
            </div>
            <div class="block-hash-row">
                <span class="block-label">Hash</span>
                <span class="hash" title="${escapeHtml(b.hash || '')}">${escapeHtml((b.hash || '').substring(0, 32))}…</span>
            </div>
            <div class="block-hash-row">
                <span class="block-label">Prev Hash</span>
                <span class="hash" title="${escapeHtml(b.previous_hash || '')}">${escapeHtml((b.previous_hash || '').substring(0, 32))}…</span>
            </div>
            ${b.data ? `<div style="margin-top:8px;font-size:11px;color:var(--text-dim)">
                Dados: ${escapeHtml(truncate(typeof b.data === 'string' ? b.data : JSON.stringify(b.data), 100))}
            </div>` : ''}
        </div>
    `).join('');
}

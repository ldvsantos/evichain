/* ============================================================
   EviChain Desktop — Dashboard Page
   ============================================================ */

Router.register('dashboard', async (container) => {
    container.innerHTML = Components.loading('Carregando dashboard…');

    try {
        const stats = await window.evichainAPI.dashboard.stats();

        container.innerHTML = `
            ${Components.pageHeader('Dashboard', 'Visão geral do sistema EviChain')}

            <div class="stats-grid">
                ${Components.statCard({ label: 'Total Denúncias', value: stats.totalComplaints || 0, icon: '📋', color: 'var(--primary)' })}
                ${Components.statCard({ label: 'Pendentes', value: stats.pending || 0, icon: '⏳', color: 'var(--warning)' })}
                ${Components.statCard({ label: 'Concluídas', value: stats.completed || 0, icon: '✅', color: 'var(--success)' })}
                ${Components.statCard({ label: 'Blocos na Chain', value: stats.totalBlocks || 0, icon: '🔗', color: 'var(--accent)' })}
            </div>

            <div class="dashboard-grid">
                <div>
                    ${Components.card(renderRecentComplaints(stats.recentComplaints || []), { title: 'Denúncias Recentes' })}
                </div>
                <div>
                    ${Components.card(renderQuickActions(), { title: 'Ações Rápidas' })}
                    ${Components.card(renderChainStatus(stats), { title: 'Status da Blockchain' })}
                </div>
            </div>
        `;

        bindQuickActions();
    } catch (err) {
        container.innerHTML = Components.pageHeader('Dashboard') +
            `<div class="card" style="padding:20px;color:var(--danger)">Erro ao carregar dados: ${escapeHtml(err.message)}</div>`;
    }
});

function renderRecentComplaints(list) {
    if (!list.length) return '<p style="color:var(--text-dim);font-size:13px">Nenhuma denúncia registrada.</p>';

    return `<div class="recent-list">${list.slice(0, 8).map(c => `
        <div class="recent-item" data-id="${c.id}" style="cursor:pointer" title="Clique para ver detalhes">
            <div>
                <div style="font-size:13px;font-weight:500;color:var(--text)">${escapeHtml(truncate(c.titulo || c.descricao, 50))}</div>
                <div style="font-size:11px;color:var(--text-dim)">${formatDate(c.created_at)}</div>
            </div>
            <span class="badge badge-${badgeClass(c.status)}">${statusLabel(c.status)}</span>
        </div>
    `).join('')}</div>`;
}

function renderQuickActions() {
    return `<div class="quick-actions">
        <button class="quick-action-btn" data-action="new-complaint">📝 Nova Denúncia</button>
        <button class="quick-action-btn" data-action="blockchain">🔗 Ver Blockchain</button>
        <button class="quick-action-btn" data-action="investigator">🔍 Investigador</button>
        <button class="quick-action-btn" data-action="reports">📊 Relatórios</button>
    </div>`;
}

function renderChainStatus(stats) {
    const valid = stats.chainValid !== false;
    return `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
            <span style="font-size:18px">${valid ? '🟢' : '🔴'}</span>
            <span style="font-size:13px;color:${valid ? 'var(--success)' : 'var(--danger)'}">
                ${valid ? 'Chain íntegra' : 'Chain com problemas'}
            </span>
        </div>
        <div style="font-size:12px;color:var(--text-dim)">
            <div>Total de blocos: <strong style="color:var(--text)">${stats.totalBlocks || 0}</strong></div>
            ${stats.lastBlockTime ? `<div>Último bloco: <strong style="color:var(--text)">${formatDate(stats.lastBlockTime)}</strong></div>` : ''}
        </div>
    `;
}

function bindQuickActions() {
    document.querySelectorAll('.quick-action-btn[data-action]').forEach(btn => {
        btn.addEventListener('click', () => Router.navigate(btn.dataset.action));
    });
    document.querySelectorAll('.recent-item[data-id]').forEach(item => {
        item.addEventListener('click', () => Router.navigate('complaints', { id: item.dataset.id }));
    });
}

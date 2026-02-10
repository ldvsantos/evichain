/* ============================================================
   EviChain Desktop — Auditoria Page
   ============================================================ */

Router.register('audit', async (container) => {
    container.innerHTML = Components.loading('Carregando log de auditoria…');

    try {
        const logs = await window.evichainAPI.audit.log();

        container.innerHTML = `
            ${Components.pageHeader('Log de Auditoria', `${logs.length} registro(s)`)}

            ${Components.toolbar({
                placeholder: 'Buscar ação, usuário…',
                onSearch: term => filterAudit(term, logs)
            })}

            <div id="audit-content">
                ${renderAuditTable(logs)}
            </div>
        `;
    } catch (err) {
        container.innerHTML = Components.pageHeader('Auditoria') +
            `<div class="card" style="padding:20px;color:var(--danger)">Erro: ${escapeHtml(err.message)}</div>`;
    }
});

function renderAuditTable(logs) {
    if (!logs.length) {
        return '<div class="card" style="padding:20px"><p style="color:var(--text-dim)">Nenhum registro de auditoria.</p></div>';
    }

    return Components.table({
        columns: ['Data', 'Usuário', 'Ação', 'Detalhes'],
        rows: logs,
        renderRow: log => `
            <td style="font-size:11px;color:var(--text-dim);white-space:nowrap">${formatDate(log.created_at || log.timestamp)}</td>
            <td style="font-weight:500">${escapeHtml(log.username || log.user || '—')}</td>
            <td>${auditActionBadge(log.action || log.acao)}</td>
            <td style="font-size:12px;color:var(--text-dim);max-width:300px;overflow:hidden;text-overflow:ellipsis">
                ${escapeHtml(truncate(log.details || log.detalhes || '—', 80))}
            </td>
        `
    });
}

function auditActionBadge(action) {
    const colors = {
        'login': 'info', 'logout': 'secondary',
        'create_complaint': 'success', 'update_complaint': 'warning',
        'analyze': 'primary', 'investigate': 'primary',
        'backup_create': 'info', 'backup_restore': 'warning',
        'export': 'info', 'settings_update': 'secondary'
    };
    return Components.badge(action || '—', colors[action] || 'secondary');
}

function filterAudit(term, all) {
    const t = term.toLowerCase();
    const filtered = t
        ? all.filter(l =>
            (l.action || l.acao || '').toLowerCase().includes(t) ||
            (l.username || l.user || '').toLowerCase().includes(t) ||
            (l.details || l.detalhes || '').toLowerCase().includes(t)
        )
        : all;
    document.getElementById('audit-content').innerHTML = renderAuditTable(filtered);
}

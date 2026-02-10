/* ============================================================
   EviChain Desktop — Reusable Components
   ============================================================ */

const Components = (() => {

    /**
     * Gera uma tabela HTML
     * @param {Object} opts
     * @param {string[]} opts.columns - Cabeçalhos
     * @param {Array} opts.rows - Dados (array de arrays ou objetos)
     * @param {Function} [opts.renderRow] - fn(row) => HTML string de <td>s
     * @param {string} [opts.emptyText] - Texto quando vazio
     */
    function table({ columns = [], rows = [], renderRow, emptyText = 'Nenhum registro encontrado.' }) {
        if (!rows.length) {
            return `<div class="empty-state"><p>${escapeHtml(emptyText)}</p></div>`;
        }

        const header = columns.map(c => `<th>${escapeHtml(c)}</th>`).join('');
        const body = rows.map(row => {
            const cells = renderRow
                ? renderRow(row)
                : Object.values(row).map(v => `<td>${escapeHtml(String(v ?? ''))}</td>`).join('');
            return `<tr>${cells}</tr>`;
        }).join('');

        return `
            <div class="table-wrapper">
                <table>
                    <thead><tr>${header}</tr></thead>
                    <tbody>${body}</tbody>
                </table>
            </div>
        `;
    }

    /**
     * Toolbar com busca e botão de ação
     */
    function toolbar({ placeholder = 'Buscar…', onSearch, actionLabel, actionIcon, onAction }) {
        const id = 'toolbar-search-' + Date.now();
        const html = `
            <div class="toolbar">
                <div class="toolbar-search">
                    <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
                    <input type="text" id="${id}" placeholder="${escapeHtml(placeholder)}">
                </div>
                ${actionLabel ? `<button class="btn btn-primary" id="${id}-action">
                    ${actionIcon || ''}${escapeHtml(actionLabel)}
                </button>` : ''}
            </div>
        `;

        // Bind events after DOM update
        setTimeout(() => {
            const input = document.getElementById(id);
            if (input && onSearch) {
                let timer;
                input.addEventListener('input', () => {
                    clearTimeout(timer);
                    timer = setTimeout(() => onSearch(input.value), 300);
                });
            }
            const btn = document.getElementById(`${id}-action`);
            if (btn && onAction) btn.addEventListener('click', onAction);
        }, 50);

        return html;
    }

    /**
     * Stat card para dashboards
     */
    function statCard({ label, value, icon, color }) {
        return `
            <div class="stat-card">
                <div class="stat-icon" style="color:${color || 'var(--primary)'}">
                    ${icon || '📊'}
                </div>
                <div class="stat-info">
                    <span class="stat-value">${escapeHtml(String(value ?? 0))}</span>
                    <span class="stat-label">${escapeHtml(label)}</span>
                </div>
            </div>
        `;
    }

    /**
     * Badge
     */
    function badge(text, type = 'secondary') {
        return `<span class="badge badge-${type}">${escapeHtml(text)}</span>`;
    }

    /**
     * Card wrapper
     */
    function card(content, { title, actions } = {}) {
        return `
            <div class="card">
                ${title ? `<div class="card-header">
                    <h3>${escapeHtml(title)}</h3>
                    ${actions || ''}
                </div>` : ''}
                <div class="card-body">${content}</div>
            </div>
        `;
    }

    /**
     * Page header
     */
    function pageHeader(title, subtitle) {
        return `
            <div class="page-header">
                <h2>${escapeHtml(title)}</h2>
                ${subtitle ? `<p>${escapeHtml(subtitle)}</p>` : ''}
            </div>
        `;
    }

    /**
     * Loading spinner
     */
    function loading(text = 'Carregando…') {
        return `<div class="loading-state"><div class="spinner"></div><span>${escapeHtml(text)}</span></div>`;
    }

    return { table, toolbar, statCard, badge, card, pageHeader, loading };
})();

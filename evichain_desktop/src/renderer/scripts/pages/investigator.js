/* ============================================================
   EviChain Desktop — Investigador Digital Page
   ============================================================ */

Router.register('investigator', async (container, params) => {
    container.innerHTML = `
        ${Components.pageHeader('Investigador Digital', 'Pesquise registros profissionais e presença digital')}

        <div class="card investigator-form">
            <div class="card-body">
                <div class="form-row" style="display:grid;grid-template-columns:2fr 1fr;gap:16px">
                    <div class="form-group">
                        <label class="form-label">Nome do Profissional</label>
                        <input type="text" id="inv-nome" class="form-input" placeholder="Nome completo"
                            value="${escapeHtml(params?.name || '')}">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Conselho</label>
                        <select id="inv-conselho" class="form-select">
                            <option value="">Todos</option>
                            <option value="CRM" ${params?.conselho === 'CRM' ? 'selected' : ''}>CRM</option>
                            <option value="OAB" ${params?.conselho === 'OAB' ? 'selected' : ''}>OAB</option>
                            <option value="CREA" ${params?.conselho === 'CREA' ? 'selected' : ''}>CREA</option>
                            <option value="CRP" ${params?.conselho === 'CRP' ? 'selected' : ''}>CRP</option>
                            <option value="CRO" ${params?.conselho === 'CRO' ? 'selected' : ''}>CRO</option>
                            <option value="CREF" ${params?.conselho === 'CREF' ? 'selected' : ''}>CREF</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">Número de Registro (opcional)</label>
                    <input type="text" id="inv-registro" class="form-input" placeholder="Ex: CRM 12345/SP">
                </div>
                <button class="btn btn-primary" id="btn-investigar">🔍 Investigar</button>
            </div>
        </div>

        <div id="inv-results" class="investigator-results"></div>
    `;

    document.getElementById('btn-investigar')?.addEventListener('click', runInvestigation);

    // Auto-run if params provided
    if (params?.name) {
        setTimeout(runInvestigation, 100);
    }
});

async function runInvestigation() {
    const nome = document.getElementById('inv-nome')?.value?.trim();
    const conselho = document.getElementById('inv-conselho')?.value;
    const registro = document.getElementById('inv-registro')?.value?.trim();

    if (!nome) {
        Toast.show('Informe o nome do profissional.', 'warning');
        return;
    }

    const resultsEl = document.getElementById('inv-results');
    resultsEl.innerHTML = Components.loading('Investigando…');

    try {
        const [investigation, socialResults] = await Promise.all([
            window.evichainAPI.investigation.start(nome, registro, conselho),
            window.evichainAPI.investigation.searchSocial(nome)
        ]);

        resultsEl.innerHTML = `
            <div class="results-tabs">
                <button class="results-tab active" data-tab="registros">📋 Registros</button>
                <button class="results-tab" data-tab="social">🌐 Redes Sociais</button>
                <button class="results-tab" data-tab="links">🔗 Links Úteis</button>
            </div>

            <div class="results-panel active" id="panel-registros">
                ${renderRegistros(investigation)}
            </div>

            <div class="results-panel" id="panel-social">
                ${renderSocial(socialResults)}
            </div>

            <div class="results-panel" id="panel-links">
                ${renderLinks(investigation, nome, conselho)}
            </div>
        `;

        // Tab switching
        resultsEl.querySelectorAll('.results-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                resultsEl.querySelectorAll('.results-tab').forEach(t => t.classList.remove('active'));
                resultsEl.querySelectorAll('.results-panel').forEach(p => p.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(`panel-${tab.dataset.tab}`)?.classList.add('active');
            });
        });

        Toast.show('Investigação concluída!', 'success');
    } catch (err) {
        resultsEl.innerHTML = `<div class="card" style="padding:16px;color:var(--danger)">Erro: ${escapeHtml(err.message)}</div>`;
    }
}

function renderRegistros(inv) {
    if (!inv?.registros?.length && !inv?.conselho) {
        return `<p style="color:var(--text-dim);font-size:13px">Nenhum registro encontrado. Verifique diretamente nos portais oficiais.</p>`;
    }

    const items = inv.registros || [];
    let html = '';

    if (inv.conselho) {
        html += `<div class="card" style="margin-bottom:12px;border-left:3px solid var(--primary)">
            <div class="card-body">
                <div style="font-size:13px;font-weight:500;color:var(--text)">Conselho: ${escapeHtml(inv.conselho)}</div>
                ${inv.portalUrl ? `<a href="${inv.portalUrl}" target="_blank" style="font-size:12px;color:var(--primary)">
                    Consultar portal oficial →
                </a>` : ''}
            </div>
        </div>`;
    }

    if (items.length) {
        html += Components.table({
            columns: ['Fonte', 'Registro', 'Status', 'Detalhes'],
            rows: items,
            renderRow: r => `
                <td>${escapeHtml(r.fonte || '—')}</td>
                <td><span class="hash">${escapeHtml(r.registro || '—')}</span></td>
                <td>${Components.badge(r.status || '—', r.status === 'Ativo' ? 'success' : 'warning')}</td>
                <td style="font-size:12px">${escapeHtml(r.detalhes || '—')}</td>
            `
        });
    }

    return html || '<p style="color:var(--text-dim)">Consulte os portais oficiais para informações atualizadas.</p>';
}

function renderSocial(results) {
    if (!results?.platforms?.length) {
        return '<p style="color:var(--text-dim);font-size:13px">Nenhuma rede social encontrada.</p>';
    }

    return `<div class="social-grid">
        ${results.platforms.map(p => `
            <div class="social-card">
                <h4>${escapeHtml(p.name || p.platform)}</h4>
                ${p.links?.map(link => `
                    <div class="social-link">
                        <a href="${escapeHtml(link.url)}" target="_blank">${escapeHtml(link.label || link.url)}</a>
                    </div>
                `).join('') || '<div style="font-size:12px;color:var(--text-dim)">Sem resultados</div>'}
            </div>
        `).join('')}
    </div>`;
}

function renderLinks(inv, nome, conselho) {
    const portals = [
        { name: 'CRM (Medicina)', url: 'https://portal.cfm.org.br/' },
        { name: 'OAB (Advocacia)', url: 'https://cna.oab.org.br/' },
        { name: 'CREA (Engenharia)', url: 'https://www.confea.org.br/' },
        { name: 'CRP (Psicologia)', url: 'https://www.cfp.org.br/' },
        { name: 'CRO (Odontologia)', url: 'https://cfo.org.br/' },
        { name: 'CREF/CONFEF (Ed. Física)', url: 'https://www.confef.org.br/' }
    ];

    const searchEngines = [
        { name: 'Google', url: `https://www.google.com/search?q=${encodeURIComponent(nome + ' ' + (conselho || ''))}` },
        { name: 'Jusbrasil', url: `https://www.jusbrasil.com.br/busca?q=${encodeURIComponent(nome)}` },
        { name: 'Escavador', url: `https://www.escavador.com/sobre/${encodeURIComponent(nome)}` }
    ];

    return `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div>
                <h4 style="font-size:13px;color:var(--text);margin-bottom:8px">Portais de Conselhos</h4>
                ${portals.map(p => `
                    <div class="social-link">
                        <a href="${p.url}" target="_blank">${escapeHtml(p.name)}</a>
                    </div>
                `).join('')}
            </div>
            <div>
                <h4 style="font-size:13px;color:var(--text);margin-bottom:8px">Buscadores</h4>
                ${searchEngines.map(s => `
                    <div class="social-link">
                        <a href="${s.url}" target="_blank">${escapeHtml(s.name)}: "${escapeHtml(nome)}"</a>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

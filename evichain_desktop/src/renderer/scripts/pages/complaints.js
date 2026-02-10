/* ============================================================
   EviChain Desktop — Complaints Page (Listagem / Detalhes)
   ============================================================ */

Router.register('complaints', async (container, params) => {
    if (params?.id) {
        await renderDetail(container, params.id);
    } else {
        await renderList(container);
    }
});

/* ── Lista de Denúncias ────────────────────────────────── */
async function renderList(container) {
    container.innerHTML = Components.loading();

    const complaints = await window.evichainAPI.complaints.list();

    container.innerHTML = `
        ${Components.pageHeader('Denúncias', `${complaints.length} registro(s)`)}
        ${Components.toolbar({
            placeholder: 'Buscar denúncia…',
            onSearch: term => filterComplaints(term, complaints),
            actionLabel: 'Nova Denúncia',
            onAction: () => Router.navigate('new-complaint')
        })}
        <div id="complaints-table">
            ${renderComplaintsTable(complaints)}
        </div>
    `;
}

function renderComplaintsTable(list) {
    return Components.table({
        columns: ['#', 'Título / Descrição', 'Denunciado', 'Conselho', 'Status', 'Data', 'Ações'],
        rows: list,
        renderRow: c => `
            <td style="color:var(--text-dim)">${c.id}</td>
            <td>${escapeHtml(truncate(c.titulo || c.descricao, 45))}</td>
            <td>${escapeHtml(c.denunciado || '—')}</td>
            <td>${escapeHtml(c.conselho || '—')}</td>
            <td>${Components.badge(statusLabel(c.status), badgeClass(c.status))}</td>
            <td style="font-size:11px;color:var(--text-dim)">${formatDateShort(c.created_at)}</td>
            <td>
                <button class="btn btn-ghost btn-sm" onclick="Router.navigate('complaints', {id:'${c.id}'})">Ver</button>
            </td>
        `,
        emptyText: 'Nenhuma denúncia registrada.'
    });
}

function filterComplaints(term, all) {
    const t = term.toLowerCase();
    const filtered = t
        ? all.filter(c =>
            (c.titulo || '').toLowerCase().includes(t) ||
            (c.descricao || '').toLowerCase().includes(t) ||
            (c.denunciado || '').toLowerCase().includes(t) ||
            (c.conselho || '').toLowerCase().includes(t)
        )
        : all;
    document.getElementById('complaints-table').innerHTML = renderComplaintsTable(filtered);
}

/* ── Detalhe da Denúncia ───────────────────────────────── */
async function renderDetail(container, id) {
    container.innerHTML = Components.loading();

    try {
        const c = await window.evichainAPI.complaints.get(id);
        if (!c) {
            container.innerHTML = Components.pageHeader('Denúncia não encontrada');
            return;
        }

        container.innerHTML = `
            ${Components.pageHeader(`Denúncia #${c.id}`,
                `Criada em ${formatDate(c.created_at)}`
            )}

            <button class="btn btn-secondary btn-sm" onclick="Router.navigate('complaints')" style="margin-bottom:16px">
                ← Voltar à lista
            </button>

            <div style="display:grid;grid-template-columns:2fr 1fr;gap:20px">
                <div>
                    ${Components.card(`
                        <div style="margin-bottom:12px">
                            <label style="font-size:11px;color:var(--text-dim)">Título</label>
                            <div style="color:var(--text);font-weight:500">${escapeHtml(c.titulo || '—')}</div>
                        </div>
                        <div style="margin-bottom:12px">
                            <label style="font-size:11px;color:var(--text-dim)">Descrição</label>
                            <div style="color:var(--text);white-space:pre-wrap;font-size:13px">${escapeHtml(c.descricao || '—')}</div>
                        </div>
                        ${c.evidencias ? `<div style="margin-bottom:12px">
                            <label style="font-size:11px;color:var(--text-dim)">Evidências</label>
                            <div style="color:var(--text);font-size:13px;white-space:pre-wrap">${escapeHtml(c.evidencias)}</div>
                        </div>` : ''}
                    `, { title: 'Informações' })}

                    ${c.analise_ia ? renderAnalysis(c.analise_ia) : ''}
                </div>

                <div>
                    ${Components.card(`
                        <div class="detail-field"><span>Status</span>${Components.badge(statusLabel(c.status), badgeClass(c.status))}</div>
                        <div class="detail-field"><span>Denunciado</span><strong>${escapeHtml(c.denunciado || '—')}</strong></div>
                        <div class="detail-field"><span>Conselho</span><strong>${escapeHtml(c.conselho || '—')}</strong></div>
                        <div class="detail-field"><span>Risco</span>
                            <span style="color:${riskColor(c.risco || 0)};font-weight:600">${c.risco || 0}%</span>
                        </div>
                        ${c.block_hash ? `<div class="detail-field">
                            <span>Hash Blockchain</span>
                            <span class="hash" title="${c.block_hash}">${c.block_hash.substring(0, 16)}…</span>
                        </div>` : ''}
                    `, { title: 'Metadados' })}

                    ${Components.card(`
                        <div style="display:flex;flex-direction:column;gap:6px">
                            <button class="btn btn-primary btn-block btn-sm" id="btn-analyze-${c.id}">🤖 Analisar com IA</button>
                            <button class="btn btn-secondary btn-block btn-sm" id="btn-investigate-${c.id}">🔍 Investigar</button>
                            <select id="status-select-${c.id}" class="form-select" style="margin-top:8px">
                                ${['pendente','em_analise','investigando','concluida','arquivada'].map(s =>
                                    `<option value="${s}" ${c.status===s?'selected':''}>${statusLabel(s)}</option>`
                                ).join('')}
                            </select>
                            <button class="btn btn-success btn-block btn-sm" id="btn-save-status-${c.id}">Salvar Status</button>
                        </div>
                    `, { title: 'Ações' })}
                </div>
            </div>
        `;

        // Bind actions
        document.getElementById(`btn-analyze-${c.id}`)?.addEventListener('click', async () => {
            Toast.show('Analisando com IA…', 'info');
            try {
                const result = await window.evichainAPI.analysis.analyze(c.id, c.descricao + ' ' + (c.evidencias || ''), c.conselho, null);
                Toast.show('Análise concluída!', 'success');
                Router.navigate('complaints', { id: c.id });
            } catch (e) { Toast.show('Erro na análise: ' + e.message, 'error'); }
        });

        document.getElementById(`btn-investigate-${c.id}`)?.addEventListener('click', () => {
            Router.navigate('investigator', { name: c.denunciado, conselho: c.conselho });
        });

        document.getElementById(`btn-save-status-${c.id}`)?.addEventListener('click', async () => {
            const newStatus = document.getElementById(`status-select-${c.id}`).value;
            try {
                await window.evichainAPI.complaints.updateStatus(c.id, newStatus);
                Toast.show('Status atualizado!', 'success');
            } catch (e) { Toast.show('Erro: ' + e.message, 'error'); }
        });

    } catch (err) {
        container.innerHTML = `<div class="card" style="padding:20px;color:var(--danger)">Erro: ${escapeHtml(err.message)}</div>`;
    }
}

function renderAnalysis(raw) {
    let data;
    try { data = typeof raw === 'string' ? JSON.parse(raw) : raw; } catch { return ''; }

    return Components.card(`
        <div class="analysis-box" style="border:none;padding:0">
            <div class="analysis-score">
                <div class="score-circle" style="background:${riskColor(data.risco || 0)}">${data.risco || 0}</div>
                <div>
                    <div style="font-size:14px;font-weight:600;color:var(--text)">Risco: ${data.gravidade || '—'}</div>
                    ${data.tipificacao ? `<div style="font-size:12px;color:var(--text-dim)">Tipificação: ${escapeHtml(data.tipificacao)}</div>` : ''}
                </div>
            </div>
            ${data.palavras_chave?.length ? `
                <div style="margin-bottom:12px">
                    <label style="font-size:11px;color:var(--text-dim)">Palavras-chave</label>
                    <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px">
                        ${data.palavras_chave.map(w => `<span class="badge badge-info">${escapeHtml(w)}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
            ${data.recomendacoes?.length ? `
                <div>
                    <label style="font-size:11px;color:var(--text-dim)">Recomendações</label>
                    <ul class="suggestion-list">${data.recomendacoes.map(r => `<li>${escapeHtml(r)}</li>`).join('')}</ul>
                </div>
            ` : ''}
        </div>
    `, { title: '🤖 Análise de IA' });
}

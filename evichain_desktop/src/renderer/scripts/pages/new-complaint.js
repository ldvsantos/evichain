/* ============================================================
   EviChain Desktop — Nova Denúncia Page
   ============================================================ */

Router.register('new-complaint', async (container) => {
    container.innerHTML = `
        ${Components.pageHeader('Nova Denúncia', 'Registre uma nova denúncia com evidências')}

        <div class="card" style="max-width:800px">
            <div class="card-body">
                <form id="complaint-form">
                    <div class="form-group">
                        <label class="form-label">Título da Denúncia *</label>
                        <input type="text" id="cf-titulo" class="form-input" placeholder="Resumo breve da denúncia" required>
                    </div>

                    <div class="form-row" style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
                        <div class="form-group">
                            <label class="form-label">Nome do Denunciado</label>
                            <input type="text" id="cf-denunciado" class="form-input" placeholder="Nome completo">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Conselho Profissional</label>
                            <select id="cf-conselho" class="form-select">
                                <option value="">Selecione…</option>
                                <option value="CRM">CRM — Medicina</option>
                                <option value="OAB">OAB — Advocacia</option>
                                <option value="CREA">CREA — Engenharia</option>
                                <option value="CRP">CRP — Psicologia</option>
                                <option value="CRO">CRO — Odontologia</option>
                                <option value="CREF">CREF — Educação Física</option>
                                <option value="CRC">CRC — Contabilidade</option>
                                <option value="COREN">COREN — Enfermagem</option>
                                <option value="CRN">CRN — Nutrição</option>
                                <option value="OUTRO">Outro</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Descrição Detalhada *</label>
                        <textarea id="cf-descricao" class="form-input" rows="6"
                            placeholder="Descreva os fatos com o máximo de detalhes possível…" required></textarea>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Evidências</label>
                        <textarea id="cf-evidencias" class="form-input" rows="3"
                            placeholder="Links, números de documentos, testemunhas, etc."></textarea>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Anexar Arquivo(s)</label>
                        <button type="button" class="btn btn-secondary btn-sm" id="btn-attach">
                            📎 Selecionar Arquivos
                        </button>
                        <div id="attachments-list" style="margin-top:8px;font-size:12px;color:var(--text-dim)"></div>
                    </div>

                    <div id="analysis-preview" style="display:none;margin-bottom:16px"></div>

                    <div style="display:flex;gap:8px;margin-top:16px">
                        <button type="button" class="btn btn-secondary" id="btn-analyze-text">
                            🤖 Pré-analisar com IA
                        </button>
                        <button type="submit" class="btn btn-primary">
                            📋 Registrar Denúncia
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;

    let attachedFiles = [];

    // Attach files
    document.getElementById('btn-attach')?.addEventListener('click', async () => {
        try {
            const result = await window.evichainAPI.dialog.openFile({
                title: 'Selecionar evidências',
                filters: [
                    { name: 'Documentos', extensions: ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'] },
                    { name: 'Todos', extensions: ['*'] }
                ],
                multiple: true
            });
            if (result?.filePaths?.length) {
                attachedFiles = result.filePaths;
                document.getElementById('attachments-list').innerHTML =
                    attachedFiles.map(f => `<div>📎 ${escapeHtml(f.split(/[/\\]/).pop())}</div>`).join('');
            }
        } catch (e) { console.log('[NewComplaint] Dialog error:', e); }
    });

    // Pre-analyze
    document.getElementById('btn-analyze-text')?.addEventListener('click', async () => {
        const desc = document.getElementById('cf-descricao').value;
        if (!desc || desc.length < 20) {
            Toast.show('Insira pelo menos 20 caracteres na descrição.', 'warning');
            return;
        }

        Toast.show('Analisando texto…', 'info');
        try {
            const result = await window.evichainAPI.analysis.analyze(null, desc, document.getElementById('cf-conselho')?.value || '', null);
            const preview = document.getElementById('analysis-preview');
            preview.style.display = 'block';
            preview.innerHTML = `
                <div class="analysis-box">
                    <h4 style="font-size:13px;color:var(--text);margin-bottom:12px">🤖 Pré-Análise de IA</h4>
                    <div class="analysis-score">
                        <div class="score-circle" style="background:${riskColor(result.risco || 0)}">${result.risco || 0}</div>
                        <div>
                            <div style="font-size:13px;font-weight:500;color:var(--text)">Gravidade: ${escapeHtml(result.gravidade || '—')}</div>
                            ${result.tipificacao ? `<div style="font-size:11px;color:var(--text-dim)">${escapeHtml(result.tipificacao)}</div>` : ''}
                        </div>
                    </div>
                    ${result.palavras_chave?.length ? `
                        <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:8px">
                            ${result.palavras_chave.map(w => `<span class="badge badge-info">${escapeHtml(w)}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
            Toast.show('Análise concluída!', 'success');
        } catch (e) { Toast.show('Erro na análise: ' + e.message, 'error'); }
    });

    // Submit form
    document.getElementById('complaint-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();

        const titulo = document.getElementById('cf-titulo').value.trim();
        const descricao = document.getElementById('cf-descricao').value.trim();
        const denunciado = document.getElementById('cf-denunciado').value.trim();
        const conselho = document.getElementById('cf-conselho').value;
        const evidencias = document.getElementById('cf-evidencias').value.trim();

        if (!titulo || !descricao) {
            Toast.show('Preencha o título e a descrição.', 'warning');
            return;
        }

        try {
            Toast.show('Registrando denúncia na blockchain…', 'info');
            const result = await window.evichainAPI.complaints.create({
                titulo, descricao, denunciado, conselho, evidencias,
                arquivos: attachedFiles
            });

            Toast.show('Denúncia registrada com sucesso! Hash: ' + (result.block_hash || '').substring(0, 12) + '…', 'success');
            Router.navigate('complaints', { id: result.id });
        } catch (err) {
            Toast.show('Erro ao registrar: ' + err.message, 'error');
        }
    });
});

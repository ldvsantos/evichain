/* ============================================================
   EviChain Desktop — Configurações Page
   ============================================================ */

Router.register('settings', async (container) => {
    container.innerHTML = Components.loading('Carregando configurações…');

    try {
        const settings = await window.evichainAPI.settings.get();

        container.innerHTML = `
            ${Components.pageHeader('Configurações', 'Ajuste o comportamento do sistema')}

            <form id="settings-form" style="max-width:700px">
                <div class="settings-section">
                    <h3>⚙️ Geral</h3>
                    <div class="form-group">
                        <label class="form-label">Nome da Instituição</label>
                        <input type="text" id="set-institution" class="form-input"
                            value="${escapeHtml(settings.institution || 'EviChain')}">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Dificuldade da Blockchain (Proof-of-Work)</label>
                        <select id="set-difficulty" class="form-select">
                            ${[2, 3, 4, 5, 6].map(d =>
                                `<option value="${d}" ${(settings.difficulty || 4) == d ? 'selected' : ''}>${d} ${d === 4 ? '(padrão)' : ''}</option>`
                            ).join('')}
                        </select>
                        <small style="color:var(--text-dim);font-size:11px">Valores maiores = mais seguro, porém mais lento</small>
                    </div>
                </div>

                <div class="settings-section">
                    <h3>🤖 Análise de IA</h3>
                    <div class="form-group">
                        <label class="form-label">Motor de Análise</label>
                        <select id="set-ai-engine" class="form-select">
                            <option value="local" ${settings.aiEngine !== 'openai' ? 'selected' : ''}>Local (sem internet)</option>
                            <option value="openai" ${settings.aiEngine === 'openai' ? 'selected' : ''}>OpenAI (requer API key)</option>
                        </select>
                    </div>
                    <div class="form-group" id="api-key-group" style="display:${settings.aiEngine === 'openai' ? 'block' : 'none'}">
                        <label class="form-label">OpenAI API Key</label>
                        <input type="password" id="set-api-key" class="form-input"
                            value="${escapeHtml(settings.openaiKey || '')}" placeholder="sk-…">
                    </div>
                </div>

                <div class="settings-section">
                    <h3>🔔 Notificações</h3>
                    <div class="form-group" style="display:flex;align-items:center;gap:8px">
                        <input type="checkbox" id="set-notifications" ${settings.notifications !== false ? 'checked' : ''}>
                        <label class="form-label" for="set-notifications" style="margin:0">Exibir notificações do sistema</label>
                    </div>
                </div>

                <div class="settings-section">
                    <h3>📂 Dados</h3>
                    <div class="form-group">
                        <label class="form-label">Diretório de exportações</label>
                        <div style="display:flex;gap:8px">
                            <input type="text" id="set-export-dir" class="form-input" readonly
                                value="${escapeHtml(settings.exportDir || 'Padrão (Documentos)')}">
                            <button type="button" class="btn btn-secondary btn-sm" id="btn-choose-dir">📁</button>
                        </div>
                    </div>
                </div>

                <div class="settings-section">
                    <h3>🌐 Servidor &amp; Sincronização</h3>
                    <div class="form-group">
                        <label class="form-label">URL do Servidor API</label>
                        <input type="text" id="set-server-url" class="form-input"
                            value="${escapeHtml(settings.api_server_url || 'http://localhost:5000')}"
                            placeholder="http://3.15.2.17 ou http://localhost:5000">
                        <small style="color:var(--text-dim);font-size:11px">Endereço do servidor EC2 para sincronizar denúncias</small>
                    </div>
                    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
                        <button type="button" class="btn btn-secondary btn-sm" id="btn-check-server">
                            🔗 Testar Conexão
                        </button>
                        <button type="button" class="btn btn-primary btn-sm" id="btn-sync-full">
                            🔄 Sincronizar Agora
                        </button>
                        <button type="button" class="btn btn-secondary btn-sm" id="btn-sync-pull">
                            ⬇️ Apenas Baixar
                        </button>
                        <button type="button" class="btn btn-secondary btn-sm" id="btn-sync-push">
                            ⬆️ Apenas Enviar
                        </button>
                    </div>
                    <div id="sync-status" style="margin-top:12px;font-size:12px;color:var(--text-dim)"></div>
                </div>

                <div style="display:flex;gap:8px;margin-top:16px">
                    <button type="submit" class="btn btn-primary">💾 Salvar Configurações</button>
                    <button type="button" class="btn btn-secondary" id="btn-reset-settings">Restaurar Padrões</button>
                </div>
            </form>

            <div class="settings-section" style="margin-top:24px;max-width:700px">
                <h3>ℹ️ Sobre</h3>
                <div style="font-size:12px;color:var(--text-dim);line-height:1.8">
                    <div><strong style="color:var(--text)">EviChain Desktop</strong> — Plataforma de evidências em blockchain</div>
                    <div>Versão: 1.0.0</div>
                    <div>Electron + SQLite + Blockchain SHA-256</div>
                    <div>© 2024 EviChain</div>
                </div>
            </div>
        `;

        // Toggle API key field
        document.getElementById('set-ai-engine')?.addEventListener('change', (e) => {
            document.getElementById('api-key-group').style.display = e.target.value === 'openai' ? 'block' : 'none';
        });

        // Choose dir
        document.getElementById('btn-choose-dir')?.addEventListener('click', async () => {
            try {
                const result = await window.evichainAPI.dialog.openFile({ title: 'Selecionar diretório de exportações', properties: ['openDirectory'] });
                if (result?.filePaths?.[0]) {
                    document.getElementById('set-export-dir').value = result.filePaths[0];
                }
            } catch (_) { }
        });

        // Save
        document.getElementById('settings-form')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                await window.evichainAPI.settings.update({
                    institution: document.getElementById('set-institution').value.trim(),
                    difficulty: parseInt(document.getElementById('set-difficulty').value),
                    aiEngine: document.getElementById('set-ai-engine').value,
                    openaiKey: document.getElementById('set-api-key')?.value?.trim() || '',
                    notifications: document.getElementById('set-notifications').checked,
                    exportDir: document.getElementById('set-export-dir').value,
                    api_server_url: document.getElementById('set-server-url')?.value?.trim() || 'http://localhost:5000'
                });
                Toast.show('Configurações salvas!', 'success');
            } catch (err) { Toast.show('Erro: ' + err.message, 'error'); }
        });

        // ── Sync handlers ────────────────────────────────────
        // Mostrar últimas info de sync
        try {
            const syncStatus = await window.evichainAPI.sync.status();
            const statusDiv = document.getElementById('sync-status');
            if (statusDiv && syncStatus.lastSync) {
                statusDiv.innerHTML = `<strong>Última sync:</strong> ${new Date(syncStatus.lastSync).toLocaleString('pt-BR')} — Servidor: ${escapeHtml(syncStatus.serverUrl)}`;
            }
        } catch (_) {}

        // Testar conexão
        document.getElementById('btn-check-server')?.addEventListener('click', async () => {
            const statusDiv = document.getElementById('sync-status');
            statusDiv.innerHTML = '🔄 Testando conexão...';
            // Salvar URL primeiro
            const url = document.getElementById('set-server-url')?.value?.trim();
            if (url) await window.evichainAPI.settings.update({ api_server_url: url });
            try {
                const result = await window.evichainAPI.sync.checkConnection();
                if (result.success) {
                    statusDiv.innerHTML = `✅ Conexão OK com <strong>${escapeHtml(result.server)}</strong> — Blocos: ${result.status?.total_blocks ?? '?'}`;
                    Toast.show('Servidor acessível!', 'success');
                } else {
                    statusDiv.innerHTML = `❌ Falha: ${escapeHtml(result.error)}`;
                    Toast.show('Servidor inacessível', 'error');
                }
            } catch (err) {
                statusDiv.innerHTML = `❌ Erro: ${escapeHtml(err.message)}`;
            }
        });

        // Sync Full
        document.getElementById('btn-sync-full')?.addEventListener('click', async () => {
            const statusDiv = document.getElementById('sync-status');
            const btn = document.getElementById('btn-sync-full');
            btn.disabled = true;
            btn.innerHTML = '🔄 Sincronizando...';
            statusDiv.innerHTML = '🔄 Sincronização bidirecional em andamento...';
            try {
                const url = document.getElementById('set-server-url')?.value?.trim();
                if (url) await window.evichainAPI.settings.update({ api_server_url: url });
                const result = await window.evichainAPI.sync.full();
                if (result.success) {
                    statusDiv.innerHTML = `✅ Sync completa — Pull: ${result.pull.imported} importadas, ${result.pull.updated} atualizadas | Push: ${result.push.pushed} enviadas${result.push.errors ? ' (' + result.push.errors.length + ' erros)' : ''}`;
                    Toast.show(`Sincronização concluída! ${result.pull.imported + result.push.pushed} registros sincronizados`, 'success');
                } else {
                    statusDiv.innerHTML = `❌ ${escapeHtml(result.error)}`;
                    Toast.show('Erro na sincronização: ' + result.error, 'error');
                }
            } catch (err) {
                statusDiv.innerHTML = `❌ ${escapeHtml(err.message)}`;
                Toast.show('Erro: ' + err.message, 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '🔄 Sincronizar Agora';
            }
        });

        // Sync Pull
        document.getElementById('btn-sync-pull')?.addEventListener('click', async () => {
            const statusDiv = document.getElementById('sync-status');
            statusDiv.innerHTML = '⬇️ Baixando do servidor...';
            try {
                const url = document.getElementById('set-server-url')?.value?.trim();
                if (url) await window.evichainAPI.settings.update({ api_server_url: url });
                const result = await window.evichainAPI.sync.pull();
                if (result.success) {
                    statusDiv.innerHTML = `✅ Pull: ${result.imported} importadas, ${result.updated} atualizadas (total no servidor: ${result.serverTotal})`;
                    Toast.show(`${result.imported} denúncias importadas do servidor`, 'success');
                } else {
                    statusDiv.innerHTML = `❌ ${escapeHtml(result.error)}`;
                }
            } catch (err) { statusDiv.innerHTML = `❌ ${escapeHtml(err.message)}`; }
        });

        // Sync Push
        document.getElementById('btn-sync-push')?.addEventListener('click', async () => {
            const statusDiv = document.getElementById('sync-status');
            statusDiv.innerHTML = '⬆️ Enviando para o servidor...';
            try {
                const url = document.getElementById('set-server-url')?.value?.trim();
                if (url) await window.evichainAPI.settings.update({ api_server_url: url });
                const result = await window.evichainAPI.sync.push();
                if (result.success) {
                    statusDiv.innerHTML = `✅ Push: ${result.pushed} enviadas (${result.alreadySynced} já sincronizadas de ${result.localTotal})`;
                    Toast.show(`${result.pushed} denúncias enviadas ao servidor`, 'success');
                } else {
                    statusDiv.innerHTML = `❌ ${escapeHtml(result.error)}`;
                }
            } catch (err) { statusDiv.innerHTML = `❌ ${escapeHtml(err.message)}`; }
        });

        // Reset
        document.getElementById('btn-reset-settings')?.addEventListener('click', async () => {
            const ok = await Modal.confirm('Restaurar todas as configurações para o padrão?');
            if (!ok) return;
            try {
                await window.evichainAPI.settings.update({
                    institution: 'EviChain', difficulty: 4, aiEngine: 'local',
                    openaiKey: '', notifications: true, exportDir: ''
                });
                Toast.show('Configurações restauradas!', 'success');
                Router.navigate('settings');
            } catch (err) { Toast.show('Erro: ' + err.message, 'error'); }
        });

    } catch (err) {
        container.innerHTML = Components.pageHeader('Configurações') +
            `<div class="card" style="padding:20px;color:var(--danger)">Erro: ${escapeHtml(err.message)}</div>`;
    }
});

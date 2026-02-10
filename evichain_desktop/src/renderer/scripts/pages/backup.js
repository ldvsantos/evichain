/* ============================================================
   EviChain Desktop — Backup Page
   ============================================================ */

Router.register('backup', async (container) => {
    container.innerHTML = Components.loading('Carregando backups…');

    try {
        const backups = await window.evichainAPI.backup.list();

        container.innerHTML = `
            ${Components.pageHeader('Backup & Restauração', 'Gerencie cópias de segurança do banco de dados')}

            <div style="display:flex;gap:8px;margin-bottom:20px">
                <button class="btn btn-primary" id="btn-create-backup">💾 Criar Backup</button>
            </div>

            <div class="card">
                <div class="card-header"><h3>Backups Disponíveis</h3></div>
                <div class="card-body">
                    <div id="backup-list-container">
                        ${renderBackupList(backups)}
                    </div>
                </div>
            </div>
        `;

        document.getElementById('btn-create-backup')?.addEventListener('click', async () => {
            Toast.show('Criando backup…', 'info');
            try {
                const result = await window.evichainAPI.backup.create();
                Toast.show('Backup criado: ' + (result?.filename || 'OK'), 'success');
                Router.navigate('backup');
            } catch (e) { Toast.show('Erro: ' + e.message, 'error'); }
        });

    } catch (err) {
        container.innerHTML = Components.pageHeader('Backup') +
            `<div class="card" style="padding:20px;color:var(--danger)">Erro: ${escapeHtml(err.message)}</div>`;
    }
});

function renderBackupList(backups) {
    if (!backups || !backups.length) {
        return '<p style="color:var(--text-dim);font-size:13px">Nenhum backup encontrado. Crie o primeiro!</p>';
    }

    return `<div class="backup-list">
        ${backups.map(b => `
            <div class="backup-item">
                <div class="backup-info">
                    <div class="backup-name">💾 ${escapeHtml(b.filename || b.name || 'backup')}</div>
                    <div class="backup-date">${formatDate(b.created_at || b.date)}</div>
                </div>
                <div class="backup-size">${b.size ? formatFileSize(b.size) : '—'}</div>
                <div style="display:flex;gap:4px;margin-left:12px">
                    <button class="btn btn-warning btn-sm" onclick="restoreBackup('${escapeHtml(b.filename || b.path)}')">
                        🔄 Restaurar
                    </button>
                </div>
            </div>
        `).join('')}
    </div>`;
}

async function restoreBackup(filename) {
    const ok = await Modal.confirm(`Deseja restaurar o backup "${filename}"?\n\nUm backup de segurança será criado automaticamente antes da restauração.`);
    if (!ok) return;

    Toast.show('Restaurando backup…', 'info');
    try {
        await window.evichainAPI.backup.restore(filename);
        Toast.show('Backup restaurado com sucesso! Reinicie o app.', 'success');
    } catch (e) { Toast.show('Erro: ' + e.message, 'error'); }
}

function formatFileSize(bytes) {
    if (!bytes) return '—';
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    let size = bytes;
    while (size >= 1024 && i < units.length - 1) { size /= 1024; i++; }
    return size.toFixed(i > 0 ? 1 : 0) + ' ' + units[i];
}

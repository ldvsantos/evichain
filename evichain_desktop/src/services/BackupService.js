// ============================================================
// EviChain Desktop — Backup Service
// ============================================================
const fs = require('fs');
const path = require('path');

class BackupService {
    constructor(db, dataDir) {
        this.db = db;
        this.backupDir = path.join(dataDir, 'backups');
        if (!fs.existsSync(this.backupDir)) fs.mkdirSync(this.backupDir, { recursive: true });
    }

    create() {
        try {
            const backupPath = this.db.createBackup(this.backupDir);
            this.db.logAudit('backup_create', 'system', null, null, { path: backupPath });
            return { success: true, path: backupPath };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    list() {
        try {
            const files = fs.readdirSync(this.backupDir)
                .filter(f => f.endsWith('.db'))
                .map(f => {
                    const fullPath = path.join(this.backupDir, f);
                    const stats = fs.statSync(fullPath);
                    return {
                        name: f,
                        path: fullPath,
                        size: stats.size,
                        created: stats.birthtime.toISOString()
                    };
                })
                .sort((a, b) => new Date(b.created) - new Date(a.created));
            return { success: true, backups: files };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    restore(backupPath) {
        try {
            if (!fs.existsSync(backupPath)) {
                return { success: false, error: 'Arquivo de backup não encontrado' };
            }
            // Create safety backup before restore
            this.create();
            // Copy backup over current db
            fs.copyFileSync(backupPath, this.db.dbPath);
            this.db.logAudit('backup_restore', 'system', null, null, { from: backupPath });
            return { success: true, message: 'Backup restaurado. Reinicie o aplicativo.' };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }
}

module.exports = BackupService;

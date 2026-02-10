// ============================================================
// EviChain Desktop — Settings Service
// ============================================================
class SettingsService {
    constructor(db) {
        this.db = db;
    }

    initDefaults() {
        const defaults = {
            app_name: 'EviChain Desktop',
            blockchain_difficulty: 4,
            auto_analyze: true,
            api_server_url: 'http://localhost:5000',
            theme: 'dark',
            language: 'pt-BR',
            auto_backup: true,
            backup_interval_hours: 24
        };

        Object.entries(defaults).forEach(([key, value]) => {
            if (this.db.getSetting(key) === null) {
                this.db.setSetting(key, value);
            }
        });
    }

    getAll() {
        try {
            return { success: true, settings: this.db.getSettings() };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    updateAll(settings) {
        try {
            Object.entries(settings).forEach(([key, value]) => {
                this.db.setSetting(key, value);
            });
            this.db.logAudit('settings_update', 'system', null, null, settings);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }
}

module.exports = SettingsService;

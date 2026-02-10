// ============================================================
// EviChain Desktop — Database Layer (SQLite)
// ============================================================
const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

class EviChainDB {
    constructor(dataDir) {
        this.dataDir = dataDir;
        this.dbPath = path.join(dataDir, 'evichain.db');
        this.db = null;
    }

    initialize() {
        this.db = new Database(this.dbPath);
        this.db.pragma('journal_mode = WAL');
        this.db.pragma('foreign_keys = ON');
        this._createTables();
        this._createGenesisBlock();
        console.log('[DB] EviChain database initialized at:', this.dbPath);
    }

    _createTables() {
        this.db.exec(`
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'operator',
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS blockchain (
                block_index INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                data TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                hash TEXT NOT NULL,
                nonce INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS complaints (
                id TEXT PRIMARY KEY,
                titulo TEXT,
                nome_denunciado TEXT,
                descricao TEXT,
                conselho TEXT,
                categoria TEXT,
                assunto TEXT,
                prioridade TEXT,
                finalidade TEXT,
                anonymous INTEGER DEFAULT 1,
                ouvidoria_anonima INTEGER DEFAULT 0,
                codigos_anteriores TEXT,
                status TEXT DEFAULT 'pending',
                ia_analysis TEXT,
                investigacao TEXT,
                block_index INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (block_index) REFERENCES blockchain(block_index)
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id TEXT,
                user_id TEXT,
                details TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS investigation_cache (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                conselho TEXT,
                result TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                expires_at TEXT
            );
        `);
    }

    _createGenesisBlock() {
        const exists = this.db.prepare('SELECT COUNT(*) as count FROM blockchain').get();
        if (exists.count === 0) {
            const genesisData = JSON.stringify({ type: 'genesis', message: 'EviChain Genesis Block' });
            const hash = this._calculateHash(0, new Date().toISOString(), genesisData, '0');
            this.db.prepare(`
                INSERT INTO blockchain (block_index, timestamp, data, previous_hash, hash, nonce)
                VALUES (?, ?, ?, ?, ?, ?)
            `).run(0, new Date().toISOString(), genesisData, '0', hash, 0);
        }
    }

    _calculateHash(index, timestamp, data, previousHash, nonce = 0) {
        const blockString = JSON.stringify({ index, timestamp, data, previousHash, nonce });
        return crypto.createHash('sha256').update(blockString).digest('hex');
    }

    // ── Settings ─────────────────────────────────────────────
    getSetting(key) {
        const row = this.db.prepare('SELECT value FROM settings WHERE key = ?').get(key);
        return row ? JSON.parse(row.value) : null;
    }

    setSetting(key, value) {
        this.db.prepare(`
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        `).run(key, JSON.stringify(value));
    }

    getSettings() {
        const rows = this.db.prepare('SELECT key, value FROM settings').all();
        const settings = {};
        rows.forEach(r => { settings[r.key] = JSON.parse(r.value); });
        return settings;
    }

    // ── Users ────────────────────────────────────────────────
    createUser(id, username, passwordHash, role = 'operator') {
        return this.db.prepare(`
            INSERT INTO users (id, username, password_hash, role) VALUES (?, ?, ?, ?)
        `).run(id, username, passwordHash, role);
    }

    getUserByUsername(username) {
        return this.db.prepare('SELECT * FROM users WHERE username = ?').get(username);
    }

    listUsers() {
        return this.db.prepare('SELECT id, username, role, active, created_at FROM users').all();
    }

    toggleUserActive(id) {
        return this.db.prepare('UPDATE users SET active = CASE WHEN active = 1 THEN 0 ELSE 1 END WHERE id = ?').run(id);
    }

    // ── Blockchain ───────────────────────────────────────────
    getLastBlock() {
        return this.db.prepare('SELECT * FROM blockchain ORDER BY block_index DESC LIMIT 1').get();
    }

    addBlock(data) {
        const lastBlock = this.getLastBlock();
        const newIndex = lastBlock.block_index + 1;
        const timestamp = new Date().toISOString();
        const dataStr = JSON.stringify(data);
        let nonce = 0;
        let hash = '';
        const difficulty = 4;
        const target = '0'.repeat(difficulty);

        do {
            hash = this._calculateHash(newIndex, timestamp, dataStr, lastBlock.hash, nonce);
            nonce++;
        } while (!hash.startsWith(target));

        this.db.prepare(`
            INSERT INTO blockchain (block_index, timestamp, data, previous_hash, hash, nonce)
            VALUES (?, ?, ?, ?, ?, ?)
        `).run(newIndex, timestamp, dataStr, lastBlock.hash, hash, nonce - 1);

        return { index: newIndex, hash, nonce: nonce - 1 };
    }

    getChainInfo() {
        const totalBlocks = this.db.prepare('SELECT COUNT(*) as count FROM blockchain').get().count;
        const lastBlock = this.getLastBlock();
        const totalComplaints = this.db.prepare('SELECT COUNT(*) as count FROM complaints').get().count;
        return {
            total_blocks: totalBlocks,
            last_block_hash: lastBlock ? lastBlock.hash : null,
            last_block_index: lastBlock ? lastBlock.block_index : 0,
            total_complaints: totalComplaints,
            chain_valid: this.validateChain()
        };
    }

    validateChain() {
        const blocks = this.db.prepare('SELECT * FROM blockchain ORDER BY block_index ASC').all();
        for (let i = 1; i < blocks.length; i++) {
            if (blocks[i].previous_hash !== blocks[i - 1].hash) return false;
        }
        return true;
    }

    getRecentBlocks(limit = 10) {
        return this.db.prepare('SELECT * FROM blockchain ORDER BY block_index DESC LIMIT ?').all(limit);
    }

    // ── Complaints ───────────────────────────────────────────
    createComplaint(complaint) {
        const id = complaint.id || this._generateComplaintId();
        this.db.prepare(`
            INSERT INTO complaints (id, titulo, nome_denunciado, descricao, conselho, categoria,
                assunto, prioridade, finalidade, anonymous, ouvidoria_anonima, codigos_anteriores,
                status, ia_analysis, investigacao, block_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).run(
            id, complaint.titulo, complaint.nome_denunciado, complaint.descricao,
            complaint.conselho, complaint.categoria, complaint.assunto, complaint.prioridade,
            complaint.finalidade, complaint.anonymous ? 1 : 0, complaint.ouvidoria_anonima ? 1 : 0,
            complaint.codigos_anteriores, complaint.status || 'pending',
            complaint.ia_analysis ? JSON.stringify(complaint.ia_analysis) : null,
            complaint.investigacao ? JSON.stringify(complaint.investigacao) : null,
            complaint.block_index || null
        );
        return id;
    }

    getComplaint(id) {
        const row = this.db.prepare('SELECT * FROM complaints WHERE id = ?').get(id);
        if (row) {
            row.ia_analysis = row.ia_analysis ? JSON.parse(row.ia_analysis) : null;
            row.investigacao = row.investigacao ? JSON.parse(row.investigacao) : null;
        }
        return row;
    }

    listComplaints(filters = {}) {
        let query = 'SELECT * FROM complaints WHERE 1=1';
        const params = [];

        if (filters.status) { query += ' AND status = ?'; params.push(filters.status); }
        if (filters.conselho) { query += ' AND conselho = ?'; params.push(filters.conselho); }
        if (filters.categoria) { query += ' AND categoria = ?'; params.push(filters.categoria); }
        if (filters.search) {
            query += ' AND (titulo LIKE ? OR nome_denunciado LIKE ? OR descricao LIKE ? OR assunto LIKE ?)';
            const like = `%${filters.search}%`;
            params.push(like, like, like, like);
        }

        query += ' ORDER BY created_at DESC';
        if (filters.limit) { query += ' LIMIT ?'; params.push(filters.limit); }

        const rows = this.db.prepare(query).all(...params);
        return rows.map(row => {
            row.ia_analysis = row.ia_analysis ? JSON.parse(row.ia_analysis) : null;
            row.investigacao = row.investigacao ? JSON.parse(row.investigacao) : null;
            return row;
        });
    }

    updateComplaintStatus(id, status) {
        return this.db.prepare(`UPDATE complaints SET status = ?, updated_at = datetime('now') WHERE id = ?`).run(status, id);
    }

    updateComplaintAnalysis(id, iaAnalysis) {
        return this.db.prepare(`UPDATE complaints SET ia_analysis = ?, updated_at = datetime('now') WHERE id = ?`).run(
            JSON.stringify(iaAnalysis), id
        );
    }

    updateComplaintInvestigation(id, investigacao) {
        return this.db.prepare(`UPDATE complaints SET investigacao = ?, updated_at = datetime('now') WHERE id = ?`).run(
            JSON.stringify(investigacao), id
        );
    }

    deleteComplaint(id) {
        return this.db.prepare('DELETE FROM complaints WHERE id = ?').run(id);
    }

    searchComplaints(query) {
        return this.listComplaints({ search: query });
    }

    // ── Statistics ────────────────────────────────────────────
    getStats() {
        const total = this.db.prepare('SELECT COUNT(*) as count FROM complaints').get().count;
        const pending = this.db.prepare("SELECT COUNT(*) as count FROM complaints WHERE status = 'pending'").get().count;
        const investigating = this.db.prepare("SELECT COUNT(*) as count FROM complaints WHERE status = 'investigating'").get().count;
        const resolved = this.db.prepare("SELECT COUNT(*) as count FROM complaints WHERE status = 'resolved'").get().count;
        const archived = this.db.prepare("SELECT COUNT(*) as count FROM complaints WHERE status = 'archived'").get().count;

        const byConselho = this.db.prepare('SELECT conselho, COUNT(*) as count FROM complaints GROUP BY conselho').all();
        const byCategoria = this.db.prepare('SELECT categoria, COUNT(*) as count FROM complaints GROUP BY categoria').all();
        const byStatus = this.db.prepare('SELECT status, COUNT(*) as count FROM complaints GROUP BY status').all();
        const byPrioridade = this.db.prepare('SELECT prioridade, COUNT(*) as count FROM complaints GROUP BY prioridade').all();

        const recentComplaints = this.db.prepare('SELECT * FROM complaints ORDER BY created_at DESC LIMIT 5').all();
        recentComplaints.forEach(row => {
            row.ia_analysis = row.ia_analysis ? JSON.parse(row.ia_analysis) : null;
        });

        const totalBlocks = this.db.prepare('SELECT COUNT(*) as count FROM blockchain').get().count;

        return {
            total, pending, investigating, resolved, archived,
            totalBlocks,
            byConselho: Object.fromEntries(byConselho.map(r => [r.conselho || 'N/A', r.count])),
            byCategoria: Object.fromEntries(byCategoria.map(r => [r.categoria || 'N/A', r.count])),
            byStatus: Object.fromEntries(byStatus.map(r => [r.status || 'N/A', r.count])),
            byPrioridade: Object.fromEntries(byPrioridade.map(r => [r.prioridade || 'N/A', r.count])),
            recentComplaints
        };
    }

    // ── Audit Log ────────────────────────────────────────────
    logAudit(action, entityType, entityId, userId, details) {
        this.db.prepare(`
            INSERT INTO audit_log (action, entity_type, entity_id, user_id, details)
            VALUES (?, ?, ?, ?, ?)
        `).run(action, entityType, entityId, userId, details ? JSON.stringify(details) : null);
    }

    getAuditLog(limit = 50) {
        return this.db.prepare('SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?').all(limit);
    }

    // ── Investigation Cache ──────────────────────────────────
    cacheInvestigation(id, nome, conselho, result) {
        const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();
        this.db.prepare(`
            INSERT OR REPLACE INTO investigation_cache (id, nome, conselho, result, created_at, expires_at)
            VALUES (?, ?, ?, ?, datetime('now'), ?)
        `).run(id, nome, conselho, JSON.stringify(result), expiresAt);
    }

    getCachedInvestigation(nome, conselho) {
        const row = this.db.prepare(
            "SELECT * FROM investigation_cache WHERE nome = ? AND conselho = ? AND expires_at > datetime('now') ORDER BY created_at DESC LIMIT 1"
        ).get(nome, conselho);
        if (row) row.result = JSON.parse(row.result);
        return row;
    }

    // ── Helpers ──────────────────────────────────────────────
    _generateComplaintId() {
        const now = new Date();
        return `EVC-${now.getFullYear()}-${Math.floor(now.getTime() % 1000000)}`;
    }

    // ── Backup ───────────────────────────────────────────────
    createBackup(backupDir) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const backupPath = path.join(backupDir, `evichain_backup_${timestamp}.db`);
        this.db.backup(backupPath);
        return backupPath;
    }

    close() {
        if (this.db) this.db.close();
    }
}

module.exports = EviChainDB;

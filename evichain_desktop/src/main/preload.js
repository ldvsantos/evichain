// ============================================================
// EviChain Desktop — Preload Bridge
// ============================================================
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('evichainAPI', {
    // ── Window Controls ──────────────────────────────────────
    window: {
        minimize: () => ipcRenderer.invoke('window:minimize'),
        maximize: () => ipcRenderer.invoke('window:maximize'),
        close: () => ipcRenderer.invoke('window:close')
    },

    // ── Auth ─────────────────────────────────────────────────
    auth: {
        login: (username, password) => ipcRenderer.invoke('auth:login', { username, password }),
        logout: () => ipcRenderer.invoke('auth:logout'),
        check: () => ipcRenderer.invoke('auth:check'),
        changePassword: (userId, currentPassword, newPassword) =>
            ipcRenderer.invoke('auth:changePassword', { userId, currentPassword, newPassword })
    },

    // ── Complaints ───────────────────────────────────────────
    complaints: {
        create: (data) => ipcRenderer.invoke('complaints:create', data),
        list: (filters) => ipcRenderer.invoke('complaints:list', filters),
        get: (id) => ipcRenderer.invoke('complaints:get', id),
        update: (id, data) => ipcRenderer.invoke('complaints:update', { id, data }),
        updateStatus: (id, status) => ipcRenderer.invoke('complaints:updateStatus', { id, status }),
        delete: (id) => ipcRenderer.invoke('complaints:delete', id),
        search: (query) => ipcRenderer.invoke('complaints:search', query)
    },

    // ── Blockchain ───────────────────────────────────────────
    blockchain: {
        info: () => ipcRenderer.invoke('blockchain:info'),
        validate: () => ipcRenderer.invoke('blockchain:validate'),
        recentBlocks: (limit) => ipcRenderer.invoke('blockchain:recentBlocks', limit)
    },

    // ── Analysis (IA) ────────────────────────────────────────
    analysis: {
        analyze: (complaintId, text, conselho, categoria) =>
            ipcRenderer.invoke('analysis:analyze', { complaintId, text, conselho, categoria }),
        assistente: (text, conselho, categoria) =>
            ipcRenderer.invoke('analysis:assistente', { text, conselho, categoria }),
        latest: () => ipcRenderer.invoke('analysis:latest')
    },

    // ── Investigation ────────────────────────────────────────
    investigation: {
        start: (nome, registro, conselho, infoAdicionais) =>
            ipcRenderer.invoke('investigation:start', { nome, registro, conselho, infoAdicionais }),
        searchSocial: (nome) =>
            ipcRenderer.invoke('investigation:searchSocial', { nome }),
        checkRegistro: (nome, registro, conselho) =>
            ipcRenderer.invoke('investigation:checkRegistro', { nome, registro, conselho })
    },

    // ── Reports ──────────────────────────────────────────────
    reports: {
        complaintPDF: (complaintId) => ipcRenderer.invoke('reports:complaintPDF', complaintId),
        blockchainPDF: () => ipcRenderer.invoke('reports:blockchainPDF'),
        exportCSV: () => ipcRenderer.invoke('reports:exportCSV')
    },

    // ── Backup ───────────────────────────────────────────────
    backup: {
        create: () => ipcRenderer.invoke('backup:create'),
        list: () => ipcRenderer.invoke('backup:list'),
        restore: (backupPath) => ipcRenderer.invoke('backup:restore', backupPath)
    },

    // ── Settings ─────────────────────────────────────────────
    settings: {
        get: () => ipcRenderer.invoke('settings:get'),
        update: (settings) => ipcRenderer.invoke('settings:update', settings)
    },

    // ── Dashboard ────────────────────────────────────────────
    dashboard: {
        stats: () => ipcRenderer.invoke('dashboard:stats')
    },

    // ── Users ────────────────────────────────────────────────
    users: {
        list: () => ipcRenderer.invoke('users:list'),
        create: (username, password, role) => ipcRenderer.invoke('users:create', { username, password, role }),
        toggleActive: (id) => ipcRenderer.invoke('users:toggleActive', id)
    },

    // ── Audit ────────────────────────────────────────────────
    audit: {
        log: (limit) => ipcRenderer.invoke('audit:log', limit)
    },

    // ── Sync ─────────────────────────────────────────────────
    sync: {
        full: () => ipcRenderer.invoke('sync:full'),
        pull: () => ipcRenderer.invoke('sync:pull'),
        push: () => ipcRenderer.invoke('sync:push'),
        status: () => ipcRenderer.invoke('sync:status'),
        checkConnection: () => ipcRenderer.invoke('sync:checkConnection')
    },

    // ── Dialog ───────────────────────────────────────────────
    dialog: {
        openFile: (options) => ipcRenderer.invoke('dialog:openFile', options),
        saveFile: (options) => ipcRenderer.invoke('dialog:saveFile', options)
    },

    // ── File ─────────────────────────────────────────────────
    file: {
        write: (filePath, data) => ipcRenderer.invoke('file:write', { filePath, data }),
        openExternal: (url) => ipcRenderer.invoke('file:openExternal', url)
    },

    // ── Navigation Events ────────────────────────────────────
    onNavigate: (callback) => {
        const channels = [
            'nav:dashboard', 'nav:complaints', 'nav:complaints-new', 'nav:blockchain',
            'nav:investigator', 'nav:reports', 'nav:backup', 'nav:settings'
        ];
        channels.forEach(ch => ipcRenderer.on(ch, () => callback(ch.replace('nav:', ''))));
    },

    onNotification: (callback) => {
        ipcRenderer.on('app:notification', (_, data) => callback(data));
    }
});

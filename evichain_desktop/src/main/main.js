// ============================================================
// EviChain Desktop — Main Process (Electron)
// ============================================================
const { app, BrowserWindow, ipcMain, Menu, dialog, shell, nativeTheme } = require('electron');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

// ── Data directory ───────────────────────────────────────────
const USER_DATA = app.getPath('userData');
const DATA_DIR = path.join(USER_DATA, 'evichain_data');
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

// ── Database ─────────────────────────────────────────────────
const EviChainDB = require('../database/database');
const db = new EviChainDB(DATA_DIR);

// ── Services ─────────────────────────────────────────────────
const ComplaintService = require('../services/ComplaintService');
const BlockchainService = require('../services/BlockchainService');
const InvestigationService = require('../services/InvestigationService');
const AnalysisService = require('../services/AnalysisService');
const AuthService = require('../services/AuthService');
const ReportService = require('../services/ReportService');
const BackupService = require('../services/BackupService');
const SettingsService = require('../services/SettingsService');
const SyncService = require('../services/SyncService');

// ── Windows ──────────────────────────────────────────────────
let mainWindow = null;
let splashWindow = null;

// ── Services instances ───────────────────────────────────────
let services = {};

// ============================================================
// Window Creation
// ============================================================
function createSplashWindow() {
    splashWindow = new BrowserWindow({
        width: 480,
        height: 360,
        frame: false,
        transparent: true,
        resizable: false,
        skipTaskbar: true,
        alwaysOnTop: true,
        icon: path.join(__dirname, '../../assets/icon.png'),
        webPreferences: { nodeIntegration: false, contextIsolation: true }
    });
    splashWindow.loadFile(path.join(__dirname, '..', 'renderer', 'splash.html'));
    splashWindow.center();
}

function createMainWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1024,
        minHeight: 700,
        show: false,
        frame: false,
        titleBarStyle: 'hidden',
        icon: path.join(__dirname, '../../assets/icon.png'),
        backgroundColor: '#f8fafc',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: false
        }
    });

    mainWindow.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));

    mainWindow.once('ready-to-show', () => {
        setTimeout(() => {
            if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
            mainWindow.show();
            if (process.env.NODE_ENV === 'development') {
                mainWindow.webContents.openDevTools();
            }
        }, 3000);
    });

    mainWindow.on('closed', () => { mainWindow = null; });
}

// ============================================================
// Services Initialization
// ============================================================
function initServices() {
    services.auth = new AuthService(db);
    services.complaint = new ComplaintService(db);
    services.blockchain = new BlockchainService(db);
    services.investigation = new InvestigationService(db);
    services.analysis = new AnalysisService(db);
    services.report = new ReportService(db);
    services.backup = new BackupService(db, DATA_DIR);
    services.settings = new SettingsService(db);
    services.sync = new SyncService(db, services.settings);

    // Create default admin user
    services.auth.ensureDefaultAdmin();

    // Initialize default settings
    services.settings.initDefaults();
}

// ============================================================
// Menu
// ============================================================
function buildMenu() {
    const template = [
        {
            label: 'Arquivo',
            submenu: [
                {
                    label: 'Nova Denúncia',
                    accelerator: 'CmdOrCtrl+N',
                    click: () => mainWindow?.webContents.send('nav:complaints-new')
                },
                { type: 'separator' },
                {
                    label: 'Exportar Relatório',
                    accelerator: 'CmdOrCtrl+E',
                    click: () => mainWindow?.webContents.send('nav:reports')
                },
                { type: 'separator' },
                {
                    label: 'Backup',
                    click: () => mainWindow?.webContents.send('nav:backup')
                },
                { type: 'separator' },
                { label: 'Sair', accelerator: 'CmdOrCtrl+Q', role: 'quit' }
            ]
        },
        {
            label: 'Editar',
            submenu: [
                { role: 'undo', label: 'Desfazer' },
                { role: 'redo', label: 'Refazer' },
                { type: 'separator' },
                { role: 'cut', label: 'Recortar' },
                { role: 'copy', label: 'Copiar' },
                { role: 'paste', label: 'Colar' },
                { role: 'selectAll', label: 'Selecionar Tudo' }
            ]
        },
        {
            label: 'Ver',
            submenu: [
                {
                    label: 'Dashboard',
                    accelerator: 'CmdOrCtrl+1',
                    click: () => mainWindow?.webContents.send('nav:dashboard')
                },
                {
                    label: 'Denúncias',
                    accelerator: 'CmdOrCtrl+2',
                    click: () => mainWindow?.webContents.send('nav:complaints')
                },
                {
                    label: 'Blockchain',
                    accelerator: 'CmdOrCtrl+3',
                    click: () => mainWindow?.webContents.send('nav:blockchain')
                },
                {
                    label: 'Investigador',
                    accelerator: 'CmdOrCtrl+4',
                    click: () => mainWindow?.webContents.send('nav:investigator')
                },
                { type: 'separator' },
                { role: 'reload', label: 'Recarregar' },
                { role: 'toggleDevTools', label: 'DevTools' },
                { type: 'separator' },
                { role: 'zoomIn', label: 'Aumentar Zoom' },
                { role: 'zoomOut', label: 'Diminuir Zoom' },
                { role: 'resetZoom', label: 'Zoom Padrão' },
                { type: 'separator' },
                { role: 'togglefullscreen', label: 'Tela Cheia' }
            ]
        },
        {
            label: 'Ajuda',
            submenu: [
                {
                    label: 'Sobre o EviChain',
                    click: () => {
                        dialog.showMessageBox(mainWindow, {
                            type: 'info',
                            title: 'Sobre o EviChain Desktop',
                            message: 'EviChain Desktop v1.0.0',
                            detail: 'Plataforma de Inovação Probatória com Blockchain e IA.\n\nSistema de registro e análise inteligente de denúncias contra profissionais regulamentados.\n\n© 2026 EviChain Team'
                        });
                    }
                },
                { type: 'separator' },
                {
                    label: 'Documentação',
                    click: () => shell.openExternal('https://github.com/ldvsantos/evichain')
                }
            ]
        }
    ];

    Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// ============================================================
// IPC Handlers
// ============================================================
function registerIPCHandlers() {
    // ── Window Controls ──────────────────────────────────────
    ipcMain.handle('window:minimize', () => mainWindow?.minimize());
    ipcMain.handle('window:maximize', () => {
        if (mainWindow?.isMaximized()) mainWindow.unmaximize();
        else mainWindow?.maximize();
    });
    ipcMain.handle('window:close', () => mainWindow?.close());

    // ── Auth ─────────────────────────────────────────────────
    ipcMain.handle('auth:login', async (_, { username, password }) => {
        return services.auth.login(username, password);
    });
    ipcMain.handle('auth:logout', async () => {
        return services.auth.logout();
    });
    ipcMain.handle('auth:check', async () => {
        return services.auth.checkSession();
    });
    ipcMain.handle('auth:changePassword', async (_, { userId, currentPassword, newPassword }) => {
        return services.auth.changePassword(userId, currentPassword, newPassword);
    });

    // ── Complaints ───────────────────────────────────────────
    ipcMain.handle('complaints:create', async (_, data) => {
        return services.complaint.create(data);
    });
    ipcMain.handle('complaints:list', async (_, filters) => {
        return services.complaint.list(filters);
    });
    ipcMain.handle('complaints:get', async (_, id) => {
        return services.complaint.get(id);
    });
    ipcMain.handle('complaints:update', async (_, { id, data }) => {
        return services.complaint.update(id, data);
    });
    ipcMain.handle('complaints:updateStatus', async (_, { id, status }) => {
        return services.complaint.updateStatus(id, status);
    });
    ipcMain.handle('complaints:delete', async (_, id) => {
        return services.complaint.delete(id);
    });
    ipcMain.handle('complaints:search', async (_, query) => {
        return services.complaint.search(query);
    });

    // ── Blockchain ───────────────────────────────────────────
    ipcMain.handle('blockchain:info', async () => {
        return services.blockchain.getInfo();
    });
    ipcMain.handle('blockchain:validate', async () => {
        return services.blockchain.validate();
    });
    ipcMain.handle('blockchain:recentBlocks', async (_, limit) => {
        return services.blockchain.getRecentBlocks(limit);
    });

    // ── Analysis (IA) ────────────────────────────────────────
    ipcMain.handle('analysis:analyze', async (_, { complaintId, text, conselho, categoria }) => {
        return services.analysis.analyzeComplaint(complaintId, text, conselho, categoria);
    });
    ipcMain.handle('analysis:assistente', async (_, { text, conselho, categoria }) => {
        return services.analysis.assistenteAnalise(text, conselho, categoria);
    });
    ipcMain.handle('analysis:latest', async () => {
        return services.analysis.getLatestAnalysis();
    });

    // ── Investigation ────────────────────────────────────────
    ipcMain.handle('investigation:start', async (_, { nome, registro, conselho, infoAdicionais }) => {
        return services.investigation.investigar(nome, registro, conselho, infoAdicionais);
    });
    ipcMain.handle('investigation:searchSocial', async (_, { nome }) => {
        return services.investigation.buscarRedesSociais(nome);
    });
    ipcMain.handle('investigation:checkRegistro', async (_, { nome, registro, conselho }) => {
        return services.investigation.consultarRegistro(nome, registro, conselho);
    });

    // ── Reports ──────────────────────────────────────────────
    ipcMain.handle('reports:complaintPDF', async (_, complaintId) => {
        const savePath = await dialog.showSaveDialog(mainWindow, {
            title: 'Salvar Relatório PDF',
            defaultPath: `EviChain_Denuncia_${complaintId}.pdf`,
            filters: [{ name: 'PDF', extensions: ['pdf'] }]
        });
        if (savePath.canceled) return { success: false, canceled: true };
        return services.report.generateComplaintPDF(complaintId, savePath.filePath);
    });
    ipcMain.handle('reports:blockchainPDF', async () => {
        const savePath = await dialog.showSaveDialog(mainWindow, {
            title: 'Salvar Relatório da Blockchain',
            defaultPath: `EviChain_Blockchain_${new Date().toISOString().split('T')[0]}.pdf`,
            filters: [{ name: 'PDF', extensions: ['pdf'] }]
        });
        if (savePath.canceled) return { success: false, canceled: true };
        return services.report.generateBlockchainPDF(savePath.filePath);
    });
    ipcMain.handle('reports:exportCSV', async () => {
        const savePath = await dialog.showSaveDialog(mainWindow, {
            title: 'Exportar Denúncias CSV',
            defaultPath: `EviChain_Export_${new Date().toISOString().split('T')[0]}.csv`,
            filters: [{ name: 'CSV', extensions: ['csv'] }]
        });
        if (savePath.canceled) return { success: false, canceled: true };
        return services.report.exportCSV(savePath.filePath);
    });

    // ── Backup ───────────────────────────────────────────────
    ipcMain.handle('backup:create', async () => {
        return services.backup.create();
    });
    ipcMain.handle('backup:list', async () => {
        return services.backup.list();
    });
    ipcMain.handle('backup:restore', async (_, backupPath) => {
        return services.backup.restore(backupPath);
    });

    // ── Settings ─────────────────────────────────────────────
    ipcMain.handle('settings:get', async () => {
        return services.settings.getAll();
    });
    ipcMain.handle('settings:update', async (_, settings) => {
        return services.settings.updateAll(settings);
    });

    // ── Dashboard Stats ──────────────────────────────────────
    ipcMain.handle('dashboard:stats', async () => {
        return services.complaint.getStats();
    });

    // ── Users ────────────────────────────────────────────────
    ipcMain.handle('users:list', async () => {
        return services.auth.listUsers();
    });
    ipcMain.handle('users:create', async (_, { username, password, role }) => {
        return services.auth.createUser(username, password, role);
    });
    ipcMain.handle('users:toggleActive', async (_, id) => {
        return services.auth.toggleUserActive(id);
    });

    // ── Audit Log ────────────────────────────────────────────
    ipcMain.handle('audit:log', async (_, limit) => {
        return db.getAuditLog(limit);
    });

    // ── Sync ─────────────────────────────────────────────────
    ipcMain.handle('sync:full', async () => {
        return services.sync.fullSync();
    });
    ipcMain.handle('sync:pull', async () => {
        try {
            const result = await services.sync.pull();
            return { success: true, ...result };
        } catch (err) {
            return { success: false, error: err.message };
        }
    });
    ipcMain.handle('sync:push', async () => {
        try {
            const result = await services.sync.push();
            return { success: true, ...result };
        } catch (err) {
            return { success: false, error: err.message };
        }
    });
    ipcMain.handle('sync:status', async () => {
        return services.sync.getStatus();
    });
    ipcMain.handle('sync:checkConnection', async () => {
        return services.sync.checkConnection();
    });

    // ── Dialog ───────────────────────────────────────────────
    ipcMain.handle('dialog:openFile', async (_, options) => {
        return dialog.showOpenDialog(mainWindow, options);
    });
    ipcMain.handle('dialog:saveFile', async (_, options) => {
        return dialog.showSaveDialog(mainWindow, options);
    });

    // ── File ─────────────────────────────────────────────────
    ipcMain.handle('file:write', async (_, { filePath, data }) => {
        fs.writeFileSync(filePath, data);
        return { success: true };
    });

    ipcMain.handle('file:openExternal', async (_, url) => {
        const { shell } = require('electron');
        await shell.openExternal(url);
    });
}

// ============================================================
// App Lifecycle
// ============================================================
app.whenReady().then(async () => {
    createSplashWindow();

    try {
        db.initialize();
        initServices();
        buildMenu();
        registerIPCHandlers();
        createMainWindow();
    } catch (err) {
        console.error('[FATAL] Initialization failed:', err);
        dialog.showErrorBox('Erro Fatal', `Falha na inicialização: ${err.message}`);
        app.quit();
    }
});

app.on('window-all-closed', () => {
    db.close();
    app.quit();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
});

// ============================================================
// EviChain Desktop — Sync Service
// Sincroniza denúncias entre Desktop (SQLite) e Server (API)
// ============================================================
const https = require('https');
const http = require('http');

class SyncService {
    constructor(db, settingsService) {
        this.db = db;
        this.settingsService = settingsService;
        this.syncing = false;
    }

    /**
     * Retorna a URL base do servidor a partir das configurações.
     */
    _getServerUrl() {
        const settings = this.settingsService.getAll();
        const url = settings.success && settings.settings.api_server_url
            ? settings.settings.api_server_url
            : 'http://localhost:5000';
        return url.replace(/\/+$/, ''); // Remove trailing slash
    }

    /**
     * Faz uma requisição HTTP(S) genérica e retorna JSON.
     */
    _request(method, url, body = null) {
        return new Promise((resolve, reject) => {
            const parsed = new URL(url);
            const lib = parsed.protocol === 'https:' ? https : http;
            const options = {
                hostname: parsed.hostname,
                port: parsed.port,
                path: parsed.pathname + parsed.search,
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-EviChain-Client': 'desktop'
                },
                timeout: 15000
            };

            const req = lib.request(options, (res) => {
                let data = '';
                res.on('data', chunk => { data += chunk; });
                res.on('end', () => {
                    try {
                        resolve({ status: res.statusCode, data: JSON.parse(data) });
                    } catch (e) {
                        reject(new Error(`Resposta inválida do servidor: ${data.substring(0, 200)}`));
                    }
                });
            });

            req.on('error', (e) => reject(new Error(`Conexão falhou: ${e.message}`)));
            req.on('timeout', () => { req.destroy(); reject(new Error('Timeout de conexão (15s)')); });

            if (body) req.write(JSON.stringify(body));
            req.end();
        });
    }

    /**
     * Verifica se o servidor está acessível.
     */
    async checkConnection() {
        try {
            const serverUrl = this._getServerUrl();
            const result = await this._request('GET', `${serverUrl}/api/health`);
            return {
                success: true,
                server: serverUrl,
                status: result.data
            };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    /**
     * PULL — Baixa denúncias do servidor que não existem localmente.
     * Retorna quantas denúncias foram importadas.
     */
    async pull() {
        const serverUrl = this._getServerUrl();
        const result = await this._request('GET', `${serverUrl}/api/sync/pull`);

        if (result.status !== 200 || !result.data.success) {
            throw new Error(result.data.error || 'Erro ao buscar dados do servidor');
        }

        const serverComplaints = result.data.complaints || [];
        let imported = 0;
        let updated = 0;

        for (const sc of serverComplaints) {
            const localComplaint = this.db.getComplaint(sc.id);

            if (!localComplaint) {
                // Denúncia não existe localmente — importar
                this.db.createComplaint({
                    id: sc.id,
                    titulo: sc.titulo || sc.metadata?.titulo || '',
                    nome_denunciado: sc.nomeDenunciado || sc.metadata?.nomeDenunciado || '',
                    descricao: sc.descricao || sc.metadata?.descricao || '',
                    conselho: sc.conselho || sc.metadata?.conselho || '',
                    categoria: sc.categoria || sc.metadata?.categoria || '',
                    assunto: sc.assunto || sc.metadata?.assunto || '',
                    prioridade: sc.prioridade || sc.metadata?.prioridade || '',
                    finalidade: sc.finalidade || sc.metadata?.finalidade || '',
                    anonymous: sc.anonymous ?? true,
                    ouvidoria_anonima: sc.ouvidoriaAnonima ?? false,
                    codigos_anteriores: sc.codigosAnteriores || '',
                    status: sc.status || 'pending',
                    ia_analysis: sc.ia_analysis || null,
                    investigacao: sc.investigacao || null
                });
                imported++;
            } else {
                // Denúncia existe — atualizar análise de IA se o servidor tiver e o local não
                if (sc.ia_analysis && Object.keys(sc.ia_analysis).length > 0 &&
                    (!localComplaint.ia_analysis || Object.keys(localComplaint.ia_analysis).length === 0)) {
                    this.db.updateComplaintAnalysis(localComplaint.id, sc.ia_analysis);
                    updated++;
                }
            }
        }

        this.db.logAudit('sync_pull', 'sync', null, null, {
            server: serverUrl,
            server_total: serverComplaints.length,
            imported,
            updated
        });

        return { success: true, imported, updated, serverTotal: serverComplaints.length };
    }

    /**
     * PUSH — Envia denúncias locais que não existem no servidor.
     * Retorna quantas denúncias foram enviadas.
     */
    async push() {
        const serverUrl = this._getServerUrl();

        // Buscar IDs que já existem no servidor
        const serverResult = await this._request('GET', `${serverUrl}/api/sync/pull`);
        if (serverResult.status !== 200 || !serverResult.data.success) {
            throw new Error('Erro ao consultar servidor para sync');
        }

        const serverIds = new Set((serverResult.data.complaints || []).map(c => c.id));
        const localComplaints = this.db.listComplaints({});
        const toSync = localComplaints.filter(c => !serverIds.has(c.id));

        let pushed = 0;
        let errors = [];

        for (const complaint of toSync) {
            try {
                const pushData = {
                    id: complaint.id,
                    titulo: complaint.titulo,
                    nomeDenunciado: complaint.nome_denunciado,
                    descricao: complaint.descricao,
                    conselho: complaint.conselho,
                    categoria: complaint.categoria,
                    assunto: complaint.assunto,
                    prioridade: complaint.prioridade,
                    finalidade: complaint.finalidade,
                    anonymous: !!complaint.anonymous,
                    ouvidoriaAnonima: !!complaint.ouvidoria_anonima,
                    codigosAnteriores: complaint.codigos_anteriores,
                    ia_analysis: complaint.ia_analysis,
                    source: 'desktop'
                };

                const result = await this._request('POST', `${serverUrl}/api/sync/push`, pushData);

                if (result.status === 200 || result.status === 201) {
                    pushed++;
                } else {
                    errors.push({ id: complaint.id, error: result.data.error || 'Erro desconhecido' });
                }
            } catch (err) {
                errors.push({ id: complaint.id, error: err.message });
            }
        }

        this.db.logAudit('sync_push', 'sync', null, null, {
            server: serverUrl,
            local_total: localComplaints.length,
            pushed,
            errors: errors.length
        });

        return {
            success: true,
            pushed,
            errors: errors.length > 0 ? errors : undefined,
            localTotal: localComplaints.length,
            alreadySynced: localComplaints.length - toSync.length
        };
    }

    /**
     * FULL SYNC — Pull + Push bidirecional.
     */
    async fullSync() {
        if (this.syncing) {
            return { success: false, error: 'Sincronização já em andamento' };
        }

        this.syncing = true;
        try {
            // Verificar conexão primeiro
            const conn = await this.checkConnection();
            if (!conn.success) {
                return { success: false, error: `Servidor inacessível: ${conn.error}` };
            }

            // 1) Pull — baixar do servidor
            const pullResult = await this.pull();

            // 2) Push — enviar para o servidor
            const pushResult = await this.push();

            const summary = {
                success: true,
                server: this._getServerUrl(),
                pull: {
                    imported: pullResult.imported,
                    updated: pullResult.updated,
                    serverTotal: pullResult.serverTotal
                },
                push: {
                    pushed: pushResult.pushed,
                    alreadySynced: pushResult.alreadySynced,
                    localTotal: pushResult.localTotal,
                    errors: pushResult.errors
                },
                timestamp: new Date().toISOString()
            };

            // Salvar timestamp da última sincronização
            this.db.setSetting('last_sync', new Date().toISOString());
            this.db.setSetting('last_sync_result', summary);

            return summary;

        } catch (err) {
            return { success: false, error: err.message };
        } finally {
            this.syncing = false;
        }
    }

    /**
     * Retorna o status de sincronização.
     */
    getStatus() {
        const lastSync = this.db.getSetting('last_sync');
        const lastResult = this.db.getSetting('last_sync_result');
        const serverUrl = this._getServerUrl();

        return {
            success: true,
            syncing: this.syncing,
            lastSync,
            lastResult,
            serverUrl
        };
    }
}

module.exports = SyncService;

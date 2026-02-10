// ============================================================
// EviChain Desktop — Complaint Service
// ============================================================
class ComplaintService {
    constructor(db) {
        this.db = db;
    }

    create(data) {
        try {
            // Register on blockchain
            const blockResult = this.db.addBlock({
                type: 'complaint',
                titulo: data.titulo,
                nome_denunciado: data.nomeDenunciado,
                conselho: data.conselho,
                categoria: data.categoria,
                timestamp: new Date().toISOString()
            });

            const id = this.db.createComplaint({
                titulo: data.titulo,
                nome_denunciado: data.nomeDenunciado,
                descricao: data.descricao,
                conselho: data.conselho,
                categoria: data.categoria,
                assunto: data.assunto,
                prioridade: data.prioridade,
                finalidade: data.finalidade,
                anonymous: data.anonymous,
                ouvidoria_anonima: data.ouvidoriaAnonima,
                codigos_anteriores: data.codigosAnteriores,
                block_index: blockResult.index
            });

            this.db.logAudit('create', 'complaint', id, null, {
                titulo: data.titulo,
                conselho: data.conselho,
                block_index: blockResult.index,
                block_hash: blockResult.hash
            });

            return {
                success: true,
                complaint_id: id,
                block_index: blockResult.index,
                block_hash: blockResult.hash
            };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    list(filters = {}) {
        try {
            const complaints = this.db.listComplaints(filters);
            return { success: true, complaints };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    get(id) {
        try {
            const complaint = this.db.getComplaint(id);
            if (!complaint) return { success: false, error: 'Denúncia não encontrada' };
            return { success: true, complaint };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    update(id, data) {
        try {
            const complaint = this.db.getComplaint(id);
            if (!complaint) return { success: false, error: 'Denúncia não encontrada' };

            // Update fields
            const updateQuery = this.db.db.prepare(`
                UPDATE complaints SET
                    titulo = COALESCE(?, titulo),
                    nome_denunciado = COALESCE(?, nome_denunciado),
                    descricao = COALESCE(?, descricao),
                    conselho = COALESCE(?, conselho),
                    categoria = COALESCE(?, categoria),
                    assunto = COALESCE(?, assunto),
                    prioridade = COALESCE(?, prioridade),
                    finalidade = COALESCE(?, finalidade),
                    updated_at = datetime('now')
                WHERE id = ?
            `);
            updateQuery.run(
                data.titulo || null, data.nomeDenunciado || null, data.descricao || null,
                data.conselho || null, data.categoria || null, data.assunto || null,
                data.prioridade || null, data.finalidade || null, id
            );

            this.db.logAudit('update', 'complaint', id, null, data);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    updateStatus(id, status) {
        try {
            this.db.updateComplaintStatus(id, status);
            this.db.logAudit('status_change', 'complaint', id, null, { status });
            return { success: true };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    delete(id) {
        try {
            this.db.deleteComplaint(id);
            this.db.logAudit('delete', 'complaint', id, null, null);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    search(query) {
        try {
            const results = this.db.searchComplaints(query);
            return { success: true, results };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    getStats() {
        try {
            const stats = this.db.getStats();
            return { success: true, ...stats };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }
}

module.exports = ComplaintService;

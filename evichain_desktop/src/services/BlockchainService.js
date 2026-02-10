// ============================================================
// EviChain Desktop — Blockchain Service
// ============================================================
class BlockchainService {
    constructor(db) {
        this.db = db;
    }

    getInfo() {
        try {
            return { success: true, ...this.db.getChainInfo() };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    validate() {
        try {
            const valid = this.db.validateChain();
            return { success: true, valid };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    getRecentBlocks(limit = 10) {
        try {
            const blocks = this.db.getRecentBlocks(limit);
            return {
                success: true,
                blocks: blocks.map(b => ({
                    index: b.block_index,
                    timestamp: b.timestamp,
                    hash: b.hash,
                    previous_hash: b.previous_hash,
                    nonce: b.nonce,
                    data: JSON.parse(b.data)
                }))
            };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }
}

module.exports = BlockchainService;

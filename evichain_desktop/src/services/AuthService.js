// ============================================================
// EviChain Desktop — Auth Service
// ============================================================
const crypto = require('crypto');
const { v4: uuidv4 } = require('uuid');

class AuthService {
    constructor(db) {
        this.db = db;
        this.currentUser = null;
    }

    _hashPassword(password) {
        return crypto.createHash('sha256').update(password).digest('hex');
    }

    ensureDefaultAdmin() {
        const admin = this.db.getUserByUsername('admin');
        if (!admin) {
            this.db.createUser(uuidv4(), 'admin', this._hashPassword('admin123'), 'admin');
            console.log('[AUTH] Default admin user created (admin/admin123)');
        }
    }

    login(username, password) {
        try {
            const user = this.db.getUserByUsername(username);
            if (!user) return { success: false, error: 'Usuário não encontrado' };
            if (!user.active) return { success: false, error: 'Usuário desativado' };
            if (user.password_hash !== this._hashPassword(password)) {
                return { success: false, error: 'Senha incorreta' };
            }
            this.currentUser = { id: user.id, username: user.username, role: user.role };
            this.db.logAudit('login', 'user', user.id, user.id, { username });
            return { success: true, user: this.currentUser };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    logout() {
        if (this.currentUser) {
            this.db.logAudit('logout', 'user', this.currentUser.id, this.currentUser.id, null);
        }
        this.currentUser = null;
        return { success: true };
    }

    checkSession() {
        return { loggedIn: !!this.currentUser, user: this.currentUser };
    }

    changePassword(userId, currentPassword, newPassword) {
        try {
            const users = this.db.listUsers();
            const user = users.find(u => u.id === userId);
            if (!user) return { success: false, error: 'Usuário não encontrado' };
            const fullUser = this.db.getUserByUsername(user.username);
            if (fullUser.password_hash !== this._hashPassword(currentPassword)) {
                return { success: false, error: 'Senha atual incorreta' };
            }
            this.db.db.prepare('UPDATE users SET password_hash = ? WHERE id = ?')
                .run(this._hashPassword(newPassword), userId);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    listUsers() {
        try {
            return { success: true, users: this.db.listUsers() };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    createUser(username, password, role) {
        try {
            const existing = this.db.getUserByUsername(username);
            if (existing) return { success: false, error: 'Usuário já existe' };
            this.db.createUser(uuidv4(), username, this._hashPassword(password), role);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    toggleUserActive(id) {
        try {
            this.db.toggleUserActive(id);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }
}

module.exports = AuthService;

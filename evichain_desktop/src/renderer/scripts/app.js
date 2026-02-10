/* ============================================================
   EviChain Desktop — App Controller
   ============================================================ */

const App = (() => {
    let currentUser = null;

    /* ── Inicialização ──────────────────────────────────── */
    async function init() {
        console.log('[App] Inicializando EviChain Desktop…');

        // Controles da barra de título
        document.getElementById('btn-minimize')?.addEventListener('click', () => window.evichainAPI.window.minimize());
        document.getElementById('btn-maximize')?.addEventListener('click', () => window.evichainAPI.window.maximize());
        document.getElementById('btn-close')?.addEventListener('click', () => window.evichainAPI.window.close());

        // Login
        document.getElementById('btn-login')?.addEventListener('click', handleLogin);
        document.getElementById('login-pass')?.addEventListener('keydown', e => {
            if (e.key === 'Enter') handleLogin();
        });

        // Sidebar
        document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const page = item.dataset.page;
                if (page) Router.navigate(page);
            });
        });

        // Logout
        document.getElementById('btn-logout')?.addEventListener('click', handleLogout);

        // Fechar modal ao clicar no overlay
        document.getElementById('modal-overlay')?.addEventListener('click', e => {
            if (e.target.id === 'modal-overlay') Modal.hide();
        });

        // Notificação do main process
        window.evichainAPI.onNotification?.((data) => {
            Toast.show(data.message, data.type || 'info');
        });

        showLoginScreen();
    }

    /* ── Login / Logout ─────────────────────────────────── */
    async function handleLogin() {
        const username = document.getElementById('login-user')?.value?.trim();
        const password = document.getElementById('login-pass')?.value;

        if (!username || !password) {
            Toast.show('Preencha usuário e senha.', 'warning');
            return;
        }

        try {
            const result = await window.evichainAPI.auth.login(username, password);
            if (result.success) {
                currentUser = result.user;
                showMainLayout();
                Toast.show(`Bem-vindo, ${currentUser.name}!`, 'success');
            } else {
                Toast.show(result.error || 'Credenciais inválidas.', 'error');
            }
        } catch (err) {
            Toast.show('Erro ao fazer login.', 'error');
            console.error('[App] Login error:', err);
        }
    }

    async function handleLogout() {
        const confirm = await Modal.confirm('Deseja realmente sair?');
        if (!confirm) return;

        try {
            await window.evichainAPI.auth.logout();
        } catch (_) { /* ignore */ }
        currentUser = null;
        showLoginScreen();
    }

    /* ── Layout Switching ───────────────────────────────── */
    function showLoginScreen() {
        document.getElementById('login-screen').style.display = 'flex';
        document.getElementById('main-layout').style.display = 'none';
        document.getElementById('login-user').value = '';
        document.getElementById('login-pass').value = '';
        document.getElementById('login-user').focus();
    }

    function showMainLayout() {
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('main-layout').style.display = 'flex';

        // Update user info
        const el = document.getElementById('user-name');
        if (el) el.textContent = currentUser?.name || 'Usuário';

        Router.navigate('dashboard');
    }

    function getUser() { return currentUser; }

    return { init, getUser, handleLogout, showLoginScreen, showMainLayout };
})();

/* ============================================================
   Toast Notifications
   ============================================================ */
const Toast = (() => {
    function show(message, type = 'info', duration = 3500) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const icons = {
            success: '✓', error: '✕', warning: '⚠', info: 'ℹ'
        };

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || 'ℹ'}</span>
            <span class="toast-msg">${escapeHtml(message)}</span>
        `;

        container.appendChild(toast);

        // trigger animation
        requestAnimationFrame(() => toast.classList.add('show'));

        setTimeout(() => {
            toast.classList.remove('show');
            toast.addEventListener('transitionend', () => toast.remove());
        }, duration);
    }

    return { show };
})();

/* ============================================================
   Modal Utility
   ============================================================ */
const Modal = (() => {
    let _resolve = null;

    function show({ title, body, buttons = [] }) {
        const overlay = document.getElementById('modal-overlay');
        const box = overlay.querySelector('.modal-box');
        if (!overlay || !box) return;

        box.innerHTML = `
            <div class="modal-header">
                <h3>${escapeHtml(title || '')}</h3>
                <button class="modal-close" onclick="Modal.hide()">×</button>
            </div>
            <div class="modal-body">${body || ''}</div>
            ${buttons.length ? `<div class="modal-footer">${buttons.map(b =>
                `<button class="btn btn-${b.type || 'secondary'}" onclick="${b.onclick || 'Modal.hide()'}">${escapeHtml(b.label)}</button>`
            ).join('')}</div>` : ''}
        `;

        overlay.classList.add('active');
    }

    function hide(value) {
        const overlay = document.getElementById('modal-overlay');
        if (overlay) overlay.classList.remove('active');
        if (_resolve) { _resolve(value); _resolve = null; }
    }

    function confirm(message) {
        return new Promise(resolve => {
            _resolve = resolve;
            show({
                title: 'Confirmação',
                body: `<p>${escapeHtml(message)}</p>`,
                buttons: [
                    { label: 'Cancelar', type: 'secondary', onclick: 'Modal.hide(false)' },
                    { label: 'Confirmar', type: 'primary', onclick: 'Modal.hide(true)' }
                ]
            });
        });
    }

    return { show, hide, confirm };
})();

/* ============================================================
   Utility Helpers
   ============================================================ */
function escapeHtml(str) {
    if (!str) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(str).replace(/[&<>"']/g, c => map[c]);
}

function formatDate(d) {
    if (!d) return '—';
    const dt = new Date(d);
    return dt.toLocaleDateString('pt-BR') + ' ' + dt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

function formatDateShort(d) {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('pt-BR');
}

function truncate(str, len = 80) {
    if (!str) return '';
    return str.length > len ? str.substring(0, len) + '…' : str;
}

function riskColor(score) {
    if (score >= 80) return 'var(--danger)';
    if (score >= 60) return 'var(--warning)';
    if (score >= 40) return '#f59e0b';
    return 'var(--success)';
}

function badgeClass(status) {
    const map = {
        'pendente': 'warning',
        'em_analise': 'info',
        'investigando': 'primary',
        'concluida': 'success',
        'arquivada': 'secondary'
    };
    return map[status] || 'secondary';
}

function statusLabel(status) {
    const map = {
        'pendente': 'Pendente',
        'em_analise': 'Em Análise',
        'investigando': 'Investigando',
        'concluida': 'Concluída',
        'arquivada': 'Arquivada'
    };
    return map[status] || status;
}

/* ── DOM Ready ──────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => App.init());

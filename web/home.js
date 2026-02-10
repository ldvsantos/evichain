// =====================================================
// EviChain — Página Inicial do Sistema (home.js)
// =====================================================

// Detecta o base URL da API
function getApiBase() {
    if (window.location.hostname.includes('github.io')) return null;
    return window.location.origin;
}

document.addEventListener('DOMContentLoaded', function () {
    initMobileNav();
    loadSystemStats();
    loadRecentActivity();
});

// ── Mobile Nav Toggle ────────────────────────────────
function initMobileNav() {
    const toggle = document.getElementById('navToggle');
    const mobileNav = document.getElementById('mobileNav');
    if (!toggle || !mobileNav) return;

    toggle.addEventListener('click', function () {
        mobileNav.classList.toggle('open');
        const expanded = mobileNav.classList.contains('open');
        toggle.setAttribute('aria-expanded', String(expanded));
        toggle.innerHTML = expanded
            ? '<i class="fas fa-times"></i>'
            : '<i class="fas fa-bars"></i>';
    });
}

// ── System Stats (top banner) ────────────────────────
async function loadSystemStats() {
    const apiBase = getApiBase();
    if (!apiBase) {
        // Modo offline: mostrar dados demo
        const blocksEl = document.getElementById('statBlocks');
        const complaintsEl = document.getElementById('statComplaints');
        if (blocksEl) blocksEl.textContent = '12';
        if (complaintsEl) complaintsEl.textContent = '5';
        return;
    }
    try {
        const [healthRes, complaintsRes] = await Promise.all([
            fetch(apiBase + '/api/health'),
            fetch(apiBase + '/api/complaints')
        ]);

        if (healthRes.ok) {
            const health = await healthRes.json();
            const blocksEl = document.getElementById('statBlocks');
            if (blocksEl) blocksEl.textContent = health.total_blocks ?? '—';
        }

        if (complaintsRes.ok) {
            const data = await complaintsRes.json();
            const count = data.success && data.complaints ? data.complaints.length : 0;
            const el = document.getElementById('statComplaints');
            if (el) el.textContent = count;
        }
    } catch (err) {
        console.warn('Não foi possível carregar stats:', err.message);
    }
}

// ── Recent Activity ──────────────────────────────────
async function loadRecentActivity() {
    const list = document.getElementById('activityList');
    if (!list) return;

    const apiBase = getApiBase();

    // Demo data para modo offline
    if (!apiBase) {
        const demoItems = [
            { titulo: 'Exercício ilegal de profissão', categoria: 'Exercício Ilegal', ia_analysis: { analise_juridica: { gravidade: 'Alta' } } },
            { titulo: 'Negligência em atendimento', categoria: 'Negligência', ia_analysis: { analise_juridica: { gravidade: 'Média' } } },
            { titulo: 'Assédio em ambiente profissional', categoria: 'Assédio', ia_analysis: { analise_juridica: { gravidade: 'Urgente' } } },
        ];
        list.innerHTML = demoItems.map(function (c) {
            return `
                <div class="sys-activity-item">
                    <div class="sys-activity-badge ${getBadgeClass(c)}">
                        <i class="fas ${getBadgeIcon(c)}"></i>
                    </div>
                    <div class="sys-activity-text">
                        <strong>${escapeHtml(c.titulo)}</strong>
                        <p>${escapeHtml(c.categoria)}</p>
                    </div>
                    <span class="sys-activity-time">demo</span>
                </div>`;
        }).join('');
        return;
    }

    try {
        const res = await fetch(apiBase + '/api/complaints');
        if (!res.ok) throw new Error('Falha ao buscar denúncias');
        const data = await res.json();

        const complaints = data.success && data.complaints ? data.complaints : [];

        if (complaints.length === 0) {
            list.innerHTML = `
                <div class="sys-activity-empty">
                    <i class="fas fa-inbox"></i>
                    <p>Nenhuma atividade registrada ainda.</p>
                </div>`;
            return;
        }

        // Últimas 8 denúncias (mais recentes primeiro)
        const recent = complaints.slice(-8).reverse();

        list.innerHTML = recent.map(function (c) {
            const title = c.titulo || c.assunto || 'Denúncia sem título';
            const cat = c.categoria || 'Geral';
            const date = formatRelativeTime(c.timestamp);
            const badge = getBadgeClass(c);
            const icon = getBadgeIcon(c);

            return `
                <div class="sys-activity-item">
                    <div class="sys-activity-badge ${badge}">
                        <i class="fas ${icon}"></i>
                    </div>
                    <div class="sys-activity-text">
                        <strong>${escapeHtml(title)}</strong>
                        <p>${escapeHtml(cat)}</p>
                    </div>
                    <span class="sys-activity-time">${date}</span>
                </div>`;
        }).join('');

    } catch (err) {
        console.warn('Erro ao carregar atividade:', err.message);
        list.innerHTML = `
            <div class="sys-activity-empty">
                <i class="fas fa-exclamation-circle"></i>
                <p>Não foi possível carregar a atividade.</p>
            </div>`;
    }
}

// ── Refresh All ──────────────────────────────────────
function refreshAll() {
    loadSystemStats();
    loadRecentActivity();
}

// ── Helpers ──────────────────────────────────────────
function formatRelativeTime(ts) {
    if (!ts) return '';
    try {
        const d = new Date(ts);
        const diff = Date.now() - d.getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1) return 'agora';
        if (mins < 60) return mins + ' min';
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return hrs + 'h';
        const days = Math.floor(hrs / 24);
        if (days < 30) return days + 'd';
        return d.toLocaleDateString('pt-BR');
    } catch (_) {
        return '';
    }
}

function getBadgeClass(complaint) {
    const grav = (complaint.ia_analysis?.analise_juridica?.gravidade || '').toLowerCase();
    if (grav.includes('alta') || grav.includes('urgente')) return 'sys-badge-red';
    if (grav.includes('média') || grav.includes('media')) return 'sys-badge-amber';
    if (grav.includes('baixa')) return 'sys-badge-green';
    return 'sys-badge-blue';
}

function getBadgeIcon(complaint) {
    const cat = (complaint.categoria || '').toLowerCase();
    if (cat.includes('assédio') || cat.includes('assedio')) return 'fa-user-shield';
    if (cat.includes('negligência') || cat.includes('negligencia')) return 'fa-exclamation-triangle';
    if (cat.includes('fraude')) return 'fa-gavel';
    if (cat.includes('exercício') || cat.includes('exercicio')) return 'fa-id-badge';
    return 'fa-file-alt';
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

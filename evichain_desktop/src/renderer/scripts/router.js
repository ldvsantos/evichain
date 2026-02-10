/* ============================================================
   EviChain Desktop — SPA Router
   ============================================================ */

const Router = (() => {
    const routes = {};
    let currentPage = null;

    function register(name, renderFn) {
        routes[name] = renderFn;
    }

    async function navigate(page, params = {}) {
        if (!routes[page]) {
            console.warn(`[Router] Página não registrada: ${page}`);
            return;
        }

        // Atualizar sidebar
        document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });

        currentPage = page;
        const content = document.getElementById('content');
        if (!content) return;

        // Loading state
        content.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:200px;color:var(--text-dim)">Carregando…</div>';

        try {
            await routes[page](content, params);
        } catch (err) {
            console.error(`[Router] Erro ao renderizar "${page}":`, err);
            content.innerHTML = `
                <div class="page-header"><h2>Erro</h2></div>
                <div class="card" style="padding:20px;color:var(--danger)">
                    Não foi possível carregar esta página.<br>
                    <small style="color:var(--text-dim)">${escapeHtml(err.message)}</small>
                </div>
            `;
        }
    }

    function getCurrentPage() { return currentPage; }

    return { register, navigate, getCurrentPage };
})();

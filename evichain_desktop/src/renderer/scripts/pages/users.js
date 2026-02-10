/* ============================================================
   EviChain Desktop — Gerenciamento de Usuários Page
   ============================================================ */

Router.register('users', async (container) => {
    container.innerHTML = Components.loading();

    try {
        const users = await window.evichainAPI.users.list();

        container.innerHTML = `
            ${Components.pageHeader('Usuários', 'Gerenciamento de contas do sistema')}

            ${Components.toolbar({
                placeholder: 'Buscar usuário…',
                onSearch: term => filterUsers(term, users),
                actionLabel: '+ Novo Usuário',
                onAction: () => showUserForm()
            })}

            <div id="users-table">
                ${renderUsersTable(users)}
            </div>

            <div id="user-form-container"></div>
        `;
    } catch (err) {
        container.innerHTML = Components.pageHeader('Usuários') +
            `<div class="card" style="padding:20px;color:var(--danger)">Erro: ${escapeHtml(err.message)}</div>`;
    }
});

function renderUsersTable(users) {
    return Components.table({
        columns: ['ID', 'Nome', 'Usuário', 'Perfil', 'Status', 'Criado em', 'Ações'],
        rows: users,
        renderRow: u => `
            <td style="color:var(--text-dim)">${u.id}</td>
            <td style="font-weight:500">${escapeHtml(u.name || '—')}</td>
            <td>${escapeHtml(u.username)}</td>
            <td>${Components.badge(u.role || 'user', u.role === 'admin' ? 'primary' : 'secondary')}</td>
            <td>${Components.badge(u.active !== false ? 'Ativo' : 'Inativo', u.active !== false ? 'success' : 'danger')}</td>
            <td style="font-size:11px;color:var(--text-dim)">${formatDateShort(u.created_at)}</td>
            <td>
                <button class="btn btn-ghost btn-sm" onclick="showUserForm(${u.id})">Editar</button>
            </td>
        `,
        emptyText: 'Nenhum usuário cadastrado.'
    });
}

function filterUsers(term, all) {
    const t = term.toLowerCase();
    const filtered = t
        ? all.filter(u =>
            (u.name || '').toLowerCase().includes(t) ||
            (u.username || '').toLowerCase().includes(t) ||
            (u.role || '').toLowerCase().includes(t)
        )
        : all;
    document.getElementById('users-table').innerHTML = renderUsersTable(filtered);
}

async function showUserForm(userId) {
    let user = null;
    if (userId) {
        try {
            const users = await window.evichainAPI.users.list();
            user = users.find(u => u.id === userId);
        } catch (_) { }
    }

    Modal.show({
        title: user ? 'Editar Usuário' : 'Novo Usuário',
        body: `
            <form id="user-modal-form" style="min-width:350px">
                <div class="form-group">
                    <label class="form-label">Nome Completo</label>
                    <input type="text" id="uf-name" class="form-input" value="${escapeHtml(user?.name || '')}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Usuário (login)</label>
                    <input type="text" id="uf-username" class="form-input" value="${escapeHtml(user?.username || '')}" ${user ? 'readonly' : 'required'}>
                </div>
                ${!user ? `<div class="form-group">
                    <label class="form-label">Senha</label>
                    <input type="password" id="uf-password" class="form-input" required>
                </div>` : ''}
                <div class="form-group">
                    <label class="form-label">Perfil</label>
                    <select id="uf-role" class="form-select">
                        <option value="user" ${user?.role === 'user' ? 'selected' : ''}>Usuário</option>
                        <option value="admin" ${user?.role === 'admin' ? 'selected' : ''}>Administrador</option>
                    </select>
                </div>
            </form>
        `,
        buttons: [
            { label: 'Cancelar', type: 'secondary', onclick: 'Modal.hide()' },
            { label: 'Salvar', type: 'primary', onclick: 'saveUser(' + (userId || 'null') + ')' }
        ]
    });
}

async function saveUser(userId) {
    const name = document.getElementById('uf-name')?.value?.trim();
    const username = document.getElementById('uf-username')?.value?.trim();
    const password = document.getElementById('uf-password')?.value;
    const role = document.getElementById('uf-role')?.value;

    if (!name) { Toast.show('Informe o nome.', 'warning'); return; }

    try {
        if (userId) {
            Toast.show('Edição de perfil será implementada em breve.', 'info');
            Modal.hide();
            return;
        } else {
            if (!username || !password) { Toast.show('Preencha usuário e senha.', 'warning'); return; }
            await window.evichainAPI.users.create(username, password, role);
        }
        Modal.hide();
        Toast.show('Usuário salvo com sucesso!', 'success');
        Router.navigate('users');
    } catch (err) {
        Toast.show('Erro: ' + err.message, 'error');
    }
}

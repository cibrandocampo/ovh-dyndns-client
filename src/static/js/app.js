// API Client
const API = {
    token: localStorage.getItem('token'),

    setToken(token) {
        this.token = token;
        localStorage.setItem('token', token);
    },

    clearToken() {
        this.token = null;
        localStorage.removeItem('token');
        localStorage.removeItem('mustChangePassword');
    },

    async request(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(url, { ...options, headers });

        if (response.status === 401) {
            this.clearToken();
            showPage('login-page');
            throw new Error('Session expired');
        }

        return response;
    },

    async get(url) {
        return this.request(url);
    },

    async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
};

// Page Management
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    document.getElementById(pageId).classList.remove('hidden');
}

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
    document.getElementById(`${sectionId}-section`).classList.remove('hidden');

    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.section === sectionId) {
            link.classList.add('active');
        }
    });

    // Load section data
    switch (sectionId) {
        case 'status':
            loadStatus();
            break;
        case 'hosts':
            loadHosts();
            break;
        case 'history':
            loadHistoryHostnames();
            loadHistory();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// Login
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById('login-error');
    errorEl.textContent = '';

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (!response.ok) {
            errorEl.textContent = data.detail || 'Login failed';
            return;
        }

        API.setToken(data.access_token);

        if (data.must_change_password) {
            localStorage.setItem('mustChangePassword', 'true');
            showPage('change-password-page');
        } else {
            localStorage.removeItem('mustChangePassword');
            showPage('dashboard');
            showSection('status');
        }
    } catch (error) {
        errorEl.textContent = 'Connection error';
    }
});

// Change Password
document.getElementById('change-password-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById('change-password-error');
    errorEl.textContent = '';

    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    if (newPassword !== confirmPassword) {
        errorEl.textContent = 'Passwords do not match';
        return;
    }

    if (newPassword.length < 6) {
        errorEl.textContent = 'Password must be at least 6 characters';
        return;
    }

    try {
        const response = await API.post('/api/auth/change-password', {
            current_password: currentPassword,
            new_password: newPassword
        });

        const data = await response.json();

        if (!response.ok) {
            errorEl.textContent = data.detail || 'Failed to change password';
            return;
        }

        localStorage.removeItem('mustChangePassword');
        showPage('dashboard');
        showSection('status');
    } catch (error) {
        errorEl.textContent = 'Connection error';
    }
});

// Logout
document.getElementById('logout-link').addEventListener('click', (e) => {
    e.preventDefault();
    API.clearToken();
    document.getElementById('login-form').reset();
    showPage('login-page');
});

// Navigation
document.querySelectorAll('.nav-link[data-section]').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        showSection(link.dataset.section);
    });
});

// Status message helper
function showStatusMessage(message, type = 'info') {
    const messageEl = document.getElementById('status-message');
    messageEl.textContent = message;
    messageEl.className = `message ${type}`;
    messageEl.classList.remove('hidden');

    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageEl.classList.add('hidden');
    }, 5000);
}

// Status
async function loadStatus() {
    try {
        const response = await API.get('/api/status/');
        const data = await response.json();

        document.getElementById('current-ip').textContent = data.current_ip || 'Unknown';
        document.getElementById('last-check').textContent = data.last_check
            ? new Date(data.last_check).toLocaleString()
            : 'Never';
        document.getElementById('next-check').textContent = data.next_check
            ? new Date(data.next_check).toLocaleString()
            : '-';

        const tbody = document.querySelector('#host-status-table tbody');
        statusRows = data.hosts;
        tbody.innerHTML = statusRows.map((host, i) => {
            const klass = host.last_status === true ? 'status-success' : host.last_status === false ? 'status-error' : 'status-pending';
            const icon = host.last_status === true ? 'i-check-circle' : host.last_status === false ? 'i-x-circle' : 'i-clock';
            const label = host.last_status === true ? 'Success' : host.last_status === false ? 'Failed' : 'Pending';
            return `
            <tr class="tr-clickable" data-idx="${i}">
                <td>${escapeHtml(host.hostname)}</td>
                <td><time datetime="${host.last_update || ''}" title="${escapeHtml(formatFullTime(host.last_update))}">${escapeHtml(formatRelativeTime(host.last_update))}</time></td>
                <td class="${klass}">
                    <svg class="icon icon-sm"><use href="/static/icons.svg#${icon}"/></svg>
                    <span class="status-label">${label}</span>
                </td>
                <td class="col-secondary">${host.last_error ? escapeHtml(host.last_error) : '-'}</td>
                <td class="col-actions">
                    <button class="btn-icon btn-icon-done" onclick="forceUpdateHost('${escapeHtml(host.hostname)}')" aria-label="Force update">
                        <svg class="icon icon-sm"><use href="/static/icons.svg#i-refresh-cw"/></svg>
                    </button>
                </td>
            </tr>`;
        }).join('');
    } catch (error) {
        console.error('Failed to load status:', error);
    }
}

async function forceUpdateHost(hostname) {
    const btn = event.target.closest('button');
    btn.disabled = true;
    btn.dataset.loading = 'true';

    try {
        const response = await API.post(`/api/status/trigger/${encodeURIComponent(hostname)}`, {});
        const data = await response.json();

        if (data.success) {
            showStatusMessage(data.message, 'success');
        } else {
            showStatusMessage(data.message, 'error');
        }

        loadStatus();
    } catch (error) {
        showStatusMessage('Failed to update host', 'error');
    } finally {
        btn.disabled = false;
        btn.dataset.loading = 'false';
    }
}

document.getElementById('trigger-update').addEventListener('click', async () => {
    const btn = document.getElementById('trigger-update');
    btn.disabled = true;
    btn.dataset.loading = 'true';

    try {
        const response = await API.post('/api/status/trigger', {});
        const data = await response.json();

        if (data.success) {
            showStatusMessage(data.message, 'success');
        } else {
            showStatusMessage(data.message, 'error');
        }

        loadStatus();
    } catch (error) {
        showStatusMessage('Failed to trigger update', 'error');
    } finally {
        btn.disabled = false;
        btn.dataset.loading = 'false';
    }
});

// Hosts
async function loadHosts() {
    try {
        const response = await API.get('/api/hosts/');
        const data = await response.json();

        const tbody = document.querySelector('#hosts-table tbody');
        hostsRows = data;
        tbody.innerHTML = hostsRows.map((host, i) => `
            <tr class="tr-clickable" data-idx="${i}">
                <td class="col-secondary">${host.id}</td>
                <td>${escapeHtml(host.hostname)}</td>
                <td class="col-secondary">${escapeHtml(host.username)}</td>
                <td class="col-secondary"><time datetime="${host.created_at || ''}" title="${escapeHtml(formatFullTime(host.created_at))}">${escapeHtml(host.created_at ? formatFullTime(host.created_at) : '-')}</time></td>
                <td class="col-actions">
                    <span class="row-actions">
                        <button class="btn-icon" onclick="editHost(${host.id})" aria-label="Edit host">
                            <svg class="icon icon-sm"><use href="/static/icons.svg#i-pencil"/></svg>
                        </button>
                        <button class="btn-icon btn-icon-delete" onclick="confirmDeleteHost(${host.id}, '${escapeHtml(host.hostname)}')" aria-label="Delete host">
                            <svg class="icon icon-sm"><use href="/static/icons.svg#i-trash-2"/></svg>
                        </button>
                    </span>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load hosts:', error);
    }
}

document.getElementById('add-host-btn').addEventListener('click', () => {
    document.getElementById('modal-title').textContent = 'Add Host';
    document.getElementById('host-form').reset();
    document.getElementById('host-id').value = '';
    document.getElementById('host-password').required = true;
    document.getElementById('password-hint').classList.add('hidden');
    document.getElementById('host-error').textContent = '';
    document.getElementById('host-modal').classList.remove('hidden');
});

async function editHost(id) {
    try {
        const response = await API.get(`/api/hosts/${id}`);
        const host = await response.json();

        document.getElementById('modal-title').textContent = 'Edit Host';
        document.getElementById('host-id').value = host.id;
        document.getElementById('host-hostname').value = host.hostname;
        document.getElementById('host-username').value = host.username;
        document.getElementById('host-password').value = '';
        document.getElementById('host-password').required = false;
        document.getElementById('password-hint').classList.remove('hidden');
        document.getElementById('host-error').textContent = '';
        document.getElementById('host-modal').classList.remove('hidden');
    } catch (error) {
        alert('Failed to load host');
    }
}

document.getElementById('host-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById('host-error');
    errorEl.textContent = '';

    const id = document.getElementById('host-id').value;
    const data = {
        hostname: document.getElementById('host-hostname').value,
        username: document.getElementById('host-username').value
    };

    const password = document.getElementById('host-password').value;
    if (password) {
        data.password = password;
    }

    try {
        let response;
        if (id) {
            response = await API.put(`/api/hosts/${id}`, data);
        } else {
            data.password = password;
            response = await API.post('/api/hosts/', data);
        }

        if (!response.ok) {
            const error = await response.json();
            errorEl.textContent = error.detail || 'Failed to save host';
            return;
        }

        document.getElementById('host-modal').classList.add('hidden');
        loadHosts();
    } catch (error) {
        errorEl.textContent = 'Connection error';
    }
});

let deleteHostId = null;

function confirmDeleteHost(id, hostname) {
    deleteHostId = id;
    document.getElementById('delete-hostname').textContent = hostname;
    document.getElementById('delete-modal').classList.remove('hidden');
}

document.getElementById('confirm-delete').addEventListener('click', async () => {
    if (!deleteHostId) return;

    try {
        await API.delete(`/api/hosts/${deleteHostId}`);
        document.getElementById('delete-modal').classList.add('hidden');
        deleteHostId = null;
        loadHosts();
    } catch (error) {
        alert('Failed to delete host');
    }
});

document.getElementById('cancel-delete').addEventListener('click', () => {
    document.getElementById('delete-modal').classList.add('hidden');
    deleteHostId = null;
});

// Modal close
document.querySelectorAll('.close-modal').forEach(el => {
    el.addEventListener('click', () => {
        el.closest('.modal').classList.add('hidden');
    });
});

// Row-click delegation for the shared details modal. Per-table mappers
// translate the row index into the dl items shown in the modal.
const rowDetailHandlers = {
    'host-status-table': {
        title: 'Host status',
        items: (h) => [
            { label: 'Hostname', value: h.hostname },
            { label: 'Last update', value: formatFullTime(h.last_update) },
            {
                label: 'Status',
                html: true,
                value: h.last_status === true
                    ? '<span class="status-success">Success</span>'
                    : h.last_status === false
                        ? '<span class="status-error">Failed</span>'
                        : '<span class="status-pending">Pending</span>',
            },
            { label: 'Error', value: h.last_error || '-' },
        ],
        source: () => statusRows,
    },
    'hosts-table': {
        title: 'Host',
        items: (h) => [
            { label: 'ID', value: String(h.id) },
            { label: 'Hostname', value: h.hostname },
            { label: 'Username', value: h.username },
            { label: 'Created at', value: formatFullTime(h.created_at) },
        ],
        source: () => hostsRows,
    },
    'history-table': {
        title: 'History entry',
        items: (e) => [
            { label: 'Timestamp', value: formatFullTime(e.timestamp) },
            { label: 'Action', value: e.action },
            { label: 'Hostname', value: e.hostname || '-' },
            { label: 'IP', value: e.ip || '-' },
            { label: 'Details', value: e.details || '-' },
        ],
        source: () => historyRows,
    },
};

Object.entries(rowDetailHandlers).forEach(([tableId, cfg]) => {
    const tbody = document.querySelector(`#${tableId} tbody`);
    if (!tbody) return;
    tbody.addEventListener('click', (e) => {
        // Don't intercept row-action buttons or links inside the row.
        if (e.target.closest('button, a')) return;
        const tr = e.target.closest('tr.tr-clickable');
        if (!tr) return;
        const idx = Number(tr.dataset.idx);
        const row = cfg.source()[idx];
        if (!row) return;
        openDetailsModal(cfg.title, cfg.items(row));
    });
});

// Row caches for the shared details modal (filled by each renderer)
let statusRows = [];
let hostsRows = [];
let historyRows = [];

// History
let historyPage = 0;
let historyHostnameFilter = '';
const historyLimit = 20;

async function loadHistoryHostnames() {
    try {
        const response = await API.get('/api/history/hostnames');
        if (!response.ok) return;
        const list = await response.json();
        const select = document.getElementById('history-filter-hostname');
        const previous = historyHostnameFilter;
        // Keep "All hosts" first, then one option per hostname (alpha-sorted by backend).
        select.innerHTML = '<option value="">All hosts</option>' +
            list.map(h => `<option value="${escapeHtml(h)}">${escapeHtml(h)}</option>`).join('');
        // Restore the user's choice if it still exists; otherwise reset to "All hosts".
        if (previous && list.includes(previous)) {
            select.value = previous;
        } else {
            select.value = '';
            historyHostnameFilter = '';
        }
    } catch (error) {
        console.error('Failed to load history hostnames:', error);
    }
}

async function loadHistory(page = 0) {
    historyPage = page;

    try {
        const params = new URLSearchParams({
            limit: String(historyLimit),
            offset: String(page * historyLimit),
        });
        if (historyHostnameFilter) params.set('hostname', historyHostnameFilter);
        const response = await API.get(`/api/history/?${params.toString()}`);
        const data = await response.json();

        const tbody = document.querySelector('#history-table tbody');
        historyRows = data.entries;
        tbody.innerHTML = historyRows.map((entry, i) => `
            <tr class="tr-clickable" data-idx="${i}">
                <td><time datetime="${entry.timestamp || ''}" title="${escapeHtml(formatFullTime(entry.timestamp))}">${escapeHtml(formatRelativeTime(entry.timestamp))}</time></td>
                <td>${escapeHtml(entry.action)}</td>
                <td>${entry.hostname ? escapeHtml(entry.hostname) : '-'}</td>
                <td class="col-secondary">${escapeHtml(entry.ip || '-')}</td>
                <td class="col-secondary">${entry.details ? escapeHtml(entry.details) : '-'}</td>
            </tr>
        `).join('');

        document.getElementById('page-info').textContent = `Page ${page + 1} of ${Math.ceil(data.total / historyLimit) || 1}`;
        document.getElementById('prev-page').disabled = page === 0;
        document.getElementById('next-page').disabled = (page + 1) * historyLimit >= data.total;
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

document.getElementById('prev-page').addEventListener('click', () => {
    if (historyPage > 0) loadHistory(historyPage - 1);
});

document.getElementById('next-page').addEventListener('click', () => {
    loadHistory(historyPage + 1);
});

document.getElementById('history-filter-hostname').addEventListener('change', (e) => {
    historyHostnameFilter = e.target.value;
    loadHistory(0);
});

// Settings
async function loadSettings() {
    try {
        const response = await API.get('/api/settings/');
        const data = await response.json();

        document.getElementById('update-interval').value = data.update_interval;
        document.getElementById('logger-level').value = data.logger_level;
    } catch (error) {
        console.error('Failed to load settings:', error);
    }

    // App version is public (no auth) and rendered as small muted text at
    // the bottom of the settings card. Failures are silent — the placeholder
    // 'dev' from index.html stays visible.
    try {
        const response = await fetch('/api/version');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('app-version').textContent = data.version;
        }
    } catch (error) {
        // ignore — keep the static placeholder
    }
}

document.getElementById('settings-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const messageEl = document.getElementById('settings-message');
    messageEl.textContent = '';
    messageEl.className = 'success-message';

    const data = {
        update_interval: parseInt(document.getElementById('update-interval').value),
        logger_level: document.getElementById('logger-level').value
    };

    try {
        const response = await API.put('/api/settings/', data);

        if (!response.ok) {
            const error = await response.json();
            messageEl.textContent = error.detail || 'Failed to save settings';
            messageEl.className = 'error-message';
            return;
        }

        messageEl.textContent = 'Settings saved successfully. Changes will take effect on next update cycle.';
    } catch (error) {
        messageEl.textContent = 'Connection error';
        messageEl.className = 'error-message';
    }
});

// Utility
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatRelativeTime(iso) {
    if (!iso) return 'Never';
    const then = new Date(iso).getTime();
    if (Number.isNaN(then)) return '-';
    const diffSec = Math.round((Date.now() - then) / 1000);
    const abs = Math.abs(diffSec);
    if (abs < 60) return 'just now';
    if (abs < 3600) return `${Math.round(abs / 60)}m`;
    if (abs < 86400) return `${Math.round(abs / 3600)}h`;
    if (abs < 86400 * 7) return `${Math.round(abs / 86400)}d`;
    return new Date(iso).toLocaleDateString();
}

function formatFullTime(iso) {
    if (!iso) return 'Never';
    const d = new Date(iso);
    return Number.isNaN(d.getTime()) ? '-' : d.toLocaleString();
}

// Open the shared row-details modal. `items` is [{label, value, html?}, …];
// when `html` is true the value is inserted as-is, otherwise it's escaped.
function openDetailsModal(title, items) {
    document.getElementById('details-modal-title').textContent = title;
    const body = document.getElementById('details-modal-body');
    body.innerHTML = items.map(it => `
        <dt>${escapeHtml(it.label)}</dt>
        <dd>${it.html ? it.value : escapeHtml(it.value ?? '-')}</dd>
    `).join('');
    document.getElementById('details-modal').classList.remove('hidden');
}

// Initialize
(function init() {
    if (API.token) {
        const mustChange = localStorage.getItem('mustChangePassword') === 'true';
        if (mustChange) {
            showPage('change-password-page');
        } else {
            showPage('dashboard');
            showSection('status');
        }
    } else {
        showPage('login-page');
    }
})();

// Make functions globally accessible
window.editHost = editHost;
window.confirmDeleteHost = confirmDeleteHost;
window.forceUpdateHost = forceUpdateHost;

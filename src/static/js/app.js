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
        tbody.innerHTML = data.hosts.map(host => `
            <tr>
                <td>${escapeHtml(host.hostname)}</td>
                <td>${host.last_update ? new Date(host.last_update).toLocaleString() : 'Never'}</td>
                <td class="${host.last_status === true ? 'status-success' : host.last_status === false ? 'status-error' : 'status-pending'}">
                    ${host.last_status === true ? 'Success' : host.last_status === false ? 'Failed' : 'Pending'}
                </td>
                <td>${host.last_error ? escapeHtml(host.last_error) : '-'}</td>
                <td>
                    <button class="btn btn-small btn-primary" onclick="forceUpdateHost('${escapeHtml(host.hostname)}')">Force Update</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load status:', error);
    }
}

async function forceUpdateHost(hostname) {
    const btn = event.target;
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Updating...';

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
        btn.textContent = originalText;
    }
}

document.getElementById('trigger-update').addEventListener('click', async () => {
    const btn = document.getElementById('trigger-update');
    btn.disabled = true;
    btn.textContent = 'Updating...';

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
        btn.textContent = 'Trigger Update Now';
    }
});

// Hosts
async function loadHosts() {
    try {
        const response = await API.get('/api/hosts/');
        const data = await response.json();

        const tbody = document.querySelector('#hosts-table tbody');
        tbody.innerHTML = data.map(host => `
            <tr>
                <td>${host.id}</td>
                <td>${escapeHtml(host.hostname)}</td>
                <td>${escapeHtml(host.username)}</td>
                <td>${host.created_at ? new Date(host.created_at).toLocaleString() : '-'}</td>
                <td>
                    <button class="btn btn-small" onclick="editHost(${host.id})">Edit</button>
                    <button class="btn btn-small btn-danger" onclick="confirmDeleteHost(${host.id}, '${escapeHtml(host.hostname)}')">Delete</button>
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

// History
let historyPage = 0;
const historyLimit = 20;

async function loadHistory(page = 0) {
    historyPage = page;

    try {
        const response = await API.get(`/api/history/?limit=${historyLimit}&offset=${page * historyLimit}`);
        const data = await response.json();

        const tbody = document.querySelector('#history-table tbody');
        tbody.innerHTML = data.entries.map(entry => `
            <tr>
                <td>${entry.timestamp ? new Date(entry.timestamp).toLocaleString() : '-'}</td>
                <td>${escapeHtml(entry.action)}</td>
                <td>${entry.hostname ? escapeHtml(entry.hostname) : '-'}</td>
                <td>${entry.ip || '-'}</td>
                <td>${entry.details ? escapeHtml(entry.details) : '-'}</td>
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

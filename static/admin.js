// API Base URL
const API_BASE = window.location.origin;

// State
let users = [];
let apiKeys = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupLogout();
    loadUsers();
    loadAPIKeys();

    // Setup form handlers
    document.getElementById('create-user-form').addEventListener('submit', handleCreateUser);
    document.getElementById('create-key-form').addEventListener('submit', handleCreateKey);
    document.getElementById('filter-user').addEventListener('change', handleFilterKeys);
    document.getElementById('batch-create-btn').addEventListener('click', handleBatchCreate);
});

// Fetch wrapper with authentication error handling
async function fetchWithAuth(url, options = {}) {
    options.credentials = 'include';  // Include cookies

    const response = await fetch(url, options);

    // Handle authentication errors
    if (response.status === 401) {
        showAlert('Session expired. Please login again.', 'error');
        setTimeout(() => {
            window.location.href = '/admin/login-page';
        }, 2000);
        throw new Error('Authentication required');
    }

    return response;
}

// Logout functionality
function setupLogout() {
    // Add logout button to header if not exists
    const header = document.querySelector('.header');
    if (header && !document.getElementById('logout-btn')) {
        const logoutBtn = document.createElement('button');
        logoutBtn.id = 'logout-btn';
        logoutBtn.className = 'btn btn-secondary';
        logoutBtn.textContent = 'Logout';
        logoutBtn.style.cssText = 'position: absolute; top: 20px; right: 20px;';
        logoutBtn.addEventListener('click', handleLogout);
        header.style.position = 'relative';
        header.appendChild(logoutBtn);
    }
}

async function handleLogout() {
    try {
        await fetchWithAuth('/admin/logout', { method: 'POST' });
        showAlert('Logged out successfully', 'success');
        setTimeout(() => {
            window.location.href = '/admin/login-page';
        }, 1000);
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Tab Management
function setupTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        }
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// Alert Management
function showAlert(message, type = 'success') {
    const alert = document.getElementById('alert');
    alert.className = `alert alert-${type} show`;
    alert.textContent = message;

    setTimeout(() => {
        alert.classList.remove('show');
    }, 5000);
}

// Users Management
async function loadUsers() {
    try {
        const response = await fetchWithAuth(`${API_BASE}/admin/users`);
        const data = await response.json();
        users = data.users;

        displayUsers(users);
        populateUserSelects();

        document.getElementById('users-loading').style.display = 'none';
        document.getElementById('users-list').style.display = 'block';
    } catch (error) {
        console.error('Error loading users:', error);
        showAlert('Failed to load users', 'error');
    }
}

function displayUsers(usersList) {
    const tbody = document.getElementById('users-table-body');

    if (usersList.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    <div class="empty-state-icon">👤</div>
                    <div>No users found. Create your first user above!</div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = usersList.map(user => `
        <tr>
            <td>${user.id}</td>
            <td><strong>${user.username}</strong></td>
            <td>${user.email || '-'}</td>
            <td>${formatDate(user.created_at)}</td>
            <td>
                <span class="badge ${user.is_active ? 'badge-success' : 'badge-danger'}">
                    ${user.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>
                <div class="actions">
                    <button class="btn btn-primary btn-sm" onclick="viewUserKeys(${user.id})">
                        View Keys
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

async function handleCreateUser(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;

    try {
        const url = `${API_BASE}/admin/users?username=${encodeURIComponent(username)}` +
                    (email ? `&email=${encodeURIComponent(email)}` : '');

        const response = await fetchWithAuth(url, { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            // Show the API key in a prominent alert (only time it's shown!)
            const alertDiv = document.getElementById('alert');
            alertDiv.className = 'alert alert-warning show';
            alertDiv.innerHTML = `
                <strong>✅ User "${username}" created successfully!</strong><br><br>
                <strong>⚠️ SAVE THIS API KEY - IT WILL NOT BE SHOWN AGAIN!</strong><br><br>
                <div class="code-block">${data.api_key}</div>
                <br>
                <small>A default API key has been automatically generated for this user. Copy it now and store it securely.</small>
            `;

            document.getElementById('create-user-form').reset();
            await loadUsers();
            await loadAPIKeys(); // Refresh keys list too
        } else {
            showAlert(data.detail || 'Failed to create user', 'error');
        }
    } catch (error) {
        console.error('Error creating user:', error);
        showAlert('Failed to create user', 'error');
    }
}

async function handleBatchCreate() {
    const fileInput = document.getElementById('batch-csv-file');
    const textInput = document.getElementById('batch-csv-text');
    const btn = document.getElementById('batch-create-btn');

    try {
        btn.disabled = true;
        btn.textContent = 'Creating users...';

        const formData = new FormData();

        // Check if file is uploaded
        if (fileInput.files && fileInput.files.length > 0) {
            formData.append('csv_file', fileInput.files[0]);
        }
        // Otherwise check if text is provided
        else if (textInput.value.trim()) {
            formData.append('csv_text', textInput.value.trim());
        }
        else {
            showAlert('Please upload a CSV file or paste CSV text', 'error');
            btn.disabled = false;
            btn.textContent = 'Batch Create Users';
            return;
        }

        const response = await fetchWithAuth(`${API_BASE}/admin/users/batch`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            // Download the result CSV
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'users_with_keys.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showAlert('Batch user creation completed! Download the CSV with API keys.', 'success');

            // Clear inputs
            fileInput.value = '';
            textInput.value = '';

            // Reload users and keys
            await loadUsers();
            await loadAPIKeys();
        } else {
            const data = await response.json();
            showAlert(data.detail || 'Batch creation failed', 'error');
        }
    } catch (error) {
        console.error('Batch creation error:', error);
        showAlert('Batch creation failed', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Batch Create Users';
    }
}

function populateUserSelects() {
    const selects = [
        document.getElementById('key-user-id'),
        document.getElementById('filter-user')
    ];

    selects.forEach(select => {
        const currentValue = select.value;
        const isFilter = select.id === 'filter-user';

        // Keep the first option (placeholder or "All Users")
        const firstOption = select.options[0];
        select.innerHTML = '';
        select.appendChild(firstOption);

        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = `${user.username} (ID: ${user.id})`;
            select.appendChild(option);
        });

        // Restore previous selection
        if (currentValue) {
            select.value = currentValue;
        }
    });
}

function viewUserKeys(userId) {
    switchTab('keys');
    document.getElementById('filter-user').value = userId;
    handleFilterKeys();
}

// API Keys Management
async function loadAPIKeys(userId = null) {
    try {
        const url = userId
            ? `${API_BASE}/admin/api-keys?user_id=${userId}`
            : `${API_BASE}/admin/api-keys`;

        const response = await fetchWithAuth(url);
        const data = await response.json();
        apiKeys = data.api_keys;

        displayAPIKeys(apiKeys);
        populateUsageKeySelect();

        document.getElementById('keys-loading').style.display = 'none';
        document.getElementById('keys-list').style.display = 'block';
    } catch (error) {
        console.error('Error loading API keys:', error);
        showAlert('Failed to load API keys', 'error');
    }
}

function displayAPIKeys(keysList) {
    const tbody = document.getElementById('keys-table-body');

    if (keysList.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="empty-state">
                    <div class="empty-state-icon">🔑</div>
                    <div>No API keys found. Create your first key above!</div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = keysList.map(key => `
        <tr>
            <td>${key.id}</td>
            <td>${key.user_id}</td>
            <td><code class="key-display">${key.key_prefix}...</code></td>
            <td>${key.name || '-'}</td>
            <td>${formatDate(key.created_at)}</td>
            <td>${key.last_used_at ? formatDate(key.last_used_at) : 'Never'}</td>
            <td>
                <span class="badge ${key.is_active ? 'badge-success' : 'badge-danger'}">
                    ${key.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>
                <div class="actions">
                    ${key.is_active ? `
                        <button class="btn btn-danger btn-sm" onclick="deactivateKey(${key.id})">
                            Deactivate
                        </button>
                    ` : ''}
                </div>
            </td>
        </tr>
    `).join('');
}

async function handleCreateKey(e) {
    e.preventDefault();

    const userId = document.getElementById('key-user-id').value;
    const keyName = document.getElementById('key-name').value;

    if (!userId) {
        showAlert('Please select a user', 'error');
        return;
    }

    try {
        const url = `${API_BASE}/admin/api-keys?user_id=${userId}` +
                    (keyName ? `&name=${encodeURIComponent(keyName)}` : '');

        const response = await fetchWithAuth(url, { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            // Show the API key in an alert (only time it's shown!)
            const alertDiv = document.getElementById('alert');
            alertDiv.className = 'alert alert-warning show';
            alertDiv.innerHTML = `
                <strong>⚠️ SAVE THIS API KEY - IT WILL NOT BE SHOWN AGAIN!</strong><br><br>
                <div class="code-block">${data.api_key}</div>
                <br>
                <small>Copy this key now and store it securely.</small>
            `;

            document.getElementById('create-key-form').reset();
            await loadAPIKeys();
        } else {
            showAlert(data.detail || 'Failed to create API key', 'error');
        }
    } catch (error) {
        console.error('Error creating API key:', error);
        showAlert('Failed to create API key', 'error');
    }
}

async function deactivateKey(keyId) {
    if (!confirm('Are you sure you want to deactivate this API key? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetchWithAuth(`${API_BASE}/admin/api-keys/${keyId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('API key deactivated successfully', 'success');
            await loadAPIKeys();
        } else {
            const data = await response.json();
            showAlert(data.detail || 'Failed to deactivate API key', 'error');
        }
    } catch (error) {
        console.error('Error deactivating API key:', error);
        showAlert('Failed to deactivate API key', 'error');
    }
}

function handleFilterKeys() {
    const userId = document.getElementById('filter-user').value;
    if (userId) {
        loadAPIKeys(parseInt(userId));
    } else {
        loadAPIKeys();
    }
}

function populateUsageKeySelect() {
    const select = document.getElementById('usage-key-id');
    const currentValue = select.value;

    select.innerHTML = '<option value="">Select an API key...</option>';

    apiKeys.forEach(key => {
        const user = users.find(u => u.id === key.user_id);
        const userName = user ? user.username : `User ${key.user_id}`;
        const option = document.createElement('option');
        option.value = key.id;
        option.textContent = `${userName} - ${key.name || 'Unnamed'} (${key.key_prefix}...)`;
        select.appendChild(option);
    });

    if (currentValue) {
        select.value = currentValue;
    }
}

// Usage Statistics
async function loadUsageStats() {
    const keyId = document.getElementById('usage-key-id').value;

    if (!keyId) {
        showAlert('Please select an API key', 'error');
        return;
    }

    document.getElementById('usage-loading').style.display = 'block';
    document.getElementById('usage-stats').style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/usage/api-key/${keyId}`);
        const data = await response.json();

        if (response.ok) {
            displayUsageStats(data);
            document.getElementById('usage-stats').style.display = 'block';
        } else {
            showAlert('Failed to load usage statistics', 'error');
        }
    } catch (error) {
        console.error('Error loading usage stats:', error);
        showAlert('Failed to load usage statistics', 'error');
    } finally {
        document.getElementById('usage-loading').style.display = 'none';
    }
}

function displayUsageStats(data) {
    document.getElementById('stat-requests').textContent = formatNumber(data.total_requests);
    document.getElementById('stat-input').textContent = formatNumber(data.total_input_tokens);
    document.getElementById('stat-output').textContent = formatNumber(data.total_output_tokens);
    document.getElementById('stat-total').textContent = formatNumber(data.total_tokens);
}

// Utility Functions
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatNumber(num) {
    if (num === undefined || num === null) return '0';
    return num.toLocaleString('en-US');
}

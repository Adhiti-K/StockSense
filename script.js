// StockSense Frontend Logic

let pendingDeleteRow = null;
let stockChart = null;

document.addEventListener('DOMContentLoaded', () => {
    checkAuthStatus();
    // Close profile menu on outside click
    document.addEventListener('click', (e) => {
        const profileWrapper = document.querySelector('.profile-wrapper');
        if (profileWrapper && !profileWrapper.contains(e.target)) {
            const menu = document.getElementById('profileMenu');
            if (menu) menu.classList.remove('show');
        }
    });
});

// 1. AUTHENTICATION LOGIC
function checkAuthStatus() {
    const isLoggedIn = localStorage.getItem('stocksense_logged_in') === 'true';
    const loginScreen = document.getElementById('loginScreen');

    if (isLoggedIn) {
        if (loginScreen) loginScreen.style.display = 'none';
        initChart();
        updateProductStats();
    } else {
        if (loginScreen) loginScreen.style.display = 'flex';
    }
}

function handleLogin(e) {
    if (e) e.preventDefault();
    const emailInput = document.getElementById('loginEmail');
    const passwordInput = document.getElementById('loginPassword');
    const errorMsg = document.getElementById('loginError');

    const email = emailInput ? emailInput.value.trim() : '';
    const password = passwordInput ? passwordInput.value.trim() : '';

    // Demo credentials: admin@stocksense.com / admin123
    if (email === 'admin@stocksense.com' && password === 'admin123') {
        localStorage.setItem('stocksense_logged_in', 'true');
        localStorage.setItem('stocksense_user_email', email);
        
        if (errorMsg) errorMsg.style.display = 'none';
        const loginScreen = document.getElementById('loginScreen');
        if (loginScreen) loginScreen.style.display = 'none';

        showToast('Logged in successfully!');
        showPage('dashboard');
        initChart();
        updateProductStats();
    } else {
        if (errorMsg) {
            errorMsg.innerText = 'Invalid email or password. Use demo credentials.';
            errorMsg.style.display = 'block';
        }
    }
}

function logout() {
    localStorage.removeItem('stocksense_logged_in');
    localStorage.removeItem('stocksense_user_email');
    
    const menu = document.getElementById('profileMenu');
    if (menu) menu.classList.remove('show');

    const loginScreen = document.getElementById('loginScreen');
    if (loginScreen) loginScreen.style.display = 'flex';

    showToast('Logged out successfully');
}

function toggleProfileMenu() {
    const menu = document.getElementById('profileMenu');
    if (menu) menu.classList.toggle('show');
}

// 2. PAGE NAVIGATION
function showPage(pageId) {
    // Hide all pages
    const pages = document.querySelectorAll('.page');
    pages.forEach(p => p.classList.remove('active-page'));

    // Deactivate nav items
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(n => n.classList.remove('active'));

    // Show target page
    const targetPage = document.getElementById(pageId);
    if (targetPage) targetPage.classList.add('active-page');

    // Update title
    const pageTitle = document.getElementById('pageTitle');
    const titleMap = {
        'dashboard': 'Inventory Dashboard',
        'products': 'Product Management',
        'receipts': 'Stock Receipts',
        'deliveries': 'Stock Deliveries',
        'transfers': 'Internal Transfers',
        'adjustments': 'Stock Adjustments',
        'ledger': 'Stock Movement Ledger'
    };
    if (pageTitle && titleMap[pageId]) {
        pageTitle.innerText = titleMap[pageId];
    }

    // Highlight nav button
    navItems.forEach(btn => {
        if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(pageId)) {
            btn.classList.add('active');
        }
    });
}

// 3. SEARCH & PRODUCTS MANAGEMENT
function searchProducts() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    const rows = document.querySelectorAll('#productTable tbody tr');

    rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

function addProduct() {
    const name = prompt('Enter Product Name:', 'New Stock Item');
    if (!name) return;

    const sku = prompt('Enter SKU Code:', 'SKU-' + Math.floor(1000 + Math.random() * 9000));
    if (!sku) return;

    const tbody = document.querySelector('#productTable tbody');
    if (!tbody) return;

    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><strong>${name}</strong></td>
        <td>${sku}</td>
        <td>Electronics</td>
        <td>25</td>
        <td><span class="badge available">Available</span></td>
        <td>10</td>
        <td><button class="delete-btn" onclick="confirmDelete(this)">🗑 Delete</button></td>
    `;
    tbody.prepend(tr);

    updateProductStats();
    showToast(`Product '${name}' added successfully`);
}

function updateProductStats() {
    const rows = document.querySelectorAll('#productTable tbody tr');
    const totalEl = document.getElementById('totalProducts');
    if (totalEl) totalEl.innerText = rows.length;
}

// 4. DELETE FUNCTIONALITY
function confirmDelete(btn) {
    pendingDeleteRow = btn.closest('tr');
    const overlay = document.getElementById('confirmOverlay');
    if (overlay) overlay.classList.add('active');
}

function closeConfirmModal() {
    pendingDeleteRow = null;
    const overlay = document.getElementById('confirmOverlay');
    if (overlay) overlay.classList.remove('active');
}

function executeDelete() {
    if (pendingDeleteRow) {
        const isProductTable = pendingDeleteRow.closest('#productTable') !== null;
        pendingDeleteRow.remove();
        pendingDeleteRow = null;

        if (isProductTable) {
            updateProductStats();
        }

        showToast('Deleted successfully');
    }
    closeConfirmModal();
}

// 5. TOAST NOTIFICATION
function showToast(message) {
    const toast = document.getElementById('toast');
    if (!toast) return;

    toast.innerHTML = `<span>✓</span> ${message}`;
    toast.style.display = 'flex';

    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

// 6. CHART INITIALIZATION
function initChart() {
    const canvas = document.getElementById('stockChart');
    if (!canvas || stockChart) return;

    const ctx = canvas.getContext('2d');
    stockChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [
                {
                    label: 'Receipts',
                    data: [65, 45, 75, 50, 80, 60, 90],
                    backgroundColor: '#6366f1',
                    borderRadius: 6
                },
                {
                    label: 'Deliveries',
                    data: [40, 30, 55, 35, 60, 45, 70],
                    backgroundColor: '#a855f7',
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8', font: { family: 'system-ui' } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

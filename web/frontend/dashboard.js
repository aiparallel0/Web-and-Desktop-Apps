/**
 * Dashboard JavaScript - Professional Government Style
 * Handles real API integration for dashboard data and receipt management
 * NO emojis, NO fake data, clean professional design
 */

// =============================================================================
// CONFIGURATION & CONSTANTS
// =============================================================================

const API_BASE_URL = window.location.origin;
const API_TIMEOUT = 30000; // 30 seconds

const PLAN_LIMITS = {
    'free': { receipts: 10, storage: 104857600 }, // 100 MB
    'pro': { receipts: 500, storage: 5368709120 }, // 5 GB
    'business': { receipts: 2000, storage: 21474836480 }, // 20 GB
    'enterprise': { receipts: -1, storage: -1 } // Unlimited
};

const MODEL_NAMES = {
    'ocr_tesseract': 'Tesseract OCR',
    'ocr_easyocr': 'EasyOCR',
    'ocr_paddle': 'PaddleOCR',
    'donut_cord': 'Donut',
    'florence2': 'Florence-2',
    'craft_detector': 'CRAFT',
    'spatial': 'Spatial OCR'
};

// =============================================================================
// STATE MANAGEMENT
// =============================================================================

const DashboardState = {
    currentPage: 1,
    perPage: 20,
    totalReceipts: 0,
    receipts: [],
    stats: {
        totalExtractions: 0,
        monthlyExtractions: 0,
        storageUsed: 0,
        currentPlan: 'free'
    },
    loading: false,
    error: null
};

// =============================================================================
// API UTILITIES
// =============================================================================

class APIClient {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
    }

    getAuthToken() {
        return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const token = this.getAuthToken();
        
        const defaultHeaders = {
            'Content-Type': 'application/json'
        };
        
        if (token) {
            defaultHeaders['Authorization'] = `Bearer ${token}`;
        }
        
        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers
            }
        };
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
        config.signal = controller.signal;
        
        try {
            const response = await fetch(url, config);
            clearTimeout(timeoutId);
            
            if (response.status === 401) {
                this.handleUnauthorized();
                throw new Error('Unauthorized - please sign in again');
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || data.message || `Request failed: ${response.status}`);
                }
                
                return data;
            }
            
            if (!response.ok) {
                throw new Error(`Request failed: ${response.status}`);
            }
            
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('Request timeout - please try again');
            }
            
            throw error;
        }
    }

    handleUnauthorized() {
        localStorage.removeItem('auth_token');
        sessionStorage.removeItem('auth_token');
        sessionStorage.removeItem('user_data');
        
        setTimeout(() => {
            window.location.href = '/enhanced-login.html';
        }, 2000);
    }

    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async patch(endpoint, data) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

const apiClient = new APIClient();

// =============================================================================
// DATA FETCHING
// =============================================================================

async function fetchUserStats() {
    try {
        const response = await apiClient.get('/api/receipts?page=1&per_page=1');
        
        const now = new Date();
        const currentMonth = now.getMonth();
        const currentYear = now.getFullYear();
        
        let monthlyCount = 0;
        let totalCount = 0;
        let storageUsed = 0;
        
        if (response.receipts && Array.isArray(response.receipts)) {
            response.receipts.forEach(receipt => {
                const receiptDate = new Date(receipt.created_at || receipt.upload_date);
                if (receiptDate.getMonth() === currentMonth && receiptDate.getFullYear() === currentYear) {
                    monthlyCount++;
                }
                totalCount++;
                storageUsed += receipt.file_size || 0;
            });
        }
        
        if (response.pagination && response.pagination.total) {
            totalCount = response.pagination.total;
        }
        
        return {
            totalExtractions: totalCount,
            monthlyExtractions: monthlyCount,
            storageUsed: storageUsed,
            currentPlan: 'free'
        };
    } catch (error) {
        console.error('Error fetching user stats:', error);
        return {
            totalExtractions: 0,
            monthlyExtractions: 0,
            storageUsed: 0,
            currentPlan: 'free'
        };
    }
}

async function fetchReceipts(page = 1, perPage = 20) {
    try {
        const response = await apiClient.get(`/api/receipts?page=${page}&per_page=${perPage}`);
        
        return {
            receipts: response.receipts || [],
            pagination: response.pagination || {
                page: page,
                per_page: perPage,
                total: 0,
                pages: 0
            }
        };
    } catch (error) {
        console.error('Error fetching receipts:', error);
        throw error;
    }
}

async function fetchReceiptDetails(receiptId) {
    try {
        const response = await apiClient.get(`/api/receipts/${receiptId}`);
        return response.receipt || response;
    } catch (error) {
        console.error('Error fetching receipt details:', error);
        throw error;
    }
}

async function deleteReceipt(receiptId) {
    try {
        await apiClient.delete(`/api/receipts/${receiptId}`);
        return true;
    } catch (error) {
        console.error('Error deleting receipt:', error);
        throw error;
    }
}

async function exportReceiptsData() {
    try {
        let allReceipts = [];
        let page = 1;
        let hasMore = true;
        
        while (hasMore) {
            const response = await fetchReceipts(page, 100);
            allReceipts = allReceipts.concat(response.receipts);
            
            if (response.pagination.page >= response.pagination.pages) {
                hasMore = false;
            } else {
                page++;
            }
        }
        
        const dataStr = JSON.stringify(allReceipts, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `receipts_export_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        return true;
    } catch (error) {
        console.error('Error exporting data:', error);
        throw error;
    }
}

// =============================================================================
// UI UPDATES
// =============================================================================

function updateStatsDisplay(stats) {
    document.getElementById('totalExtractions').textContent = stats.totalExtractions.toLocaleString();
    document.getElementById('monthlyExtractions').textContent = stats.monthlyExtractions.toLocaleString();
    
    const storageGB = (stats.storageUsed / (1024 * 1024 * 1024)).toFixed(2);
    const storageMB = (stats.storageUsed / (1024 * 1024)).toFixed(1);
    document.getElementById('storageUsed').textContent = storageGB >= 1 ? `${storageGB} GB` : `${storageMB} MB`;
    
    const planName = stats.currentPlan.charAt(0).toUpperCase() + stats.currentPlan.slice(1);
    document.getElementById('currentPlan').textContent = planName;
    
    DashboardState.stats = stats;
    updateUsageDisplay(stats);
}

function updateUsageDisplay(stats) {
    const plan = stats.currentPlan.toLowerCase();
    const limits = PLAN_LIMITS[plan];
    
    if (!limits) return;
    
    const receiptsUsed = stats.monthlyExtractions;
    const receiptsLimit = limits.receipts;
    const storageUsed = stats.storageUsed;
    const storageLimit = limits.storage;
    
    if (receiptsLimit > 0) {
        const receiptsPercent = Math.min((receiptsUsed / receiptsLimit) * 100, 100);
        document.getElementById('usageReceiptsText').textContent = `${receiptsUsed} / ${receiptsLimit}`;
        document.getElementById('usageReceiptsBar').style.width = `${receiptsPercent}%`;
    } else {
        document.getElementById('usageReceiptsText').textContent = `${receiptsUsed} / Unlimited`;
        document.getElementById('usageReceiptsBar').style.width = '0%';
    }
    
    if (storageLimit > 0) {
        const storagePercent = Math.min((storageUsed / storageLimit) * 100, 100);
        const usedMB = (storageUsed / (1024 * 1024)).toFixed(1);
        const limitMB = (storageLimit / (1024 * 1024)).toFixed(0);
        document.getElementById('usageStorageText').textContent = `${usedMB} MB / ${limitMB} MB`;
        document.getElementById('usageStorageBar').style.width = `${storagePercent}%`;
    } else {
        const usedGB = (storageUsed / (1024 * 1024 * 1024)).toFixed(2);
        document.getElementById('usageStorageText').textContent = `${usedGB} GB / Unlimited`;
        document.getElementById('usageStorageBar').style.width = '0%';
    }
}

function updateReceiptsTable(receipts) {
    const tableBody = document.getElementById('receiptsTableBody');
    const table = document.getElementById('receiptsTable');
    const emptyState = document.getElementById('receiptsEmpty');
    const loading = document.getElementById('receiptsLoading');
    
    loading.style.display = 'none';
    
    if (!receipts || receipts.length === 0) {
        table.style.display = 'none';
        emptyState.style.display = 'block';
        document.getElementById('paginationContainer').style.display = 'none';
        return;
    }
    
    table.style.display = 'table';
    emptyState.style.display = 'none';
    
    tableBody.innerHTML = receipts.map(receipt => {
        const date = new Date(receipt.created_at || receipt.upload_date);
        const formattedDate = date.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const modelName = MODEL_NAMES[receipt.model_id] || receipt.model_id || 'Unknown';
        const status = receipt.status || 'completed';
        const fileName = receipt.filename || receipt.file_name || 'Unknown';
        const storeName = receipt.store_name || receipt.merchant_name || 'N/A';
        
        let badgeClass = 'badge-success';
        let statusText = 'Completed';
        
        if (status === 'processing') {
            badgeClass = 'badge-processing';
            statusText = 'Processing';
        } else if (status === 'failed') {
            badgeClass = 'badge-error';
            statusText = 'Failed';
        } else if (status === 'pending') {
            badgeClass = 'badge-warning';
            statusText = 'Pending';
        }
        
        return `
            <tr class="receipt-row" data-receipt-id="${receipt.id}">
                <td>${formattedDate}</td>
                <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${fileName}">${fileName}</td>
                <td>${storeName}</td>
                <td>${modelName}</td>
                <td><span class="badge ${badgeClass}">${statusText}</span></td>
                <td>
                    <button class="btn btn-secondary btn-sm view-receipt-btn" data-receipt-id="${receipt.id}">View</button>
                    <button class="btn btn-secondary btn-sm delete-receipt-btn" data-receipt-id="${receipt.id}">Delete</button>
                </td>
            </tr>
        `;
    }).join('');
    
    document.querySelectorAll('.view-receipt-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const receiptId = btn.getAttribute('data-receipt-id');
            showReceiptDetails(receiptId);
        });
    });
    
    document.querySelectorAll('.delete-receipt-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const receiptId = btn.getAttribute('data-receipt-id');
            handleDeleteReceipt(receiptId);
        });
    });
}

function updatePagination(pagination) {
    const container = document.getElementById('paginationContainer');
    
    if (!pagination || pagination.total === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'flex';
    
    const currentPage = pagination.page;
    const totalPages = pagination.pages;
    
    let html = '<button class="pagination-btn" id="prevPageBtn">Previous</button>';
    
    const maxButtons = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);
    
    if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === currentPage ? 'active' : '';
        html += `<button class="pagination-btn ${activeClass}" data-page="${i}">${i}</button>`;
    }
    
    html += '<button class="pagination-btn" id="nextPageBtn">Next</button>';
    
    container.innerHTML = html;
    
    document.getElementById('prevPageBtn').addEventListener('click', () => {
        if (currentPage > 1) loadReceipts(currentPage - 1);
    });
    
    document.getElementById('nextPageBtn').addEventListener('click', () => {
        if (currentPage < totalPages) loadReceipts(currentPage + 1);
    });
    
    document.querySelectorAll('.pagination-btn[data-page]').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = parseInt(btn.getAttribute('data-page'));
            loadReceipts(page);
        });
    });
    
    document.getElementById('prevPageBtn').disabled = currentPage === 1;
    document.getElementById('nextPageBtn').disabled = currentPage === totalPages;
}

function showError(message) {
    const container = document.getElementById('errorContainer');
    container.innerHTML = `<div class="error-message">${message}</div>`;
    
    setTimeout(() => {
        container.innerHTML = '';
    }, 5000);
}

function showSuccess(message) {
    const container = document.getElementById('successContainer');
    container.innerHTML = `<div class="success-message">${message}</div>`;
    
    setTimeout(() => {
        container.innerHTML = '';
    }, 3000);
}

function setLoading(isLoading) {
    DashboardState.loading = isLoading;
    
    const refreshBtn = document.getElementById('refreshBtn');
    const refreshText = document.getElementById('refreshBtnText');
    const refreshSpinner = document.getElementById('refreshSpinner');
    
    if (isLoading) {
        refreshBtn.disabled = true;
        refreshText.style.display = 'none';
        refreshSpinner.style.display = 'inline-block';
    } else {
        refreshBtn.disabled = false;
        refreshText.style.display = 'inline';
        refreshSpinner.style.display = 'none';
    }
}

// =============================================================================
// MAIN OPERATIONS
// =============================================================================

async function loadDashboardData() {
    if (DashboardState.loading) return;
    
    setLoading(true);
    
    try {
        const stats = await fetchUserStats();
        updateStatsDisplay(stats);
        
        await loadReceipts(DashboardState.currentPage);
        
        showSuccess('Dashboard data loaded successfully');
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError(`Failed to load dashboard data: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

async function loadReceipts(page = 1) {
    const loading = document.getElementById('receiptsLoading');
    loading.style.display = 'block';
    document.getElementById('receiptsTable').style.display = 'none';
    document.getElementById('receiptsEmpty').style.display = 'none';
    
    try {
        const data = await fetchReceipts(page, DashboardState.perPage);
        
        DashboardState.receipts = data.receipts;
        DashboardState.currentPage = data.pagination.page;
        DashboardState.totalReceipts = data.pagination.total;
        
        updateReceiptsTable(data.receipts);
        updatePagination(data.pagination);
    } catch (error) {
        console.error('Error loading receipts:', error);
        showError(`Failed to load receipts: ${error.message}`);
        
        loading.style.display = 'none';
        document.getElementById('receiptsEmpty').style.display = 'block';
    }
}

async function showReceiptDetails(receiptId) {
    const modal = document.getElementById('receiptModal');
    const modalBody = document.getElementById('modalBody');
    
    modal.classList.add('active');
    modalBody.innerHTML = '<div style="text-align: center; padding: 24px;"><div class="loading-spinner" style="width: 32px; height: 32px; border-width: 3px;"></div><p style="margin-top: 16px;">Loading receipt details...</p></div>';
    
    try {
        const receipt = await fetchReceiptDetails(receiptId);
        
        const date = new Date(receipt.created_at || receipt.upload_date);
        const formattedDate = date.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        const modelName = MODEL_NAMES[receipt.model_id] || receipt.model_id || 'Unknown';
        const extractedText = receipt.extracted_text || receipt.text || 'No text extracted';
        
        modalBody.innerHTML = `
            <dl class="receipt-details">
                <dt>Receipt ID</dt>
                <dd>${receipt.id}</dd>
                
                <dt>File Name</dt>
                <dd>${receipt.filename || receipt.file_name || 'Unknown'}</dd>
                
                <dt>Upload Date</dt>
                <dd>${formattedDate}</dd>
                
                <dt>Store Name</dt>
                <dd>${receipt.store_name || receipt.merchant_name || 'N/A'}</dd>
                
                <dt>Model Used</dt>
                <dd>${modelName}</dd>
                
                <dt>Status</dt>
                <dd>${receipt.status || 'completed'}</dd>
                
                <dt>File Size</dt>
                <dd>${receipt.file_size ? (receipt.file_size / 1024).toFixed(2) + ' KB' : 'N/A'}</dd>
                
                <dt>Extracted Text</dt>
                <dd>
                    <div class="text-content">${extractedText}</div>
                </dd>
            </dl>
            
            <div style="margin-top: 24px; display: flex; gap: 8px; justify-content: flex-end;">
                <button class="btn btn-secondary" id="closeDetailsBtn">Close</button>
                <button class="btn btn-primary" id="downloadReceiptBtn">Download JSON</button>
            </div>
        `;
        
        document.getElementById('closeDetailsBtn').addEventListener('click', () => {
            modal.classList.remove('active');
        });
        
        document.getElementById('downloadReceiptBtn').addEventListener('click', () => {
            const dataStr = JSON.stringify(receipt, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `receipt_${receipt.id}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            showSuccess('Receipt downloaded successfully');
        });
        
    } catch (error) {
        console.error('Error loading receipt details:', error);
        modalBody.innerHTML = `<div class="error-message">Failed to load receipt details: ${error.message}</div>`;
    }
}

async function handleDeleteReceipt(receiptId) {
    if (!confirm('Are you sure you want to delete this receipt? This action cannot be undone.')) {
        return;
    }
    
    try {
        await deleteReceipt(receiptId);
        showSuccess('Receipt deleted successfully');
        await loadDashboardData();
    } catch (error) {
        console.error('Error deleting receipt:', error);
        showError(`Failed to delete receipt: ${error.message}`);
    }
}

async function handleExportData() {
    if (!confirm('Export all receipt data as JSON?')) {
        return;
    }
    
    setLoading(true);
    
    try {
        await exportReceiptsData();
        showSuccess('Data exported successfully');
    } catch (error) {
        console.error('Error exporting data:', error);
        showError(`Failed to export data: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

async function handleDeleteAll() {
    if (!confirm('Are you sure you want to delete ALL your receipts? This action cannot be undone.')) {
        return;
    }
    
    if (!confirm('Final confirmation: Delete all receipts permanently?')) {
        return;
    }
    
    setLoading(true);
    
    try {
        const data = await fetchReceipts(1, 100);
        const receipts = data.receipts;
        
        if (receipts.length === 0) {
            showSuccess('No receipts to delete');
            return;
        }
        
        let deleted = 0;
        for (const receipt of receipts) {
            try {
                await deleteReceipt(receipt.id);
                deleted++;
            } catch (error) {
                console.error(`Failed to delete receipt ${receipt.id}:`, error);
            }
        }
        
        showSuccess(`Deleted ${deleted} receipts successfully`);
        await loadDashboardData();
    } catch (error) {
        console.error('Error deleting all receipts:', error);
        showError(`Failed to delete receipts: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

function handleLogout() {
    localStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('user_data');
    window.location.href = '/enhanced-login.html';
}

// =============================================================================
// INITIALIZATION
// =============================================================================

function checkAuthentication() {
    const token = apiClient.getAuthToken();
    
    if (!token) {
        window.location.href = '/enhanced-login.html';
        return false;
    }
    
    return true;
}

function setupEventListeners() {
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadDashboardData();
    });
    
    document.getElementById('closeModalBtn').addEventListener('click', () => {
        document.getElementById('receiptModal').classList.remove('active');
    });
    
    document.getElementById('exportDataBtn').addEventListener('click', handleExportData);
    
    document.getElementById('deleteAllBtn').addEventListener('click', handleDeleteAll);
    
    document.getElementById('receiptModal').addEventListener('click', (e) => {
        if (e.target.id === 'receiptModal') {
            document.getElementById('receiptModal').classList.remove('active');
        }
    });
}

function initializeDashboard() {
    console.log('Initializing dashboard...');
    
    if (!checkAuthentication()) {
        return;
    }
    
    setupEventListeners();
    
    loadDashboardData();
    
    console.log('Dashboard initialized successfully');
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboard);
} else {
    initializeDashboard();
}

window.DashboardState = DashboardState;

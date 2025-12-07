/**
 * Advanced Data Table Component
 * Feature-rich table with sorting, filtering, pagination, and selection
 */

import eventBus from '../core/event-bus.js';

class DataTable {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            data: [],
            columns: [],
            pageSize: 10,
            sortable: true,
            filterable: true,
            searchable: true,
            selectable: false,
            multiSelect: false,
            pagination: true,
            responsive: true,
            emptyMessage: 'No data available',
            loadingMessage: 'Loading...',
            ...options
        };

        this.state = {
            data: [],
            filteredData: [],
            displayData: [],
            currentPage: 1,
            totalPages: 1,
            sortColumn: null,
            sortDirection: 'asc',
            searchQuery: '',
            filters: {},
            selected: new Set(),
            loading: false
        };

        this.init();
    }

    init() {
        if (!this.container) {
            console.error('DataTable: Container not found');
            return;
        }

        this.setData(this.options.data);
        this.render();
        this.setupEventListeners();
    }

    setData(data) {
        this.state.data = data;
        this.applyFiltersAndSearch();
        this.updatePagination();
    }

    applyFiltersAndSearch() {
        let data = [...this.state.data];

        // Apply search
        if (this.state.searchQuery) {
            const query = this.state.searchQuery.toLowerCase();
            data = data.filter(row => {
                return this.options.columns.some(col => {
                    const value = this.getCellValue(row, col.field);
                    return String(value).toLowerCase().includes(query);
                });
            });
        }

        // Apply filters
        Object.entries(this.state.filters).forEach(([field, value]) => {
            if (value !== null && value !== '') {
                data = data.filter(row => {
                    const cellValue = this.getCellValue(row, field);
                    return String(cellValue) === String(value);
                });
            }
        });

        this.state.filteredData = data;
        
        // Apply sorting
        if (this.state.sortColumn) {
            this.sortData();
        } else {
            this.updateDisplayData();
        }
    }

    sortData() {
        const column = this.options.columns.find(col => col.field === this.state.sortColumn);
        if (!column) return;

        this.state.filteredData.sort((a, b) => {
            const aVal = this.getCellValue(a, this.state.sortColumn);
            const bVal = this.getCellValue(b, this.state.sortColumn);

            let comparison = 0;
            if (column.sortType === 'number') {
                comparison = parseFloat(aVal) - parseFloat(bVal);
            } else if (column.sortType === 'date') {
                comparison = new Date(aVal) - new Date(bVal);
            } else {
                comparison = String(aVal).localeCompare(String(bVal));
            }

            return this.state.sortDirection === 'asc' ? comparison : -comparison;
        });

        this.updateDisplayData();
    }

    updateDisplayData() {
        const start = (this.state.currentPage - 1) * this.options.pageSize;
        const end = start + this.options.pageSize;
        this.state.displayData = this.state.filteredData.slice(start, end);
    }

    updatePagination() {
        this.state.totalPages = Math.ceil(this.state.filteredData.length / this.options.pageSize);
        if (this.state.currentPage > this.state.totalPages) {
            this.state.currentPage = Math.max(1, this.state.totalPages);
        }
        this.updateDisplayData();
    }

    render() {
        this.container.innerHTML = '';
        this.container.className = 'data-table-container';

        // Search bar
        if (this.options.searchable) {
            this.container.appendChild(this.renderSearchBar());
        }

        // Table wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'data-table-wrapper';
        
        if (this.state.loading) {
            wrapper.innerHTML = `<div class="data-table-loading">${this.options.loadingMessage}</div>`;
        } else if (this.state.displayData.length === 0) {
            wrapper.innerHTML = `<div class="data-table-empty">${this.options.emptyMessage}</div>`;
        } else {
            wrapper.appendChild(this.renderTable());
        }

        this.container.appendChild(wrapper);

        // Pagination
        if (this.options.pagination && this.state.totalPages > 1) {
            this.container.appendChild(this.renderPagination());
        }

        // Info bar
        this.container.appendChild(this.renderInfo());
    }

    renderSearchBar() {
        const searchBar = document.createElement('div');
        searchBar.className = 'data-table-search';
        searchBar.innerHTML = `
            <input type="search" 
                   class="data-table-search-input" 
                   placeholder="Search..." 
                   value="${this.state.searchQuery}">
            ${this.options.selectable && this.state.selected.size > 0 ? `
                <div class="data-table-actions">
                    <span class="selection-count">${this.state.selected.size} selected</span>
                    <button class="btn btn-sm btn-outline" data-action="clear-selection">Clear</button>
                </div>
            ` : ''}
        `;
        return searchBar;
    }

    renderTable() {
        const table = document.createElement('table');
        table.className = 'data-table';
        table.setAttribute('role', 'table');

        // Header
        const thead = document.createElement('thead');
        thead.innerHTML = this.renderTableHeader();
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');
        tbody.innerHTML = this.renderTableBody();
        table.appendChild(tbody);

        return table;
    }

    renderTableHeader() {
        const selectAllCell = this.options.selectable && this.options.multiSelect ? `
            <th class="select-cell">
                <input type="checkbox" 
                       class="select-all" 
                       ${this.isAllSelected() ? 'checked' : ''}>
            </th>
        ` : this.options.selectable ? '<th class="select-cell"></th>' : '';

        const headerCells = this.options.columns.map(col => {
            const sortable = this.options.sortable && col.sortable !== false;
            const sorted = this.state.sortColumn === col.field;
            const sortClass = sorted ? `sorted-${this.state.sortDirection}` : '';

            return `
                <th class="${sortable ? 'sortable' : ''} ${sortClass}" 
                    data-field="${col.field}"
                    ${sortable ? 'role="button" tabindex="0"' : ''}>
                    <div class="th-content">
                        <span>${col.title}</span>
                        ${sortable ? this.renderSortIcon(sorted, this.state.sortDirection) : ''}
                    </div>
                </th>
            `;
        }).join('');

        return `<tr>${selectAllCell}${headerCells}</tr>`;
    }

    renderSortIcon(sorted, direction) {
        if (!sorted) {
            return `<span class="sort-icon sort-none">⇅</span>`;
        }
        return direction === 'asc' 
            ? `<span class="sort-icon sort-asc">↑</span>`
            : `<span class="sort-icon sort-desc">↓</span>`;
    }

    renderTableBody() {
        return this.state.displayData.map((row, index) => {
            const rowId = this.getRowId(row, index);
            const isSelected = this.state.selected.has(rowId);

            const selectCell = this.options.selectable ? `
                <td class="select-cell">
                    <input type="checkbox" 
                           class="select-row" 
                           data-row-id="${rowId}"
                           ${isSelected ? 'checked' : ''}>
                </td>
            ` : '';

            const dataCells = this.options.columns.map(col => {
                const value = this.getCellValue(row, col.field);
                const formatted = col.formatter ? col.formatter(value, row) : value;
                return `<td data-field="${col.field}">${formatted}</td>`;
            }).join('');

            return `
                <tr data-row-id="${rowId}" class="${isSelected ? 'selected' : ''}">
                    ${selectCell}${dataCells}
                </tr>
            `;
        }).join('');
    }

    renderPagination() {
        const pagination = document.createElement('div');
        pagination.className = 'data-table-pagination';

        const pages = this.getPaginationPages();
        const buttons = pages.map(page => {
            if (page === '...') {
                return '<span class="pagination-ellipsis">...</span>';
            }
            const active = page === this.state.currentPage ? 'active' : '';
            return `<button class="pagination-btn ${active}" data-page="${page}">${page}</button>`;
        }).join('');

        pagination.innerHTML = `
            <button class="pagination-btn" data-page="prev" ${this.state.currentPage === 1 ? 'disabled' : ''}>
                Previous
            </button>
            ${buttons}
            <button class="pagination-btn" data-page="next" ${this.state.currentPage === this.state.totalPages ? 'disabled' : ''}>
                Next
            </button>
        `;

        return pagination;
    }

    getPaginationPages() {
        const current = this.state.currentPage;
        const total = this.state.totalPages;
        const pages = [];

        if (total <= 7) {
            for (let i = 1; i <= total; i++) {
                pages.push(i);
            }
        } else {
            pages.push(1);
            
            if (current > 3) {
                pages.push('...');
            }

            const start = Math.max(2, current - 1);
            const end = Math.min(total - 1, current + 1);

            for (let i = start; i <= end; i++) {
                pages.push(i);
            }

            if (current < total - 2) {
                pages.push('...');
            }

            pages.push(total);
        }

        return pages;
    }

    renderInfo() {
        const info = document.createElement('div');
        info.className = 'data-table-info';
        
        const start = (this.state.currentPage - 1) * this.options.pageSize + 1;
        const end = Math.min(start + this.options.pageSize - 1, this.state.filteredData.length);
        const total = this.state.filteredData.length;

        info.textContent = `Showing ${start}-${end} of ${total} entries`;
        
        return info;
    }

    setupEventListeners() {
        // Search
        this.container.addEventListener('input', (e) => {
            if (e.target.classList.contains('data-table-search-input')) {
                this.handleSearch(e.target.value);
            }
        });

        // Sort
        this.container.addEventListener('click', (e) => {
            const th = e.target.closest('th.sortable');
            if (th) {
                this.handleSort(th.dataset.field);
            }
        });

        // Pagination
        this.container.addEventListener('click', (e) => {
            if (e.target.classList.contains('pagination-btn')) {
                const page = e.target.dataset.page;
                this.handlePageChange(page);
            }
        });

        // Selection
        this.container.addEventListener('change', (e) => {
            if (e.target.classList.contains('select-all')) {
                this.handleSelectAll(e.target.checked);
            } else if (e.target.classList.contains('select-row')) {
                this.handleSelectRow(e.target.dataset.rowId, e.target.checked);
            }
        });

        // Clear selection
        this.container.addEventListener('click', (e) => {
            if (e.target.closest('[data-action="clear-selection"]')) {
                this.clearSelection();
            }
        });
    }

    handleSearch(query) {
        this.state.searchQuery = query;
        this.state.currentPage = 1;
        this.applyFiltersAndSearch();
        this.updatePagination();
        this.render();
    }

    handleSort(field) {
        if (this.state.sortColumn === field) {
            this.state.sortDirection = this.state.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.state.sortColumn = field;
            this.state.sortDirection = 'asc';
        }

        this.sortData();
        this.render();
    }

    handlePageChange(page) {
        if (page === 'prev') {
            this.state.currentPage = Math.max(1, this.state.currentPage - 1);
        } else if (page === 'next') {
            this.state.currentPage = Math.min(this.state.totalPages, this.state.currentPage + 1);
        } else {
            this.state.currentPage = parseInt(page);
        }

        this.updateDisplayData();
        this.render();
    }

    handleSelectAll(checked) {
        if (checked) {
            this.state.displayData.forEach((row, index) => {
                this.state.selected.add(this.getRowId(row, index));
            });
        } else {
            this.state.displayData.forEach((row, index) => {
                this.state.selected.delete(this.getRowId(row, index));
            });
        }

        this.render();
        this.emitSelectionChange();
    }

    handleSelectRow(rowId, checked) {
        if (checked) {
            if (!this.options.multiSelect) {
                this.state.selected.clear();
            }
            this.state.selected.add(rowId);
        } else {
            this.state.selected.delete(rowId);
        }

        this.render();
        this.emitSelectionChange();
    }

    clearSelection() {
        this.state.selected.clear();
        this.render();
        this.emitSelectionChange();
    }

    isAllSelected() {
        if (this.state.displayData.length === 0) return false;
        return this.state.displayData.every((row, index) => 
            this.state.selected.has(this.getRowId(row, index))
        );
    }

    getRowId(row, index) {
        return row.id || row._id || index;
    }

    getCellValue(row, field) {
        return field.split('.').reduce((obj, key) => obj?.[key], row) ?? '';
    }

    emitSelectionChange() {
        const selectedRows = this.state.data.filter((row, index) => 
            this.state.selected.has(this.getRowId(row, index))
        );

        eventBus.emit('datatable:selection-changed', {
            selected: Array.from(this.state.selected),
            selectedRows
        });

        if (this.options.onSelectionChange) {
            this.options.onSelectionChange(Array.from(this.state.selected), selectedRows);
        }
    }

    // Public API
    refresh() {
        this.render();
    }

    reload() {
        this.state.loading = true;
        this.render();

        if (this.options.onReload) {
            this.options.onReload().then(data => {
                this.setData(data);
                this.state.loading = false;
                this.render();
            });
        }
    }

    getSelectedRows() {
        return this.state.data.filter((row, index) => 
            this.state.selected.has(this.getRowId(row, index))
        );
    }

    getSelected() {
        return Array.from(this.state.selected);
    }

    setFilter(field, value) {
        this.state.filters[field] = value;
        this.state.currentPage = 1;
        this.applyFiltersAndSearch();
        this.updatePagination();
        this.render();
    }

    clearFilters() {
        this.state.filters = {};
        this.state.searchQuery = '';
        this.state.currentPage = 1;
        this.applyFiltersAndSearch();
        this.updatePagination();
        this.render();
    }

    destroy() {
        this.container.innerHTML = '';
    }
}

// Expose globally
if (typeof window !== 'undefined') {
    window.DataTable = DataTable;
}

export default DataTable;

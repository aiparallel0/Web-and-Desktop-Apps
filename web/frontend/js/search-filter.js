/**
 * Advanced Search and Filter System
 * Provides comprehensive search, filter, and sort capabilities
 * @version 2.0.0
 */

(function(window) {
    'use strict';

    class SearchFilter {
        constructor(options = {}) {
            this.data = options.data || [];
            this.searchableFields = options.searchableFields || [];
            this.filters = {};
            this.sortConfig = {
                field: null,
                direction: 'asc'
            };
            this.listeners = new Map();
            this.searchIndex = null;
            this.buildSearchIndex();
        }

        /**
         * Build search index for faster searching
         */
        buildSearchIndex() {
            this.searchIndex = new Map();
            
            this.data.forEach((item, index) => {
                const searchText = this.searchableFields
                    .map(field => {
                        const value = this.getNestedValue(item, field);
                        return value ? String(value).toLowerCase() : '';
                    })
                    .join(' ');
                
                this.searchIndex.set(index, searchText);
            });
        }

        /**
         * Get nested value from object
         */
        getNestedValue(obj, path) {
            return path.split('.').reduce((current, key) => current?.[key], obj);
        }

        /**
         * Set data
         */
        setData(data) {
            this.data = data;
            this.buildSearchIndex();
            this.emit('dataChanged', data);
        }

        /**
         * Search data
         */
        search(query) {
            if (!query || query.trim() === '') {
                return this.data;
            }

            const lowerQuery = query.toLowerCase();
            const terms = lowerQuery.split(/\s+/).filter(t => t.length > 0);

            const results = this.data.filter((item, index) => {
                const searchText = this.searchIndex.get(index);
                return terms.every(term => searchText.includes(term));
            });

            this.emit('searchComplete', { query, results, count: results.length });
            return results;
        }

        /**
         * Advanced search with operators
         */
        advancedSearch(queryString) {
            // Parse query string
            const tokens = this.parseQuery(queryString);
            
            // Apply filters
            const results = this.data.filter(item => {
                return tokens.every(token => this.matchToken(item, token));
            });

            return results;
        }

        /**
         * Parse query string into tokens
         */
        parseQuery(queryString) {
            const tokens = [];
            const regex = /(\w+):([\w\s"]+)|\b(\w+)\b/g;
            let match;

            while ((match = regex.exec(queryString)) !== null) {
                if (match[1] && match[2]) {
                    // Field-specific search
                    tokens.push({
                        type: 'field',
                        field: match[1],
                        value: match[2].replace(/"/g, '')
                    });
                } else if (match[3]) {
                    // General search term
                    tokens.push({
                        type: 'term',
                        value: match[3]
                    });
                }
            }

            return tokens;
        }

        /**
         * Match token against item
         */
        matchToken(item, token) {
            if (token.type === 'field') {
                const value = this.getNestedValue(item, token.field);
                if (!value) return false;
                return String(value).toLowerCase().includes(token.value.toLowerCase());
            } else if (token.type === 'term') {
                return this.searchableFields.some(field => {
                    const value = this.getNestedValue(item, field);
                    return value && String(value).toLowerCase().includes(token.value.toLowerCase());
                });
            }
            return false;
        }

        /**
         * Add filter
         */
        addFilter(name, predicate) {
            this.filters[name] = predicate;
            this.emit('filterAdded', { name, predicate });
        }

        /**
         * Remove filter
         */
        removeFilter(name) {
            delete this.filters[name];
            this.emit('filterRemoved', { name });
        }

        /**
         * Clear all filters
         */
        clearFilters() {
            this.filters = {};
            this.emit('filtersCleared');
        }

        /**
         * Apply all filters
         */
        applyFilters(data = null) {
            const dataset = data || this.data;
            
            let filtered = [...dataset];
            
            Object.values(this.filters).forEach(predicate => {
                filtered = filtered.filter(predicate);
            });

            this.emit('filtersApplied', { count: filtered.length });
            return filtered;
        }

        /**
         * Sort data
         */
        sort(field, direction = 'asc') {
            this.sortConfig = { field, direction };
            
            const sorted = [...this.data].sort((a, b) => {
                const aVal = this.getNestedValue(a, field);
                const bVal = this.getNestedValue(b, field);
                
                // Handle null/undefined
                if (aVal == null) return 1;
                if (bVal == null) return -1;
                
                // Determine data type
                const isNumber = typeof aVal === 'number' && typeof bVal === 'number';
                const isDate = aVal instanceof Date && bVal instanceof Date;
                
                let comparison = 0;
                
                if (isNumber || isDate) {
                    comparison = aVal - bVal;
                } else {
                    comparison = String(aVal).localeCompare(String(bVal));
                }
                
                return direction === 'asc' ? comparison : -comparison;
            });

            this.emit('sorted', { field, direction });
            return sorted;
        }

        /**
         * Get filter stats
         */
        getFilterStats(field) {
            const stats = {
                unique: new Set(),
                counts: {},
                min: null,
                max: null,
                total: 0
            };

            this.data.forEach(item => {
                const value = this.getNestedValue(item, field);
                if (value != null) {
                    stats.unique.add(value);
                    stats.counts[value] = (stats.counts[value] || 0) + 1;
                    stats.total++;
                    
                    if (typeof value === 'number') {
                        if (stats.min === null || value < stats.min) stats.min = value;
                        if (stats.max === null || value > stats.max) stats.max = value;
                    }
                }
            });

            stats.unique = Array.from(stats.unique);
            return stats;
        }

        /**
         * Filter by date range
         */
        filterDateRange(field, startDate, endDate) {
            const start = new Date(startDate);
            const end = new Date(endDate);
            
            return this.data.filter(item => {
                const value = this.getNestedValue(item, field);
                if (!value) return false;
                
                const date = new Date(value);
                return date >= start && date <= end;
            });
        }

        /**
         * Filter by numeric range
         */
        filterNumericRange(field, min, max) {
            return this.data.filter(item => {
                const value = this.getNestedValue(item, field);
                if (typeof value !== 'number') return false;
                
                return value >= min && value <= max;
            });
        }

        /**
         * Filter by values
         */
        filterByValues(field, values) {
            const valueSet = new Set(values);
            
            return this.data.filter(item => {
                const value = this.getNestedValue(item, field);
                return valueSet.has(value);
            });
        }

        /**
         * Group data by field
         */
        groupBy(field) {
            const groups = {};
            
            this.data.forEach(item => {
                const value = this.getNestedValue(item, field);
                const key = value != null ? String(value) : 'null';
                
                if (!groups[key]) {
                    groups[key] = [];
                }
                groups[key].push(item);
            });

            return groups;
        }

        /**
         * Get facets for field
         */
        getFacets(field) {
            const facets = {};
            
            this.data.forEach(item => {
                const value = this.getNestedValue(item, field);
                const key = value != null ? String(value) : 'null';
                
                facets[key] = (facets[key] || 0) + 1;
            });

            // Convert to array and sort by count
            return Object.entries(facets)
                .map(([value, count]) => ({ value, count }))
                .sort((a, b) => b.count - a.count);
        }

        /**
         * Fuzzy search
         */
        fuzzySearch(query, threshold = 0.6) {
            const results = this.data.filter((item, index) => {
                const searchText = this.searchIndex.get(index);
                const score = this.fuzzyScore(query.toLowerCase(), searchText);
                return score >= threshold;
            });

            return results.sort((a, b) => {
                const scoreA = this.fuzzyScore(query.toLowerCase(), this.searchIndex.get(this.data.indexOf(a)));
                const scoreB = this.fuzzyScore(query.toLowerCase(), this.searchIndex.get(this.data.indexOf(b)));
                return scoreB - scoreA;
            });
        }

        /**
         * Calculate fuzzy match score
         */
        fuzzyScore(query, text) {
            if (!query || !text) return 0;
            
            let score = 0;
            let queryIndex = 0;
            
            for (let i = 0; i < text.length && queryIndex < query.length; i++) {
                if (text[i] === query[queryIndex]) {
                    score++;
                    queryIndex++;
                }
            }
            
            return score / query.length;
        }

        /**
         * Highlight search terms in text
         */
        highlight(text, query) {
            if (!query || !text) return text;
            
            const terms = query.split(/\s+/).filter(t => t.length > 0);
            let result = text;
            
            terms.forEach(term => {
                const regex = new RegExp(`(${term})`, 'gi');
                result = result.replace(regex, '<mark>$1</mark>');
            });
            
            return result;
        }

        /**
         * Get search suggestions
         */
        getSuggestions(query, limit = 10) {
            if (!query || query.trim() === '') return [];
            
            const lowerQuery = query.toLowerCase();
            const suggestions = new Set();
            
            this.data.forEach((item, index) => {
                const searchText = this.searchIndex.get(index);
                
                // Find words that start with the query
                const words = searchText.split(/\s+/);
                words.forEach(word => {
                    if (word.startsWith(lowerQuery) && word.length > lowerQuery.length) {
                        suggestions.add(word);
                    }
                });
            });
            
            return Array.from(suggestions).slice(0, limit);
        }

        /**
         * Export filtered results
         */
        export(format = 'json', data = null) {
            const exportData = data || this.applyFilters();
            
            switch (format.toLowerCase()) {
                case 'json':
                    return JSON.stringify(exportData, null, 2);
                
                case 'csv':
                    return this.toCSV(exportData);
                
                case 'tsv':
                    return this.toCSV(exportData, '\t');
                
                default:
                    throw new Error(`Unsupported format: ${format}`);
            }
        }

        /**
         * Convert to CSV
         */
        toCSV(data, delimiter = ',') {
            if (data.length === 0) return '';
            
            const keys = Object.keys(data[0]);
            const header = keys.join(delimiter);
            
            const rows = data.map(item => {
                return keys.map(key => {
                    const value = item[key];
                    const stringValue = value != null ? String(value) : '';
                    
                    // Escape delimiter and quotes
                    if (stringValue.includes(delimiter) || stringValue.includes('"') || stringValue.includes('\n')) {
                        return `"${stringValue.replace(/"/g, '""')}"`;
                    }
                    
                    return stringValue;
                }).join(delimiter);
            });
            
            return [header, ...rows].join('\n');
        }

        /**
         * Pagination
         */
        paginate(page = 1, perPage = 10, data = null) {
            const dataset = data || this.data;
            const start = (page - 1) * perPage;
            const end = start + perPage;
            
            return {
                data: dataset.slice(start, end),
                page,
                perPage,
                total: dataset.length,
                totalPages: Math.ceil(dataset.length / perPage),
                hasNext: end < dataset.length,
                hasPrev: page > 1
            };
        }

        /**
         * Full text search with ranking
         */
        fullTextSearch(query) {
            const results = this.data.map((item, index) => {
                const score = this.calculateRelevanceScore(query, item, index);
                return { item, score };
            })
            .filter(result => result.score > 0)
            .sort((a, b) => b.score - a.score)
            .map(result => result.item);

            return results;
        }

        /**
         * Calculate relevance score
         */
        calculateRelevanceScore(query, item, index) {
            const lowerQuery = query.toLowerCase();
            const terms = lowerQuery.split(/\s+/).filter(t => t.length > 0);
            const searchText = this.searchIndex.get(index);
            
            let score = 0;
            
            terms.forEach(term => {
                // Exact match bonus
                if (searchText.includes(term)) {
                    score += 10;
                }
                
                // Partial match
                const regex = new RegExp(term, 'gi');
                const matches = searchText.match(regex);
                if (matches) {
                    score += matches.length * 5;
                }
                
                // Field-specific bonuses
                this.searchableFields.forEach(field => {
                    const value = this.getNestedValue(item, field);
                    if (value) {
                        const fieldText = String(value).toLowerCase();
                        if (fieldText.includes(term)) {
                            score += 3;
                        }
                        // Exact field match bonus
                        if (fieldText === term) {
                            score += 15;
                        }
                    }
                });
            });
            
            return score;
        }

        /**
         * Event emitter
         */
        on(event, callback) {
            if (!this.listeners.has(event)) {
                this.listeners.set(event, new Set());
            }
            this.listeners.get(event).add(callback);
        }

        off(event, callback) {
            if (this.listeners.has(event)) {
                this.listeners.get(event).delete(callback);
            }
        }

        emit(event, data) {
            if (this.listeners.has(event)) {
                this.listeners.get(event).forEach(callback => {
                    try {
                        callback(data);
                    } catch (error) {
                        console.error(`Error in event listener for ${event}:`, error);
                    }
                });
            }
        }
    }

    /**
     * Filter Builder UI Component
     */
    class FilterBuilder {
        constructor(searchFilter, container) {
            this.searchFilter = searchFilter;
            this.container = container;
            this.activeFilters = [];
            this.render();
        }

        render() {
            if (!this.container) return;

            this.container.innerHTML = '';
            this.container.className = 'filter-builder';
            this.container.style.cssText = `
                padding: 20px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            `;

            // Search box
            const searchBox = this.createSearchBox();
            this.container.appendChild(searchBox);

            // Filter controls
            const filterControls = this.createFilterControls();
            this.container.appendChild(filterControls);

            // Active filters
            const activeFiltersEl = this.createActiveFilters();
            this.container.appendChild(activeFiltersEl);
        }

        createSearchBox() {
            const wrapper = document.createElement('div');
            wrapper.style.cssText = 'margin-bottom: 20px;';

            const input = document.createElement('input');
            input.type = 'text';
            input.placeholder = 'Search...';
            input.className = 'search-input';
            input.style.cssText = `
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                font-size: 16px;
                box-sizing: border-box;
            `;

            let debounceTimer;
            input.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    const results = this.searchFilter.search(e.target.value);
                    this.emitResults(results);
                }, 300);
            });

            wrapper.appendChild(input);
            return wrapper;
        }

        createFilterControls() {
            const wrapper = document.createElement('div');
            wrapper.style.cssText = 'margin-bottom: 20px;';

            const button = document.createElement('button');
            button.textContent = '+ Add Filter';
            button.className = 'btn btn-outline';
            button.style.cssText = `
                padding: 8px 16px;
                border: 2px solid #3b82f6;
                background: transparent;
                color: #3b82f6;
                border-radius: 6px;
                font-weight: 500;
                cursor: pointer;
            `;

            button.addEventListener('click', () => {
                this.showFilterModal();
            });

            wrapper.appendChild(button);
            return wrapper;
        }

        createActiveFilters() {
            const wrapper = document.createElement('div');
            wrapper.id = 'activeFilters';
            wrapper.style.cssText = 'display: flex; flex-wrap: wrap; gap: 8px;';

            this.activeFilters.forEach(filter => {
                const tag = this.createFilterTag(filter);
                wrapper.appendChild(tag);
            });

            return wrapper;
        }

        createFilterTag(filter) {
            const tag = document.createElement('div');
            tag.style.cssText = `
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 6px 12px;
                background: #dbeafe;
                color: #1e40af;
                border-radius: 16px;
                font-size: 14px;
            `;

            const text = document.createElement('span');
            text.textContent = filter.label;
            tag.appendChild(text);

            const removeBtn = document.createElement('button');
            removeBtn.textContent = '×';
            removeBtn.style.cssText = `
                background: none;
                border: none;
                color: #1e40af;
                font-size: 18px;
                cursor: pointer;
                padding: 0;
                line-height: 1;
            `;

            removeBtn.addEventListener('click', () => {
                this.removeFilter(filter);
            });

            tag.appendChild(removeBtn);
            return tag;
        }

        showFilterModal() {
            // This would show a modal to add new filters
            console.log('Show filter modal');
        }

        removeFilter(filter) {
            this.activeFilters = this.activeFilters.filter(f => f !== filter);
            this.searchFilter.removeFilter(filter.name);
            this.render();
        }

        emitResults(results) {
            const event = new CustomEvent('filterResults', { detail: results });
            this.container.dispatchEvent(event);
        }
    }

    // Export
    window.SearchFilter = SearchFilter;
    window.FilterBuilder = FilterBuilder;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { SearchFilter, FilterBuilder };
    }

})(window);

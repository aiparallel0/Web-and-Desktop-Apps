/**
 * Search and Filter System
 * Advanced search with filters, facets, and suggestions
 */

import eventBus from '../core/event-bus.js';
import stateManager from '../core/state-manager.js';

class SearchFilterSystem {
    constructor() {
        this.searchIndex = new Map();
        this.filters = new Map();
        this.facets = new Map();
        this.searchHistory = [];
        this.maxHistorySize = 10;
        this.debounceTimer = null;
        this.debounceDelay = 300;
    }

    /**
     * Initialize search index
     */
    buildIndex(data, fields = []) {
        this.searchIndex.clear();

        data.forEach((item, index) => {
            const searchableText = fields.map(field => {
                const value = this.getNestedValue(item, field);
                return String(value).toLowerCase();
            }).join(' ');

            this.searchIndex.set(index, {
                item,
                searchableText,
                terms: this.tokenize(searchableText)
            });
        });

        this.buildFacets(data, fields);
    }

    /**
     * Build facets for filtering
     */
    buildFacets(data, fields) {
        this.facets.clear();

        fields.forEach(field => {
            const values = new Map();

            data.forEach(item => {
                const value = this.getNestedValue(item, field);
                if (value !== null && value !== undefined && value !== '') {
                    const key = String(value);
                    values.set(key, (values.get(key) || 0) + 1);
                }
            });

            this.facets.set(field, values);
        });
    }

    /**
     * Perform search
     */
    search(query, options = {}) {
        const {
            fuzzy = false,
            caseSensitive = false,
            exactMatch = false,
            minScore = 0.3,
            maxResults = 100
        } = options;

        if (!query || query.trim() === '') {
            return Array.from(this.searchIndex.values()).map(entry => entry.item);
        }

        const queryTerms = this.tokenize(query.toLowerCase());
        const results = [];

        for (const [index, entry] of this.searchIndex) {
            let score = 0;

            if (exactMatch) {
                if (entry.searchableText.includes(query.toLowerCase())) {
                    score = 1;
                }
            } else if (fuzzy) {
                score = this.fuzzyMatch(queryTerms, entry.terms);
            } else {
                score = this.termMatch(queryTerms, entry.terms);
            }

            if (score >= minScore) {
                results.push({
                    item: entry.item,
                    score,
                    matches: this.highlightMatches(entry.item, queryTerms)
                });
            }
        }

        // Sort by score descending
        results.sort((a, b) => b.score - a.score);

        // Add to search history
        this.addToHistory(query);

        return results.slice(0, maxResults);
    }

    /**
     * Apply filters
     */
    applyFilters(data, filters) {
        if (!filters || Object.keys(filters).length === 0) {
            return data;
        }

        return data.filter(item => {
            return Object.entries(filters).every(([field, value]) => {
                if (value === null || value === undefined || value === '') {
                    return true;
                }

                const itemValue = this.getNestedValue(item, field);

                if (Array.isArray(value)) {
                    return value.includes(itemValue);
                }

                if (typeof value === 'object' && value.min !== undefined && value.max !== undefined) {
                    return itemValue >= value.min && itemValue <= value.max;
                }

                return String(itemValue) === String(value);
            });
        });
    }

    /**
     * Get search suggestions
     */
    getSuggestions(query, maxSuggestions = 5) {
        if (!query || query.length < 2) {
            return this.searchHistory.slice(0, maxSuggestions);
        }

        const suggestions = new Set();
        const queryLower = query.toLowerCase();

        // Check search history
        this.searchHistory.forEach(term => {
            if (term.toLowerCase().includes(queryLower)) {
                suggestions.add(term);
            }
        });

        // Check index terms
        for (const entry of this.searchIndex.values()) {
            entry.terms.forEach(term => {
                if (term.startsWith(queryLower) && term.length > query.length) {
                    suggestions.add(term);
                }
            });

            if (suggestions.size >= maxSuggestions) break;
        }

        return Array.from(suggestions).slice(0, maxSuggestions);
    }

    /**
     * Tokenize text
     */
    tokenize(text) {
        return text
            .toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .split(/\s+/)
            .filter(term => term.length > 0);
    }

    /**
     * Term matching (simple)
     */
    termMatch(queryTerms, documentTerms) {
        let matchCount = 0;

        queryTerms.forEach(queryTerm => {
            if (documentTerms.some(docTerm => docTerm.includes(queryTerm))) {
                matchCount++;
            }
        });

        return queryTerms.length > 0 ? matchCount / queryTerms.length : 0;
    }

    /**
     * Fuzzy matching using Levenshtein distance
     */
    fuzzyMatch(queryTerms, documentTerms) {
        let totalScore = 0;

        queryTerms.forEach(queryTerm => {
            let bestScore = 0;

            documentTerms.forEach(docTerm => {
                const distance = this.levenshteinDistance(queryTerm, docTerm);
                const maxLength = Math.max(queryTerm.length, docTerm.length);
                const similarity = 1 - (distance / maxLength);

                if (similarity > bestScore) {
                    bestScore = similarity;
                }
            });

            totalScore += bestScore;
        });

        return queryTerms.length > 0 ? totalScore / queryTerms.length : 0;
    }

    /**
     * Calculate Levenshtein distance
     */
    levenshteinDistance(str1, str2) {
        const matrix = [];

        for (let i = 0; i <= str2.length; i++) {
            matrix[i] = [i];
        }

        for (let j = 0; j <= str1.length; j++) {
            matrix[0][j] = j;
        }

        for (let i = 1; i <= str2.length; i++) {
            for (let j = 1; j <= str1.length; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }

        return matrix[str2.length][str1.length];
    }

    /**
     * Highlight matches
     */
    highlightMatches(item, queryTerms) {
        const highlights = {};

        Object.entries(item).forEach(([key, value]) => {
            if (typeof value !== 'string') return;

            const valueLower = value.toLowerCase();
            let hasMatch = false;

            queryTerms.forEach(term => {
                if (valueLower.includes(term)) {
                    hasMatch = true;
                }
            });

            if (hasMatch) {
                highlights[key] = value;
            }
        });

        return highlights;
    }

    /**
     * Get nested value from object
     */
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => current?.[key], obj);
    }

    /**
     * Add to search history
     */
    addToHistory(query) {
        if (!query || query.trim() === '') return;

        // Remove if already exists
        const index = this.searchHistory.indexOf(query);
        if (index > -1) {
            this.searchHistory.splice(index, 1);
        }

        // Add to beginning
        this.searchHistory.unshift(query);

        // Trim to max size
        if (this.searchHistory.length > this.maxHistorySize) {
            this.searchHistory = this.searchHistory.slice(0, this.maxHistorySize);
        }

        // Persist to localStorage
        try {
            localStorage.setItem('search_history', JSON.stringify(this.searchHistory));
        } catch (error) {
            console.error('Failed to save search history:', error);
        }
    }

    /**
     * Load search history
     */
    loadHistory() {
        try {
            const saved = localStorage.getItem('search_history');
            if (saved) {
                this.searchHistory = JSON.parse(saved);
            }
        } catch (error) {
            console.error('Failed to load search history:', error);
        }
    }

    /**
     * Clear search history
     */
    clearHistory() {
        this.searchHistory = [];
        localStorage.removeItem('search_history');
    }

    /**
     * Get facet values
     */
    getFacets(field) {
        return this.facets.get(field) || new Map();
    }

    /**
     * Get all facets
     */
    getAllFacets() {
        const result = {};
        for (const [field, values] of this.facets) {
            result[field] = Object.fromEntries(values);
        }
        return result;
    }

    /**
     * Debounced search
     */
    debouncedSearch(query, callback, delay = this.debounceDelay) {
        clearTimeout(this.debounceTimer);

        this.debounceTimer = setTimeout(() => {
            const results = this.search(query);
            callback(results);
        }, delay);
    }

    /**
     * Clear index
     */
    clear() {
        this.searchIndex.clear();
        this.filters.clear();
        this.facets.clear();
    }
}

// Create singleton
const searchFilterSystem = new SearchFilterSystem();

// Load history on init
searchFilterSystem.loadHistory();

// Expose globally
if (typeof window !== 'undefined') {
    window.searchFilterSystem = searchFilterSystem;
    window.SearchFilterSystem = SearchFilterSystem;
}

export default searchFilterSystem;

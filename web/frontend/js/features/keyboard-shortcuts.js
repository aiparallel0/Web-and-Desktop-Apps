/**
 * Keyboard Shortcuts System
 * Global keyboard shortcut manager with customizable bindings
 */

import eventBus from '../core/event-bus.js';
import modalSystem from '../components/modal-system.js';

class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.sequences = new Map();
        this.enabled = true;
        this.sequenceTimeout = 1000;
        this.currentSequence = [];
        this.sequenceTimer = null;
        this.modifierKeys = {
            ctrl: 'Control',
            cmd: 'Meta',
            alt: 'Alt',
            shift: 'Shift'
        };

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.registerDefaultShortcuts();
    }

    setupEventListeners() {
        document.addEventListener('keydown', (e) => {
            if (!this.enabled) return;

            // Check if in input field
            const tagName = e.target.tagName.toLowerCase();
            const isInput = ['input', 'textarea', 'select'].includes(tagName);
            const isContentEditable = e.target.isContentEditable;

            if (isInput || isContentEditable) {
                // Only allow certain shortcuts in input fields
                if (!this.isGlobalShortcut(e)) return;
            }

            this.handleKeyDown(e);
        });
    }

    handleKeyDown(e) {
        const key = this.normalizeKey(e);
        const shortcutKey = this.buildShortcutKey(e);

        // Check direct shortcuts
        const shortcut = this.shortcuts.get(shortcutKey);
        if (shortcut) {
            if (shortcut.preventDefault !== false) {
                e.preventDefault();
            }

            this.executeShortcut(shortcut, e);
            return;
        }

        // Check sequences
        this.handleSequence(key);
    }

    handleSequence(key) {
        this.currentSequence.push(key);

        clearTimeout(this.sequenceTimer);
        this.sequenceTimer = setTimeout(() => {
            this.currentSequence = [];
        }, this.sequenceTimeout);

        const sequenceKey = this.currentSequence.join(' ');
        const sequence = this.sequences.get(sequenceKey);

        if (sequence) {
            this.executeShortcut(sequence);
            this.currentSequence = [];
            clearTimeout(this.sequenceTimer);
        }
    }

    executeShortcut(shortcut, event = null) {
        if (shortcut.condition && !shortcut.condition()) {
            return;
        }

        shortcut.handler(event);

        eventBus.emit('shortcut:executed', {
            name: shortcut.name,
            key: shortcut.key
        });
    }

    register(key, config) {
        const {
            name,
            description,
            handler,
            condition = null,
            preventDefault = true,
            global = false,
            sequence = false
        } = config;

        const shortcutData = {
            key,
            name,
            description,
            handler,
            condition,
            preventDefault,
            global,
            sequence
        };

        if (sequence) {
            this.sequences.set(key, shortcutData);
        } else {
            this.shortcuts.set(key, shortcutData);
        }

        return () => this.unregister(key, sequence);
    }

    unregister(key, sequence = false) {
        if (sequence) {
            this.sequences.delete(key);
        } else {
            this.shortcuts.delete(key);
        }
    }

    buildShortcutKey(e) {
        const parts = [];

        if (e.ctrlKey || e.metaKey) parts.push('ctrl');
        if (e.altKey) parts.push('alt');
        if (e.shiftKey) parts.push('shift');

        const key = this.normalizeKey(e);
        if (key) parts.push(key);

        return parts.join('+');
    }

    normalizeKey(e) {
        let key = e.key.toLowerCase();

        // Normalize special keys
        const keyMap = {
            'escape': 'esc',
            'arrowup': 'up',
            'arrowdown': 'down',
            'arrowleft': 'left',
            'arrowright': 'right',
            ' ': 'space'
        };

        return keyMap[key] || key;
    }

    isGlobalShortcut(e) {
        const shortcutKey = this.buildShortcutKey(e);
        const shortcut = this.shortcuts.get(shortcutKey);
        return shortcut && shortcut.global;
    }

    registerDefaultShortcuts() {
        // Navigation
        this.register('ctrl+/', {
            name: 'Show shortcuts',
            description: 'Display keyboard shortcuts help',
            global: true,
            handler: () => this.showShortcutsDialog()
        });

        this.register('ctrl+k', {
            name: 'Quick search',
            description: 'Open quick search dialog',
            global: true,
            handler: () => eventBus.emit('search:open')
        });

        this.register('esc', {
            name: 'Close',
            description: 'Close modal/dialog',
            handler: () => {
                if (modalSystem.hasOpenModals()) {
                    const topModal = modalSystem.getTopModal();
                    if (topModal) {
                        modalSystem.close(topModal.id);
                    }
                }
            },
            preventDefault: false
        });

        // Selection
        this.register('ctrl+a', {
            name: 'Select all',
            description: 'Select all items in current view',
            handler: (e) => {
                e.preventDefault();
                eventBus.emit('selection:selectAll');
            }
        });

        // Copy/Paste
        this.register('ctrl+c', {
            name: 'Copy',
            description: 'Copy selected items',
            handler: () => eventBus.emit('clipboard:copy'),
            preventDefault: false
        });

        this.register('ctrl+x', {
            name: 'Cut',
            description: 'Cut selected items',
            handler: () => eventBus.emit('clipboard:cut'),
            preventDefault: false
        });

        this.register('ctrl+v', {
            name: 'Paste',
            description: 'Paste from clipboard',
            handler: () => eventBus.emit('clipboard:paste'),
            preventDefault: false
        });

        // Actions
        this.register('ctrl+n', {
            name: 'New',
            description: 'Create new item',
            handler: (e) => {
                e.preventDefault();
                eventBus.emit('action:new');
            }
        });

        this.register('ctrl+s', {
            name: 'Save',
            description: 'Save current changes',
            global: true,
            handler: (e) => {
                e.preventDefault();
                eventBus.emit('action:save');
            }
        });

        this.register('ctrl+e', {
            name: 'Export',
            description: 'Export data',
            handler: (e) => {
                e.preventDefault();
                eventBus.emit('action:export');
            }
        });

        this.register('delete', {
            name: 'Delete',
            description: 'Delete selected items',
            handler: () => eventBus.emit('action:delete')
        });

        // Navigation with arrows
        this.register('up', {
            name: 'Navigate up',
            description: 'Move selection up',
            handler: () => eventBus.emit('navigation:up'),
            preventDefault: false
        });

        this.register('down', {
            name: 'Navigate down',
            description: 'Move selection down',
            handler: () => eventBus.emit('navigation:down'),
            preventDefault: false
        });

        // View
        this.register('ctrl+1', {
            name: 'Dashboard',
            description: 'Go to dashboard',
            handler: (e) => {
                e.preventDefault();
                eventBus.emit('navigate:dashboard');
            }
        });

        this.register('ctrl+2', {
            name: 'Extractions',
            description: 'Go to extractions',
            handler: (e) => {
                e.preventDefault();
                eventBus.emit('navigate:extractions');
            }
        });

        this.register('ctrl+3', {
            name: 'Batch',
            description: 'Go to batch processing',
            handler: (e) => {
                e.preventDefault();
                eventBus.emit('navigate:batch');
            }
        });

        // Refresh
        this.register('ctrl+r', {
            name: 'Refresh',
            description: 'Refresh current view',
            handler: (e) => {
                e.preventDefault();
                eventBus.emit('action:refresh');
            }
        });

        // Toggle features
        this.register('ctrl+d', {
            name: 'Toggle dark mode',
            description: 'Switch between light and dark theme',
            global: true,
            handler: (e) => {
                e.preventDefault();
                eventBus.emit('theme:toggle');
            }
        });

        // Help
        this.register('f1', {
            name: 'Help',
            description: 'Show help documentation',
            handler: (e) => {
                e.preventDefault();
                eventBus.emit('help:show');
            }
        });

        // Sequences
        this.register('g d', {
            name: 'Go to dashboard',
            description: 'Navigate to dashboard',
            sequence: true,
            handler: () => eventBus.emit('navigate:dashboard')
        });

        this.register('g e', {
            name: 'Go to extractions',
            description: 'Navigate to extractions',
            sequence: true,
            handler: () => eventBus.emit('navigate:extractions')
        });

        this.register('g b', {
            name: 'Go to batch',
            description: 'Navigate to batch processing',
            sequence: true,
            handler: () => eventBus.emit('navigate:batch')
        });
    }

    showShortcutsDialog() {
        const shortcuts = this.getAllShortcuts();
        
        const categories = {
            'Navigation': [],
            'Actions': [],
            'Selection': [],
            'View': [],
            'Other': []
        };

        shortcuts.forEach(shortcut => {
            const category = this.categorizeShortcut(shortcut);
            categories[category].push(shortcut);
        });

        const content = `
            <div class="shortcuts-dialog">
                ${Object.entries(categories).map(([category, items]) => {
                    if (items.length === 0) return '';
                    
                    return `
                        <div class="shortcuts-category">
                            <h3>${category}</h3>
                            <div class="shortcuts-list">
                                ${items.map(s => `
                                    <div class="shortcut-item">
                                        <div class="shortcut-keys">${this.formatShortcut(s.key)}</div>
                                        <div class="shortcut-desc">${s.description}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        modalSystem.open('keyboard-shortcuts', content, {
            title: 'Keyboard Shortcuts',
            size: 'large',
            showClose: true
        });
    }

    categorizeShortcut(shortcut) {
        const name = shortcut.name.toLowerCase();
        
        if (name.includes('navigate') || name.includes('go to')) return 'Navigation';
        if (name.includes('select') || name.includes('copy') || name.includes('paste')) return 'Selection';
        if (name.includes('view') || name.includes('toggle')) return 'View';
        if (name.includes('save') || name.includes('delete') || name.includes('export')) return 'Actions';
        
        return 'Other';
    }

    formatShortcut(key) {
        return key.split('+').map(part => {
            const formatted = {
                'ctrl': window.navigator.platform.includes('Mac') ? '⌘' : 'Ctrl',
                'alt': window.navigator.platform.includes('Mac') ? '⌥' : 'Alt',
                'shift': '⇧',
                'esc': 'Esc',
                'delete': 'Del',
                'space': 'Space'
            };

            return formatted[part] || part.toUpperCase();
        }).join(' + ');
    }

    getAllShortcuts() {
        const all = [];

        for (const shortcut of this.shortcuts.values()) {
            all.push(shortcut);
        }

        for (const sequence of this.sequences.values()) {
            all.push(sequence);
        }

        return all;
    }

    enable() {
        this.enabled = true;
    }

    disable() {
        this.enabled = false;
    }

    toggle() {
        this.enabled = !this.enabled;
    }

    isEnabled() {
        return this.enabled;
    }
}

// Create singleton
const keyboardShortcuts = new KeyboardShortcuts();

// Expose globally
if (typeof window !== 'undefined') {
    window.keyboardShortcuts = keyboardShortcuts;
    window.KeyboardShortcuts = KeyboardShortcuts;
}

export default keyboardShortcuts;

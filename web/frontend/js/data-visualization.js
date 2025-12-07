/**
 * Data Visualization and Reporting System
 * Creates charts, reports, and data visualizations
 * @version 2.0.0
 */

(function(window) {
    'use strict';

    class DataVisualization {
        constructor() {
            this.charts = new Map();
            this.colors = {
                primary: '#3b82f6',
                success: '#10b981',
                warning: '#f59e0b',
                danger: '#ef4444',
                info: '#6366f1',
                neutral: '#6b7280'
            };
            this.colorPalette = [
                '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
                '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'
            ];
        }

        /**
         * Create bar chart
         */
        createBarChart(canvasId, data, options = {}) {
            const canvas = document.getElementById(canvasId);
            if (!canvas || !window.Chart) {
                console.error('Canvas or Chart.js not found');
                return null;
            }

            const config = {
                type: 'bar',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: options.label || 'Data',
                        data: data.values || [],
                        backgroundColor: options.color || this.colors.primary,
                        borderColor: options.borderColor || this.colors.primary,
                        borderWidth: options.borderWidth || 0,
                        borderRadius: options.borderRadius || 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: options.maintainAspectRatio !== false,
                    plugins: {
                        legend: {
                            display: options.showLegend !== false
                        },
                        tooltip: {
                            enabled: options.showTooltip !== false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                display: options.showGrid !== false
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    },
                    ...options.chartOptions
                }
            };

            // Destroy existing chart if present
            if (this.charts.has(canvasId)) {
                this.charts.get(canvasId).destroy();
            }

            const chart = new Chart(canvas, config);
            this.charts.set(canvasId, chart);
            
            return chart;
        }

        /**
         * Create line chart
         */
        createLineChart(canvasId, data, options = {}) {
            const canvas = document.getElementById(canvasId);
            if (!canvas || !window.Chart) {
                console.error('Canvas or Chart.js not found');
                return null;
            }

            const datasets = Array.isArray(data.datasets) ? data.datasets : [{
                label: options.label || 'Data',
                data: data.values || [],
                borderColor: options.color || this.colors.primary,
                backgroundColor: options.fill ? this.hexToRgba(options.color || this.colors.primary, 0.1) : 'transparent',
                tension: options.tension || 0.4,
                fill: options.fill || false,
                pointRadius: options.pointRadius || 3,
                pointHoverRadius: options.pointHoverRadius || 5
            }];

            const config = {
                type: 'line',
                data: {
                    labels: data.labels || [],
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: options.maintainAspectRatio !== false,
                    plugins: {
                        legend: {
                            display: options.showLegend !== false
                        },
                        tooltip: {
                            enabled: options.showTooltip !== false,
                            mode: 'index',
                            intersect: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                display: options.showGrid !== false
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    },
                    ...options.chartOptions
                }
            };

            if (this.charts.has(canvasId)) {
                this.charts.get(canvasId).destroy();
            }

            const chart = new Chart(canvas, config);
            this.charts.set(canvasId, chart);
            
            return chart;
        }

        /**
         * Create pie/doughnut chart
         */
        createPieChart(canvasId, data, options = {}) {
            const canvas = document.getElementById(canvasId);
            if (!canvas || !window.Chart) {
                console.error('Canvas or Chart.js not found');
                return null;
            }

            const config = {
                type: options.doughnut ? 'doughnut' : 'pie',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.values || [],
                        backgroundColor: options.colors || this.colorPalette,
                        borderWidth: options.borderWidth || 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: options.maintainAspectRatio !== false,
                    plugins: {
                        legend: {
                            display: options.showLegend !== false,
                            position: options.legendPosition || 'bottom'
                        },
                        tooltip: {
                            enabled: options.showTooltip !== false,
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    ...options.chartOptions
                }
            };

            if (this.charts.has(canvasId)) {
                this.charts.get(canvasId).destroy();
            }

            const chart = new Chart(canvas, config);
            this.charts.set(canvasId, chart);
            
            return chart;
        }

        /**
         * Create sparkline (mini chart)
         */
        createSparkline(canvasId, values, options = {}) {
            const canvas = document.getElementById(canvasId);
            if (!canvas || !window.Chart) {
                console.error('Canvas or Chart.js not found');
                return null;
            }

            const config = {
                type: 'line',
                data: {
                    labels: values.map((_, i) => i),
                    datasets: [{
                        data: values,
                        borderColor: options.color || this.colors.primary,
                        borderWidth: options.lineWidth || 2,
                        fill: false,
                        pointRadius: 0,
                        pointHoverRadius: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: false }
                    },
                    scales: {
                        x: { display: false },
                        y: { display: false }
                    },
                    elements: {
                        line: {
                            tension: 0.4
                        }
                    }
                }
            };

            if (this.charts.has(canvasId)) {
                this.charts.get(canvasId).destroy();
            }

            const chart = new Chart(canvas, config);
            this.charts.set(canvasId, chart);
            
            return chart;
        }

        /**
         * Create progress ring
         */
        createProgressRing(containerId, value, max = 100, options = {}) {
            const container = document.getElementById(containerId);
            if (!container) return null;

            const percentage = (value / max) * 100;
            const size = options.size || 120;
            const strokeWidth = options.strokeWidth || 10;
            const radius = (size - strokeWidth) / 2;
            const circumference = 2 * Math.PI * radius;
            const offset = circumference - (percentage / 100) * circumference;

            container.innerHTML = `
                <svg width="${size}" height="${size}" style="transform: rotate(-90deg);">
                    <circle
                        cx="${size / 2}"
                        cy="${size / 2}"
                        r="${radius}"
                        fill="none"
                        stroke="#e5e7eb"
                        stroke-width="${strokeWidth}"
                    />
                    <circle
                        cx="${size / 2}"
                        cy="${size / 2}"
                        r="${radius}"
                        fill="none"
                        stroke="${options.color || this.colors.primary}"
                        stroke-width="${strokeWidth}"
                        stroke-dasharray="${circumference}"
                        stroke-dashoffset="${offset}"
                        stroke-linecap="round"
                        style="transition: stroke-dashoffset 0.5s ease;"
                    />
                </svg>
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
                    <div style="font-size: ${size * 0.25}px; font-weight: 600; color: #111827;">${Math.round(percentage)}%</div>
                    ${options.label ? `<div style="font-size: ${size * 0.12}px; color: #6b7280;">${options.label}</div>` : ''}
                </div>
            `;

            container.style.position = 'relative';
            container.style.width = size + 'px';
            container.style.height = size + 'px';

            return container;
        }

        /**
         * Create heatmap
         */
        createHeatmap(containerId, data, options = {}) {
            const container = document.getElementById(containerId);
            if (!container) return null;

            const cellSize = options.cellSize || 30;
            const gap = options.gap || 2;
            const rows = data.length;
            const cols = data[0]?.length || 0;

            // Find min and max values for color scaling
            let min = Infinity, max = -Infinity;
            data.forEach(row => {
                row.forEach(value => {
                    if (value < min) min = value;
                    if (value > max) max = value;
                });
            });

            container.innerHTML = '';
            container.style.cssText = `
                display: grid;
                grid-template-columns: repeat(${cols}, ${cellSize}px);
                gap: ${gap}px;
            `;

            data.forEach((row, i) => {
                row.forEach((value, j) => {
                    const cell = document.createElement('div');
                    const intensity = (value - min) / (max - min);
                    cell.style.cssText = `
                        width: ${cellSize}px;
                        height: ${cellSize}px;
                        background: ${this.interpolateColor(intensity, options.startColor || '#dbeafe', options.endColor || '#1e40af')};
                        border-radius: 4px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 11px;
                        color: ${intensity > 0.5 ? 'white' : '#111827'};
                        cursor: pointer;
                    `;
                    
                    if (options.showValues) {
                        cell.textContent = value;
                    }

                    cell.title = `Row ${i + 1}, Col ${j + 1}: ${value}`;
                    container.appendChild(cell);
                });
            });

            return container;
        }

        /**
         * Create statistics summary card
         */
        createStatsSummary(containerId, stats) {
            const container = document.getElementById(containerId);
            if (!container) return null;

            container.innerHTML = '';
            container.style.cssText = `
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            `;

            Object.entries(stats).forEach(([key, value]) => {
                const card = document.createElement('div');
                card.style.cssText = `
                    background: white;
                    border-radius: 12px;
                    padding: 20px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                `;

                const label = key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
                
                card.innerHTML = `
                    <div style="font-size: 14px; color: #6b7280; margin-bottom: 8px;">${label}</div>
                    <div style="font-size: 32px; font-weight: 700; color: #111827;">${this.formatNumber(value)}</div>
                `;

                container.appendChild(card);
            });

            return container;
        }

        /**
         * Create trend indicator
         */
        createTrendIndicator(value, previousValue, options = {}) {
            const change = value - previousValue;
            const percentChange = previousValue !== 0 ? (change / previousValue) * 100 : 0;
            const isPositive = change >= 0;

            const indicator = document.createElement('span');
            indicator.style.cssText = `
                display: inline-flex;
                align-items: center;
                gap: 4px;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
                background: ${isPositive ? '#d1fae5' : '#fee2e2'};
                color: ${isPositive ? '#065f46' : '#991b1b'};
            `;

            const arrow = isPositive ? '↑' : '↓';
            indicator.textContent = `${arrow} ${Math.abs(percentChange).toFixed(1)}%`;

            return indicator;
        }

        /**
         * Create data table with sortable columns
         */
        createDataTable(containerId, data, columns, options = {}) {
            const container = document.getElementById(containerId);
            if (!container) return null;

            const table = document.createElement('table');
            table.className = 'data-visualization-table';
            table.style.cssText = `
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            `;

            // Create header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            headerRow.style.cssText = 'background: #f9fafb; border-bottom: 2px solid #e5e7eb;';

            columns.forEach(col => {
                const th = document.createElement('th');
                th.textContent = col.label || col.key;
                th.style.cssText = `
                    padding: 12px 16px;
                    text-align: left;
                    font-weight: 600;
                    color: #374151;
                    cursor: pointer;
                    user-select: none;
                `;

                if (col.sortable !== false) {
                    th.addEventListener('click', () => {
                        this.sortTable(table, col.key);
                    });
                }

                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Create body
            const tbody = document.createElement('tbody');
            this.populateTableBody(tbody, data, columns, options);
            table.appendChild(tbody);

            container.innerHTML = '';
            container.appendChild(table);

            return table;
        }

        /**
         * Populate table body
         */
        populateTableBody(tbody, data, columns, options = {}) {
            tbody.innerHTML = '';

            data.forEach((row, index) => {
                const tr = document.createElement('tr');
                tr.style.cssText = `
                    border-bottom: 1px solid #e5e7eb;
                    transition: background 0.2s;
                `;

                tr.addEventListener('mouseenter', () => {
                    tr.style.background = '#f9fafb';
                });

                tr.addEventListener('mouseleave', () => {
                    tr.style.background = 'transparent';
                });

                columns.forEach(col => {
                    const td = document.createElement('td');
                    td.style.cssText = 'padding: 12px 16px; color: #111827;';

                    let value = row[col.key];

                    // Apply formatter if provided
                    if (col.format) {
                        value = col.format(value, row);
                    } else if (typeof value === 'number') {
                        value = this.formatNumber(value);
                    }

                    if (typeof value === 'string' || typeof value === 'number') {
                        td.textContent = value;
                    } else if (value instanceof HTMLElement) {
                        td.appendChild(value);
                    }

                    tr.appendChild(td);
                });

                tbody.appendChild(tr);
            });
        }

        /**
         * Sort table
         */
        sortTable(table, key) {
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            // Determine sort direction
            const currentDirection = table.dataset.sortDirection || 'asc';
            const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
            table.dataset.sortDirection = newDirection;

            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.dataset[key] || a.textContent;
                const bValue = b.dataset[key] || b.textContent;

                if (newDirection === 'asc') {
                    return aValue.localeCompare(bValue);
                } else {
                    return bValue.localeCompare(aValue);
                }
            });

            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));
        }

        /**
         * Export chart as image
         */
        exportChart(canvasId, filename = 'chart.png') {
            const chart = this.charts.get(canvasId);
            if (!chart) {
                console.error('Chart not found');
                return;
            }

            const url = chart.toBase64Image();
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.click();
        }

        /**
         * Update chart data
         */
        updateChart(canvasId, newData) {
            const chart = this.charts.get(canvasId);
            if (!chart) {
                console.error('Chart not found');
                return;
            }

            if (newData.labels) {
                chart.data.labels = newData.labels;
            }

            if (newData.values || newData.datasets) {
                if (newData.datasets) {
                    chart.data.datasets = newData.datasets;
                } else if (newData.values) {
                    chart.data.datasets[0].data = newData.values;
                }
            }

            chart.update();
        }

        /**
         * Destroy chart
         */
        destroyChart(canvasId) {
            const chart = this.charts.get(canvasId);
            if (chart) {
                chart.destroy();
                this.charts.delete(canvasId);
            }
        }

        /**
         * Destroy all charts
         */
        destroyAllCharts() {
            this.charts.forEach(chart => chart.destroy());
            this.charts.clear();
        }

        /**
         * Hex to RGBA
         */
        hexToRgba(hex, alpha = 1) {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            if (!result) return hex;

            const r = parseInt(result[1], 16);
            const g = parseInt(result[2], 16);
            const b = parseInt(result[3], 16);

            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }

        /**
         * Interpolate between two colors
         */
        interpolateColor(value, startColor, endColor) {
            // Simple linear interpolation
            const start = this.hexToRgb(startColor);
            const end = this.hexToRgb(endColor);

            const r = Math.round(start.r + (end.r - start.r) * value);
            const g = Math.round(start.g + (end.g - start.g) * value);
            const b = Math.round(start.b + (end.b - start.b) * value);

            return `rgb(${r}, ${g}, ${b})`;
        }

        /**
         * Hex to RGB
         */
        hexToRgb(hex) {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? {
                r: parseInt(result[1], 16),
                g: parseInt(result[2], 16),
                b: parseInt(result[3], 16)
            } : { r: 0, g: 0, b: 0 };
        }

        /**
         * Format number
         */
        formatNumber(value) {
            if (typeof value !== 'number') return value;

            // Format with commas
            if (value >= 1000) {
                return value.toLocaleString('en-US');
            }

            // Round to 2 decimal places if needed
            if (value % 1 !== 0) {
                return value.toFixed(2);
            }

            return value.toString();
        }

        /**
         * Format currency
         */
        formatCurrency(value, currency = 'USD') {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: currency
            }).format(value);
        }

        /**
         * Format percentage
         */
        formatPercentage(value, decimals = 1) {
            return `${value.toFixed(decimals)}%`;
        }

        /**
         * Calculate statistics
         */
        calculateStats(values) {
            const sorted = [...values].sort((a, b) => a - b);
            const sum = values.reduce((a, b) => a + b, 0);
            const mean = sum / values.length;

            return {
                count: values.length,
                sum: sum,
                mean: mean,
                median: this.calculateMedian(sorted),
                min: sorted[0],
                max: sorted[sorted.length - 1],
                range: sorted[sorted.length - 1] - sorted[0],
                variance: this.calculateVariance(values, mean),
                stdDev: this.calculateStdDev(values, mean)
            };
        }

        calculateMedian(sorted) {
            const mid = Math.floor(sorted.length / 2);
            return sorted.length % 2 === 0
                ? (sorted[mid - 1] + sorted[mid]) / 2
                : sorted[mid];
        }

        calculateVariance(values, mean) {
            const squaredDiffs = values.map(v => Math.pow(v - mean, 2));
            return squaredDiffs.reduce((a, b) => a + b, 0) / values.length;
        }

        calculateStdDev(values, mean) {
            return Math.sqrt(this.calculateVariance(values, mean));
        }
    }

    // Export
    window.DataVisualization = new DataVisualization();

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = DataVisualization;
    }

})(window);

/**
 * Data Visualization Component
 * Interactive charts and graphs for analytics display
 */

class DataVisualization {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container with id "${containerId}" not found`);
        }

        this.options = {
            theme: 'light',
            responsive: true,
            ...options
        };

        this.charts = [];
        this.init();
    }

    init() {
        this.addStyles();
    }

    addStyles() {
        if (document.getElementById('dataviz-styles')) return;

        const style = document.createElement('style');
        style.id = 'dataviz-styles';
        style.textContent = `
            .dataviz-wrapper {
                width: 100%;
                height: 100%;
                position: relative;
            }

            .dataviz-chart {
                width: 100%;
                height: 100%;
            }

            .dataviz-legend {
                display: flex;
                flex-wrap: wrap;
                gap: var(--space-2);
                margin-top: var(--space-3);
                justify-content: center;
            }

            .legend-item {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 0.875rem;
                color: var(--color-gray-700);
            }

            .legend-color {
                width: 16px;
                height: 16px;
                border-radius: 3px;
            }

            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: var(--space-3);
                margin: var(--space-4) 0;
            }

            .stat-box {
                text-align: center;
                padding: var(--space-3);
                background: var(--color-gray-50);
                border-radius: var(--radius-lg);
                border: 1px solid var(--color-gray-200);
            }

            .stat-value {
                font-size: 2rem;
                font-weight: var(--font-bold);
                color: var(--color-gray-900);
                margin-bottom: 4px;
            }

            .stat-label {
                font-size: 0.875rem;
                color: var(--color-gray-600);
            }

            .stat-change {
                font-size: 0.75rem;
                font-weight: var(--font-semibold);
                margin-top: 4px;
            }

            .stat-change.positive {
                color: var(--color-success-dark);
            }

            .stat-change.negative {
                color: var(--color-danger);
            }

            .progress-chart {
                width: 100%;
                margin: var(--space-3) 0;
            }

            .progress-row {
                display: flex;
                align-items: center;
                margin-bottom: var(--space-2);
            }

            .progress-label {
                flex: 0 0 120px;
                font-size: 0.875rem;
                color: var(--color-gray-700);
                font-weight: var(--font-medium);
            }

            .progress-bar-wrapper {
                flex: 1;
                height: 24px;
                background: var(--color-gray-200);
                border-radius: var(--radius-md);
                overflow: hidden;
                position: relative;
            }

            .progress-bar-fill {
                height: 100%;
                background: var(--color-primary);
                border-radius: var(--radius-md);
                transition: width var(--transition-slow);
                display: flex;
                align-items: center;
                justify-content: flex-end;
                padding-right: 8px;
            }

            .progress-value {
                color: white;
                font-size: 0.75rem;
                font-weight: var(--font-semibold);
            }

            .pie-chart-container {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: var(--space-6);
                flex-wrap: wrap;
            }

            .pie-chart {
                position: relative;
                width: 200px;
                height: 200px;
            }

            .pie-chart svg {
                transform: rotate(-90deg);
            }

            .pie-chart-center {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
            }

            .pie-chart-total {
                font-size: 2rem;
                font-weight: var(--font-bold);
                color: var(--color-gray-900);
            }

            .pie-chart-label {
                font-size: 0.875rem;
                color: var(--color-gray-600);
            }

            .trend-line-chart {
                width: 100%;
                height: 300px;
                position: relative;
            }

            .chart-grid {
                position: absolute;
                inset: 0;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }

            .chart-grid-line {
                height: 1px;
                background: var(--color-gray-200);
            }

            .chart-path {
                fill: none;
                stroke: var(--color-primary);
                stroke-width: 3;
                stroke-linecap: round;
                stroke-linejoin: round;
            }

            .chart-area {
                fill: var(--color-primary);
                opacity: 0.1;
            }

            .chart-point {
                fill: white;
                stroke: var(--color-primary);
                stroke-width: 3;
                cursor: pointer;
                transition: all var(--transition-fast);
            }

            .chart-point:hover {
                r: 6;
                stroke-width: 4;
            }

            .chart-tooltip {
                position: absolute;
                background: var(--color-gray-900);
                color: white;
                padding: 8px 12px;
                border-radius: var(--radius-md);
                font-size: 0.875rem;
                pointer-events: none;
                opacity: 0;
                transition: opacity var(--transition-fast);
                z-index: 100;
            }

            .chart-tooltip.active {
                opacity: 1;
            }

            .heatmap-grid {
                display: grid;
                gap: 4px;
                margin: var(--space-3) 0;
            }

            .heatmap-row {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(30px, 1fr));
                gap: 4px;
            }

            .heatmap-cell {
                aspect-ratio: 1;
                border-radius: 3px;
                background: var(--color-gray-200);
                cursor: pointer;
                transition: all var(--transition-fast);
            }

            .heatmap-cell:hover {
                transform: scale(1.1);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            }

            .heatmap-cell.level-1 {
                background: #ebedf0;
            }

            .heatmap-cell.level-2 {
                background: #c6e48b;
            }

            .heatmap-cell.level-3 {
                background: #7bc96f;
            }

            .heatmap-cell.level-4 {
                background: #239a3b;
            }

            .heatmap-cell.level-5 {
                background: #196127;
            }

            @media (max-width: 768px) {
                .pie-chart-container {
                    flex-direction: column;
                }

                .trend-line-chart {
                    height: 200px;
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Create a bar chart
     */
    createBarChart(data, config = {}) {
        const wrapper = document.createElement('div');
        wrapper.className = 'dataviz-wrapper progress-chart';

        data.forEach(item => {
            const row = document.createElement('div');
            row.className = 'progress-row';
            row.innerHTML = `
                <div class="progress-label">${item.label}</div>
                <div class="progress-bar-wrapper">
                    <div class="progress-bar-fill" style="width: ${item.percentage}%; background-color: ${item.color || 'var(--color-primary)'};">
                        <span class="progress-value">${item.value}</span>
                    </div>
                </div>
            `;
            wrapper.appendChild(row);
        });

        this.container.appendChild(wrapper);
        return wrapper;
    }

    /**
     * Create a pie chart
     */
    createPieChart(data, config = {}) {
        const total = data.reduce((sum, item) => sum + item.value, 0);
        const wrapper = document.createElement('div');
        wrapper.className = 'pie-chart-container';

        // Create SVG pie chart
        const pieChart = document.createElement('div');
        pieChart.className = 'pie-chart';

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '200');
        svg.setAttribute('height', '200');
        svg.setAttribute('viewBox', '0 0 200 200');

        const radius = 80;
        const centerX = 100;
        const centerY = 100;
        let currentAngle = 0;

        const colors = [
            '#3B82F6', '#10B981', '#F59E0B', '#EF4444', 
            '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'
        ];

        data.forEach((item, index) => {
            const percentage = (item.value / total) * 100;
            const angle = (percentage / 100) * 360;
            
            const slice = this.createPieSlice(
                centerX, centerY, radius,
                currentAngle, angle,
                item.color || colors[index % colors.length]
            );
            
            svg.appendChild(slice);
            currentAngle += angle;
        });

        pieChart.appendChild(svg);

        // Add center text
        const center = document.createElement('div');
        center.className = 'pie-chart-center';
        center.innerHTML = `
            <div class="pie-chart-total">${total}</div>
            <div class="pie-chart-label">Total</div>
        `;
        pieChart.appendChild(center);

        // Create legend
        const legend = document.createElement('div');
        legend.className = 'dataviz-legend';
        data.forEach((item, index) => {
            legend.innerHTML += `
                <div class="legend-item">
                    <div class="legend-color" style="background-color: ${item.color || colors[index % colors.length]};"></div>
                    <span>${item.label}: ${item.value}</span>
                </div>
            `;
        });

        wrapper.appendChild(pieChart);
        wrapper.appendChild(legend);
        this.container.appendChild(wrapper);
        return wrapper;
    }

    /**
     * Helper to create pie slice
     */
    createPieSlice(cx, cy, r, startAngle, angle, color) {
        const startRad = (startAngle * Math.PI) / 180;
        const endRad = ((startAngle + angle) * Math.PI) / 180;
        
        const x1 = cx + r * Math.cos(startRad);
        const y1 = cy + r * Math.sin(startRad);
        const x2 = cx + r * Math.cos(endRad);
        const y2 = cy + r * Math.sin(endRad);
        
        const largeArc = angle > 180 ? 1 : 0;
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', `
            M ${cx} ${cy}
            L ${x1} ${y1}
            A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}
            Z
        `);
        path.setAttribute('fill', color);
        path.setAttribute('opacity', '0.9');
        path.classList.add('pie-slice');
        
        return path;
    }

    /**
     * Create a line chart
     */
    createLineChart(data, config = {}) {
        const wrapper = document.createElement('div');
        wrapper.className = 'trend-line-chart';

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '100%');
        svg.setAttribute('viewBox', '0 0 800 300');

        const maxValue = Math.max(...data.map(d => d.value));
        const padding = 40;
        const width = 800 - padding * 2;
        const height = 300 - padding * 2;

        // Create path for line
        const points = data.map((d, i) => {
            const x = padding + (i / (data.length - 1)) * width;
            const y = padding + height - (d.value / maxValue) * height;
            return { x, y, label: d.label, value: d.value };
        });

        // Draw area
        const areaPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const areaD = [
            `M ${padding} ${padding + height}`,
            ...points.map(p => `L ${p.x} ${p.y}`),
            `L ${padding + width} ${padding + height}`,
            'Z'
        ].join(' ');
        areaPath.setAttribute('d', areaD);
        areaPath.setAttribute('class', 'chart-area');
        svg.appendChild(areaPath);

        // Draw line
        const linePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const lineD = points.map((p, i) => 
            `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
        ).join(' ');
        linePath.setAttribute('d', lineD);
        linePath.setAttribute('class', 'chart-path');
        svg.appendChild(linePath);

        // Draw points
        const tooltip = document.createElement('div');
        tooltip.className = 'chart-tooltip';
        wrapper.appendChild(tooltip);

        points.forEach(p => {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', p.x);
            circle.setAttribute('cy', p.y);
            circle.setAttribute('r', '4');
            circle.setAttribute('class', 'chart-point');
            
            circle.addEventListener('mouseenter', (e) => {
                tooltip.innerHTML = `
                    <div><strong>${p.label}</strong></div>
                    <div>${p.value}</div>
                `;
                tooltip.classList.add('active');
                tooltip.style.left = p.x + 'px';
                tooltip.style.top = (p.y - 40) + 'px';
            });
            
            circle.addEventListener('mouseleave', () => {
                tooltip.classList.remove('active');
            });
            
            svg.appendChild(circle);
        });

        wrapper.appendChild(svg);
        this.container.appendChild(wrapper);
        return wrapper;
    }

    /**
     * Create a heatmap
     */
    createHeatmap(data, config = {}) {
        const wrapper = document.createElement('div');
        wrapper.className = 'heatmap-grid';

        data.forEach(row => {
            const rowEl = document.createElement('div');
            rowEl.className = 'heatmap-row';
            
            row.forEach(cell => {
                const cellEl = document.createElement('div');
                cellEl.className = `heatmap-cell level-${cell.level || 1}`;
                cellEl.title = cell.label || '';
                cellEl.dataset.value = cell.value || 0;
                rowEl.appendChild(cellEl);
            });
            
            wrapper.appendChild(rowEl);
        });

        this.container.appendChild(wrapper);
        return wrapper;
    }

    /**
     * Create stats grid
     */
    createStatsGrid(data) {
        const wrapper = document.createElement('div');
        wrapper.className = 'stats-grid';

        data.forEach(stat => {
            const box = document.createElement('div');
            box.className = 'stat-box';
            box.innerHTML = `
                <div class="stat-value">${stat.value}</div>
                <div class="stat-label">${stat.label}</div>
                ${stat.change ? `
                    <div class="stat-change ${stat.change > 0 ? 'positive' : 'negative'}">
                        ${stat.change > 0 ? '↑' : '↓'} ${Math.abs(stat.change)}%
                    </div>
                ` : ''}
            `;
            wrapper.appendChild(box);
        });

        this.container.appendChild(wrapper);
        return wrapper;
    }

    /**
     * Clear all visualizations
     */
    clear() {
        this.container.innerHTML = '';
        this.charts = [];
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataVisualization;
}
window.DataVisualization = DataVisualization;

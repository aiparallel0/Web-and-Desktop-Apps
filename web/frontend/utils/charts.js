/**
 * Chart Builder - Data visualization utility
 * Creates charts and graphs for analytics and receipt data
 */

class ChartBuilder {
    constructor(canvas, options = {}) {
        this.canvas = typeof canvas === 'string' ? document.getElementById(canvas) : canvas;
        if (!this.canvas) {
            throw new Error('Canvas element not found');
        }

        this.ctx = this.canvas.getContext('2d');
        this.options = {
            responsive: true,
            maintainAspectRatio: true,
            padding: 20,
            colors: [
                '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
                '#EC4899', '#14B8A6', '#F97316', '#06B6D4', '#84CC16'
            ],
            ...options
        };

        this.data = null;
        this.chart = null;
    }

    /**
     * Create bar chart
     */
    createBarChart(data, options = {}) {
        this.data = data;
        const config = {
            type: 'bar',
            labels: data.labels || [],
            datasets: data.datasets || [],
            ...this.options,
            ...options
        };

        this.drawBarChart(config);
    }

    /**
     * Create line chart
     */
    createLineChart(data, options = {}) {
        this.data = data;
        const config = {
            type: 'line',
            labels: data.labels || [],
            datasets: data.datasets || [],
            ...this.options,
            ...options
        };

        this.drawLineChart(config);
    }

    /**
     * Create pie chart
     */
    createPieChart(data, options = {}) {
        this.data = data;
        const config = {
            type: 'pie',
            labels: data.labels || [],
            values: data.values || [],
            colors: data.colors || this.options.colors,
            ...this.options,
            ...options
        };

        this.drawPieChart(config);
    }

    /**
     * Draw bar chart
     */
    drawBarChart(config) {
        const { width, height } = this.canvas;
        const ctx = this.ctx;
        const padding = config.padding;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Get data
        const labels = config.labels;
        const datasets = config.datasets;

        if (!labels.length || !datasets.length) return;

        // Calculate dimensions
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 3;
        const barWidth = chartWidth / labels.length * 0.8;
        const barSpacing = chartWidth / labels.length * 0.2;

        // Find max value
        const maxValue = Math.max(...datasets[0].data);

        // Draw bars
        labels.forEach((label, index) => {
            const value = datasets[0].data[index];
            const barHeight = (value / maxValue) * chartHeight;
            const x = padding + index * (barWidth + barSpacing);
            const y = height - padding * 2 - barHeight;

            // Draw bar
            ctx.fillStyle = config.colors[index % config.colors.length];
            ctx.fillRect(x, y, barWidth, barHeight);

            // Draw label
            ctx.fillStyle = '#6B7280';
            ctx.font = '12px Inter';
            ctx.textAlign = 'center';
            ctx.fillText(label, x + barWidth / 2, height - padding);

            // Draw value
            ctx.fillStyle = '#111827';
            ctx.font = '600 14px Inter';
            ctx.fillText(value.toFixed(0), x + barWidth / 2, y - 5);
        });
    }

    /**
     * Draw line chart
     */
    drawLineChart(config) {
        const { width, height } = this.canvas;
        const ctx = this.ctx;
        const padding = config.padding;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Get data
        const labels = config.labels;
        const datasets = config.datasets;

        if (!labels.length || !datasets.length) return;

        // Calculate dimensions
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 3;
        const pointSpacing = chartWidth / (labels.length - 1);

        // Find max value
        const allValues = datasets.flatMap(d => d.data);
        const maxValue = Math.max(...allValues);
        const minValue = Math.min(...allValues);
        const valueRange = maxValue - minValue;

        // Draw each dataset
        datasets.forEach((dataset, datasetIndex) => {
            const color = dataset.color || config.colors[datasetIndex % config.colors.length];

            // Draw line
            ctx.beginPath();
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;

            dataset.data.forEach((value, index) => {
                const x = padding + index * pointSpacing;
                const y = height - padding * 2 - ((value - minValue) / valueRange) * chartHeight;

                if (index === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });

            ctx.stroke();

            // Draw points
            dataset.data.forEach((value, index) => {
                const x = padding + index * pointSpacing;
                const y = height - padding * 2 - ((value - minValue) / valueRange) * chartHeight;

                ctx.beginPath();
                ctx.fillStyle = color;
                ctx.arc(x, y, 4, 0, Math.PI * 2);
                ctx.fill();
            });
        });

        // Draw labels
        labels.forEach((label, index) => {
            const x = padding + index * pointSpacing;
            ctx.fillStyle = '#6B7280';
            ctx.font = '12px Inter';
            ctx.textAlign = 'center';
            ctx.fillText(label, x, height - padding);
        });
    }

    /**
     * Draw pie chart
     */
    drawPieChart(config) {
        const { width, height } = this.canvas;
        const ctx = this.ctx;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Get data
        const labels = config.labels;
        const values = config.values;
        const colors = config.colors;

        if (!labels.length || !values.length) return;

        // Calculate center and radius
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) / 2 - 40;

        // Calculate total
        const total = values.reduce((sum, v) => sum + v, 0);

        // Draw slices
        let currentAngle = -Math.PI / 2; // Start from top

        values.forEach((value, index) => {
            const sliceAngle = (value / total) * Math.PI * 2;

            // Draw slice
            ctx.beginPath();
            ctx.fillStyle = colors[index % colors.length];
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
            ctx.closePath();
            ctx.fill();

            // Draw label
            const labelAngle = currentAngle + sliceAngle / 2;
            const labelX = centerX + Math.cos(labelAngle) * (radius + 25);
            const labelY = centerY + Math.sin(labelAngle) * (radius + 25);

            ctx.fillStyle = '#111827';
            ctx.font = '12px Inter';
            ctx.textAlign = labelX > centerX ? 'left' : 'right';
            ctx.fillText(`${labels[index]} (${((value / total) * 100).toFixed(1)}%)`, labelX, labelY);

            currentAngle += sliceAngle;
        });
    }

    /**
     * Update chart data
     */
    update(data) {
        this.data = data;
        if (this.chart) {
            // Redraw based on chart type
            if (this.chart.type === 'bar') {
                this.createBarChart(data);
            } else if (this.chart.type === 'line') {
                this.createLineChart(data);
            } else if (this.chart.type === 'pie') {
                this.createPieChart(data);
            }
        }
    }

    /**
     * Clear chart
     */
    clear() {
        const { width, height } = this.canvas;
        this.ctx.clearRect(0, 0, width, height);
        this.data = null;
        this.chart = null;
    }

    /**
     * Export chart as image
     */
    exportImage(filename = 'chart.png') {
        const link = document.createElement('a');
        link.download = filename;
        link.href = this.canvas.toDataURL();
        link.click();
    }
}

/**
 * Statistics Calculator
 * Calculate statistics from receipt data
 */
class StatisticsCalculator {
    /**
     * Calculate total spending
     */
    static calculateTotal(receipts) {
        return receipts.reduce((sum, receipt) => {
            const amount = parseFloat(receipt.total || 0);
            return sum + amount;
        }, 0);
    }

    /**
     * Calculate average spending
     */
    static calculateAverage(receipts) {
        if (receipts.length === 0) return 0;
        return this.calculateTotal(receipts) / receipts.length;
    }

    /**
     * Group by merchant
     */
    static groupByMerchant(receipts) {
        const groups = {};
        
        receipts.forEach(receipt => {
            const merchant = receipt.merchant || 'Unknown';
            if (!groups[merchant]) {
                groups[merchant] = {
                    count: 0,
                    total: 0,
                    receipts: []
                };
            }
            
            groups[merchant].count++;
            groups[merchant].total += parseFloat(receipt.total || 0);
            groups[merchant].receipts.push(receipt);
        });

        return groups;
    }

    /**
     * Group by date
     */
    static groupByDate(receipts, interval = 'day') {
        const groups = {};
        
        receipts.forEach(receipt => {
            if (!receipt.date) return;
            
            const date = new Date(receipt.date);
            let key;

            if (interval === 'day') {
                key = date.toISOString().split('T')[0];
            } else if (interval === 'week') {
                const weekStart = new Date(date);
                weekStart.setDate(date.getDate() - date.getDay());
                key = weekStart.toISOString().split('T')[0];
            } else if (interval === 'month') {
                key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            } else if (interval === 'year') {
                key = String(date.getFullYear());
            }

            if (!groups[key]) {
                groups[key] = {
                    count: 0,
                    total: 0,
                    receipts: []
                };
            }

            groups[key].count++;
            groups[key].total += parseFloat(receipt.total || 0);
            groups[key].receipts.push(receipt);
        });

        return groups;
    }

    /**
     * Get top merchants
     */
    static getTopMerchants(receipts, limit = 10) {
        const groups = this.groupByMerchant(receipts);
        
        return Object.entries(groups)
            .map(([merchant, data]) => ({
                merchant,
                ...data
            }))
            .sort((a, b) => b.total - a.total)
            .slice(0, limit);
    }

    /**
     * Get spending trend
     */
    static getSpendingTrend(receipts, interval = 'month') {
        const groups = this.groupByDate(receipts, interval);
        
        return Object.entries(groups)
            .map(([date, data]) => ({
                date,
                ...data
            }))
            .sort((a, b) => a.date.localeCompare(b.date));
    }

    /**
     * Calculate statistics summary
     */
    static calculateSummary(receipts) {
        const total = this.calculateTotal(receipts);
        const average = this.calculateAverage(receipts);
        const count = receipts.length;

        // Find min and max
        const amounts = receipts.map(r => parseFloat(r.total || 0));
        const min = Math.min(...amounts);
        const max = Math.max(...amounts);

        // Calculate median
        const sorted = [...amounts].sort((a, b) => a - b);
        const median = sorted.length % 2 === 0
            ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
            : sorted[Math.floor(sorted.length / 2)];

        return {
            total,
            average,
            median,
            min,
            max,
            count
        };
    }

    /**
     * Get date range
     */
    static getDateRange(receipts) {
        const dates = receipts
            .filter(r => r.date)
            .map(r => new Date(r.date).getTime());

        if (dates.length === 0) {
            return { earliest: null, latest: null };
        }

        return {
            earliest: new Date(Math.min(...dates)),
            latest: new Date(Math.max(...dates))
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChartBuilder, StatisticsCalculator };
}

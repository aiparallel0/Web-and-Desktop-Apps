/**
 * Canvas Overlay for Bounding Box Preview
 * Draws detection regions and bounding boxes on receipt images
 */

class CanvasOverlay {
    constructor(imageElement) {
        this.imageElement = imageElement;
        this.canvas = null;
        this.ctx = null;
        this.regions = [];
        this.isDrawing = false;
        this.currentRegion = null;
        this.onRegionAdded = null;
        
        this.init();
    }

    init() {
        // Create canvas overlay
        this.canvas = document.createElement('canvas');
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '10';
        
        // Get 2D context
        this.ctx = this.canvas.getContext('2d');
        
        // Set canvas size to match image
        this.updateCanvasSize();
        
        // Insert canvas after image
        if (this.imageElement.parentNode) {
            this.imageElement.parentNode.style.position = 'relative';
            this.imageElement.parentNode.insertBefore(this.canvas, this.imageElement.nextSibling);
        }
    }

    updateCanvasSize() {
        if (!this.imageElement) return;
        
        const rect = this.imageElement.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
        this.canvas.style.width = `${rect.width}px`;
        this.canvas.style.height = `${rect.height}px`;
        
        // Redraw regions after resize
        this.draw();
    }

    enableManualSelection() {
        this.canvas.style.pointerEvents = 'auto';
        this.canvas.style.cursor = 'crosshair';
        
        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // Touch support
        this.canvas.addEventListener('touchstart', this.handleTouchStart.bind(this));
        this.canvas.addEventListener('touchmove', this.handleTouchMove.bind(this));
        this.canvas.addEventListener('touchend', this.handleTouchEnd.bind(this));
    }

    disableManualSelection() {
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.cursor = 'default';
    }

    handleMouseDown(e) {
        this.isDrawing = true;
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        this.currentRegion = {
            startX: x,
            startY: y,
            endX: x,
            endY: y
        };
    }

    handleMouseMove(e) {
        if (!this.isDrawing) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        this.currentRegion.endX = x;
        this.currentRegion.endY = y;
        
        // Redraw with current region
        this.draw();
    }

    handleMouseUp(e) {
        if (!this.isDrawing) return;
        
        this.isDrawing = false;
        
        // Only add region if it has size
        const width = Math.abs(this.currentRegion.endX - this.currentRegion.startX);
        const height = Math.abs(this.currentRegion.endY - this.currentRegion.startY);
        
        if (width > 10 && height > 10) {
            // Normalize region coordinates
            const region = {
                x: Math.min(this.currentRegion.startX, this.currentRegion.endX),
                y: Math.min(this.currentRegion.startY, this.currentRegion.endY),
                width: width,
                height: height
            };
            
            this.addRegion(region);
            
            if (this.onRegionAdded) {
                this.onRegionAdded(region);
            }
        }
        
        this.currentRegion = null;
        this.draw();
    }

    handleTouchStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousedown', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        this.handleMouseDown(mouseEvent);
    }

    handleTouchMove(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousemove', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        this.handleMouseMove(mouseEvent);
    }

    handleTouchEnd(e) {
        e.preventDefault();
        const mouseEvent = new MouseEvent('mouseup', {});
        this.handleMouseUp(mouseEvent);
    }

    addRegion(region) {
        this.regions.push(region);
        this.draw();
    }

    clearRegions() {
        this.regions = [];
        this.draw();
    }

    setRegions(regions) {
        this.regions = regions || [];
        this.draw();
    }

    draw() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw saved regions
        this.regions.forEach((region, index) => {
            this.drawRegion(region, index + 1);
        });
        
        // Draw current region being drawn
        if (this.isDrawing && this.currentRegion) {
            this.drawCurrentRegion();
        }
    }

    drawRegion(region, label) {
        const { x, y, width, height } = region;
        
        // Draw rectangle
        this.ctx.strokeStyle = '#2563eb';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(x, y, width, height);
        
        // Draw semi-transparent fill
        this.ctx.fillStyle = 'rgba(37, 99, 235, 0.1)';
        this.ctx.fillRect(x, y, width, height);
        
        // Draw label
        this.ctx.fillStyle = '#2563eb';
        this.ctx.font = 'bold 14px Inter, sans-serif';
        
        const labelText = `Region ${label}`;
        const labelWidth = this.ctx.measureText(labelText).width;
        const labelPadding = 6;
        
        // Draw label background
        this.ctx.fillStyle = '#2563eb';
        this.ctx.fillRect(x, y - 24, labelWidth + labelPadding * 2, 20);
        
        // Draw label text
        this.ctx.fillStyle = 'white';
        this.ctx.fillText(labelText, x + labelPadding, y - 8);
    }

    drawCurrentRegion() {
        const { startX, startY, endX, endY } = this.currentRegion;
        const x = Math.min(startX, endX);
        const y = Math.min(startY, endY);
        const width = Math.abs(endX - startX);
        const height = Math.abs(endY - startY);
        
        // Draw dashed rectangle
        this.ctx.strokeStyle = '#10b981';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        this.ctx.strokeRect(x, y, width, height);
        this.ctx.setLineDash([]);
        
        // Draw semi-transparent fill
        this.ctx.fillStyle = 'rgba(16, 185, 129, 0.15)';
        this.ctx.fillRect(x, y, width, height);
    }

    drawDetectionResults(detections) {
        // Clear existing regions
        this.regions = [];
        
        // Convert detection results to regions
        if (detections && detections.length > 0) {
            detections.forEach(detection => {
                if (detection.bbox) {
                    const [x, y, w, h] = detection.bbox;
                    this.regions.push({
                        x: x * this.canvas.width,
                        y: y * this.canvas.height,
                        width: w * this.canvas.width,
                        height: h * this.canvas.height,
                        text: detection.text,
                        confidence: detection.confidence
                    });
                }
            });
        }
        
        this.draw();
    }

    show() {
        if (this.canvas) {
            this.canvas.style.display = 'block';
        }
    }

    hide() {
        if (this.canvas) {
            this.canvas.style.display = 'none';
        }
    }

    destroy() {
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
        this.canvas = null;
        this.ctx = null;
        this.regions = [];
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CanvasOverlay;
}

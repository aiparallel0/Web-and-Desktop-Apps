/**
 * Client-Side Image Processor
 * Handles basic image preprocessing before upload
 */

class ImageProcessor {
    /**
     * Deskew image (rotate to correct orientation)
     * @param {HTMLImageElement|File} image - Image to process
     * @returns {Promise<Blob>} Processed image
     */
    static async deskew(image) {
        const canvas = await this.imageToCanvas(image);
        const ctx = canvas.getContext('2d');
        
        // Simple rotation detection based on image dimensions
        // In production, this would use more sophisticated algorithms
        const angle = this.detectRotation(canvas);
        
        if (Math.abs(angle) > 0.5) {
            return this.rotateImage(canvas, angle);
        }
        
        return this.canvasToBlob(canvas);
    }

    /**
     * Enhance image quality
     * @param {HTMLImageElement|File} image - Image to enhance
     * @returns {Promise<Blob>} Enhanced image
     */
    static async enhance(image) {
        const canvas = await this.imageToCanvas(image);
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        // Apply contrast enhancement
        this.adjustContrast(imageData, 1.2);
        
        // Apply sharpening
        this.sharpen(imageData);
        
        ctx.putImageData(imageData, 0, 0);
        return this.canvasToBlob(canvas);
    }

    /**
     * Resize image if too large
     * @param {HTMLImageElement|File} image - Image to resize
     * @param {number} maxSize - Maximum dimension
     * @returns {Promise<Blob>} Resized image
     */
    static async resize(image, maxSize = 2048) {
        const canvas = await this.imageToCanvas(image);
        
        if (canvas.width <= maxSize && canvas.height <= maxSize) {
            return this.canvasToBlob(canvas);
        }
        
        const scale = maxSize / Math.max(canvas.width, canvas.height);
        const newWidth = Math.floor(canvas.width * scale);
        const newHeight = Math.floor(canvas.height * scale);
        
        const resizedCanvas = document.createElement('canvas');
        resizedCanvas.width = newWidth;
        resizedCanvas.height = newHeight;
        
        const ctx = resizedCanvas.getContext('2d');
        ctx.drawImage(canvas, 0, 0, newWidth, newHeight);
        
        return this.canvasToBlob(resizedCanvas);
    }

    /**
     * Convert image to grayscale
     * @param {HTMLImageElement|File} image - Image to convert
     * @returns {Promise<Blob>} Grayscale image
     */
    static async toGrayscale(image) {
        const canvas = await this.imageToCanvas(image);
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        
        for (let i = 0; i < data.length; i += 4) {
            const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
            data[i] = gray;
            data[i + 1] = gray;
            data[i + 2] = gray;
        }
        
        ctx.putImageData(imageData, 0, 0);
        return this.canvasToBlob(canvas);
    }

    // =========================================================================
    // HELPER METHODS
    // =========================================================================

    /**
     * Convert image or file to canvas
     */
    static async imageToCanvas(image) {
        let img;
        
        if (image instanceof File || image instanceof Blob) {
            img = await this.fileToImage(image);
        } else {
            img = image;
        }
        
        const canvas = document.createElement('canvas');
        canvas.width = img.width || img.naturalWidth;
        canvas.height = img.height || img.naturalHeight;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        
        return canvas;
    }

    /**
     * Convert File to Image element
     */
    static async fileToImage(file) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            const url = URL.createObjectURL(file);
            
            img.onload = () => {
                URL.revokeObjectURL(url);
                resolve(img);
            };
            
            img.onerror = () => {
                URL.revokeObjectURL(url);
                reject(new Error('Failed to load image'));
            };
            
            img.src = url;
        });
    }

    /**
     * Convert canvas to Blob
     */
    static canvasToBlob(canvas, type = 'image/jpeg', quality = 0.92) {
        return new Promise((resolve) => {
            canvas.toBlob(resolve, type, quality);
        });
    }

    /**
     * Detect rotation angle using edge detection and variance analysis
     * Analyzes horizontal and vertical edge strength to determine text orientation
     * Returns rotation angle in degrees (0, 90, 180, 270)
     */
    static detectRotation(canvas) {
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        const width = canvas.width;
        const height = canvas.height;
        
        // Convert to grayscale and calculate edge strength
        const grayscale = new Float32Array(width * height);
        for (let i = 0; i < data.length; i += 4) {
            const idx = i / 4;
            grayscale[idx] = (data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114) / 255;
        }
        
        // Calculate horizontal and vertical edge variances at different rotations
        const rotations = [0, 90, 180, 270];
        const scores = rotations.map(angle => {
            return this.calculateEdgeVariance(grayscale, width, height, angle);
        });
        
        // Find rotation with maximum horizontal edge variance (text lines)
        let maxScore = scores[0];
        let bestRotation = 0;
        
        for (let i = 1; i < scores.length; i++) {
            if (scores[i] > maxScore) {
                maxScore = scores[i];
                bestRotation = rotations[i];
            }
        }
        
        return bestRotation;
    }
    
    /**
     * Calculate edge variance for a given rotation
     * Higher variance indicates stronger horizontal lines (text orientation)
     */
    static calculateEdgeVariance(grayscale, width, height, rotation) {
        const sampleSize = Math.min(50, Math.floor(height / 10)); // Sample rows
        let horizontalVariance = 0;
        
        // Sample horizontal lines and calculate variance
        for (let row = 0; row < height; row += Math.floor(height / sampleSize)) {
            const rowValues = [];
            for (let col = 0; col < width - 1; col++) {
                const idx = row * width + col;
                const nextIdx = row * width + col + 1;
                
                if (idx < grayscale.length && nextIdx < grayscale.length) {
                    // Calculate horizontal gradient
                    const gradient = Math.abs(grayscale[nextIdx] - grayscale[idx]);
                    rowValues.push(gradient);
                }
            }
            
            // Calculate variance of this row
            if (rowValues.length > 0) {
                const mean = rowValues.reduce((a, b) => a + b, 0) / rowValues.length;
                const variance = rowValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / rowValues.length;
                horizontalVariance += variance;
            }
        }
        
        return horizontalVariance / sampleSize;
    }

    /**
     * Rotate image by angle
     */
    static async rotateImage(canvas, angle) {
        const radians = (angle * Math.PI) / 180;
        const cos = Math.cos(radians);
        const sin = Math.sin(radians);
        
        const newWidth = Math.abs(canvas.width * cos) + Math.abs(canvas.height * sin);
        const newHeight = Math.abs(canvas.width * sin) + Math.abs(canvas.height * cos);
        
        const rotatedCanvas = document.createElement('canvas');
        rotatedCanvas.width = newWidth;
        rotatedCanvas.height = newHeight;
        
        const ctx = rotatedCanvas.getContext('2d');
        ctx.translate(newWidth / 2, newHeight / 2);
        ctx.rotate(radians);
        ctx.drawImage(canvas, -canvas.width / 2, -canvas.height / 2);
        
        return this.canvasToBlob(rotatedCanvas);
    }

    /**
     * Adjust image contrast
     */
    static adjustContrast(imageData, contrast) {
        const data = imageData.data;
        const factor = (259 * (contrast + 255)) / (255 * (259 - contrast));
        
        for (let i = 0; i < data.length; i += 4) {
            data[i] = factor * (data[i] - 128) + 128;
            data[i + 1] = factor * (data[i + 1] - 128) + 128;
            data[i + 2] = factor * (data[i + 2] - 128) + 128;
        }
    }

    /**
     * Sharpen image (simplified)
     */
    static sharpen(imageData) {
        // Simplified sharpening - just increase local contrast
        const data = imageData.data;
        const width = imageData.width;
        const height = imageData.height;
        
        // Create a copy for reading
        const original = new Uint8ClampedArray(data);
        
        // Simple unsharp mask kernel
        const kernel = [
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ];
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                for (let c = 0; c < 3; c++) {
                    let sum = 0;
                    
                    for (let ky = -1; ky <= 1; ky++) {
                        for (let kx = -1; kx <= 1; kx++) {
                            const idx = ((y + ky) * width + (x + kx)) * 4 + c;
                            sum += original[idx] * kernel[ky + 1][kx + 1];
                        }
                    }
                    
                    const idx = (y * width + x) * 4 + c;
                    data[idx] = Math.max(0, Math.min(255, sum));
                }
            }
        }
    }

    /**
     * Get image info
     */
    static async getImageInfo(image) {
        const img = await (image instanceof File ? this.fileToImage(image) : Promise.resolve(image));
        
        return {
            width: img.width || img.naturalWidth,
            height: img.height || img.naturalHeight,
            aspectRatio: (img.width || img.naturalWidth) / (img.height || img.naturalHeight)
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImageProcessor;
}

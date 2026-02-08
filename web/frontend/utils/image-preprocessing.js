/**
 * Image Preprocessing Utilities
 * Client-side image enhancement, deskew detection, and optimization
 * Uses Canvas API for real-time processing
 */

class ImagePreprocessor {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.originalImage = null;
    }

    /**
     * Initialize canvas with image
     */
    async loadImage(imageSource) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            
            img.onload = () => {
                this.originalImage = img;
                this.canvas = document.createElement('canvas');
                this.canvas.width = img.width;
                this.canvas.height = img.height;
                this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
                this.ctx.drawImage(img, 0, 0);
                resolve(img);
            };
            
            img.onerror = (err) => {
                reject(new Error('Failed to load image'));
            };
            
            if (typeof imageSource === 'string') {
                img.src = imageSource;
            } else if (imageSource instanceof File) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    img.src = e.target.result;
                };
                reader.onerror = reject;
                reader.readAsDataURL(imageSource);
            } else if (imageSource instanceof Blob) {
                img.src = URL.createObjectURL(imageSource);
            } else {
                reject(new Error('Invalid image source'));
            }
        });
    }

    /**
     * Detect image skew angle using Hough transform approximation
     */
    detectSkewAngle() {
        if (!this.ctx || !this.canvas) {
            return 0;
        }

        try {
            const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
            const data = imageData.data;
            
            // Convert to grayscale and apply edge detection
            const edges = this.detectEdges(imageData);
            
            // Sample angles from -15 to 15 degrees
            const angles = [];
            const angleStep = 0.5;
            
            for (let angle = -15; angle <= 15; angle += angleStep) {
                const score = this.calculateHoughScore(edges, angle);
                angles.push({ angle, score });
            }
            
            // Find angle with highest score
            angles.sort((a, b) => b.score - a.score);
            
            return angles[0].angle;
        } catch (error) {
            console.error('Skew detection error:', error);
            return 0;
        }
    }

    /**
     * Simple edge detection using Sobel operator
     */
    detectEdges(imageData) {
        const width = imageData.width;
        const height = imageData.height;
        const data = imageData.data;
        const edges = new Float32Array(width * height);
        
        // Sobel kernels
        const sobelX = [-1, 0, 1, -2, 0, 2, -1, 0, 1];
        const sobelY = [-1, -2, -1, 0, 0, 0, 1, 2, 1];
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                let gx = 0;
                let gy = 0;
                
                for (let ky = -1; ky <= 1; ky++) {
                    for (let kx = -1; kx <= 1; kx++) {
                        const idx = ((y + ky) * width + (x + kx)) * 4;
                        const gray = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
                        const kernelIdx = (ky + 1) * 3 + (kx + 1);
                        
                        gx += gray * sobelX[kernelIdx];
                        gy += gray * sobelY[kernelIdx];
                    }
                }
                
                edges[y * width + x] = Math.sqrt(gx * gx + gy * gy);
            }
        }
        
        return edges;
    }

    /**
     * Calculate Hough transform score for a given angle
     */
    calculateHoughScore(edges, angle) {
        const width = this.canvas.width;
        const height = this.canvas.height;
        const radians = (angle * Math.PI) / 180;
        const cos = Math.cos(radians);
        const sin = Math.sin(radians);
        
        const accumulator = new Map();
        let score = 0;
        
        // Sample points for performance
        const step = 5;
        
        for (let y = 0; y < height; y += step) {
            for (let x = 0; x < width; x += step) {
                const edgeValue = edges[y * width + x];
                
                if (edgeValue > 50) { // Threshold for edge detection
                    const rho = Math.round(x * cos + y * sin);
                    const key = rho;
                    accumulator.set(key, (accumulator.get(key) || 0) + edgeValue);
                }
            }
        }
        
        // Sum of top scores
        const scores = Array.from(accumulator.values()).sort((a, b) => b - a);
        score = scores.slice(0, 10).reduce((sum, val) => sum + val, 0);
        
        return score;
    }

    /**
     * Rotate image by given angle
     */
    rotateImage(angle) {
        if (Math.abs(angle) < 0.1 || !this.canvas || !this.originalImage) {
            return this.canvas;
        }

        const radians = (angle * Math.PI) / 180;
        const cos = Math.cos(radians);
        const sin = Math.sin(radians);
        
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        // Calculate new dimensions
        const newWidth = Math.abs(width * cos) + Math.abs(height * sin);
        const newHeight = Math.abs(width * sin) + Math.abs(height * cos);
        
        const rotatedCanvas = document.createElement('canvas');
        rotatedCanvas.width = newWidth;
        rotatedCanvas.height = newHeight;
        const rotatedCtx = rotatedCanvas.getContext('2d');
        
        // Fill with white background
        rotatedCtx.fillStyle = '#FFFFFF';
        rotatedCtx.fillRect(0, 0, newWidth, newHeight);
        
        // Rotate and draw
        rotatedCtx.translate(newWidth / 2, newHeight / 2);
        rotatedCtx.rotate(radians);
        rotatedCtx.drawImage(this.canvas, -width / 2, -height / 2);
        
        return rotatedCanvas;
    }

    /**
     * Deskew image automatically
     */
    async deskew() {
        const angle = this.detectSkewAngle();
        console.log('Detected skew angle:', angle);
        
        if (Math.abs(angle) > 0.5) {
            const rotated = this.rotateImage(-angle);
            this.canvas = rotated;
            this.ctx = rotated.getContext('2d', { willReadFrequently: true });
            return angle;
        }
        
        return 0;
    }

    /**
     * Enhance image for better OCR
     */
    enhanceImage(options = {}) {
        if (!this.ctx || !this.canvas) {
            return;
        }

        const {
            brightness = 1.1,
            contrast = 1.2,
            sharpen = true,
            denoise = false,
            binarize = false,
            threshold = 128
        } = options;

        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        const data = imageData.data;

        // Apply brightness and contrast
        for (let i = 0; i < data.length; i += 4) {
            // Get RGB values
            let r = data[i];
            let g = data[i + 1];
            let b = data[i + 2];

            // Apply brightness
            r *= brightness;
            g *= brightness;
            b *= brightness;

            // Apply contrast
            r = ((r - 128) * contrast) + 128;
            g = ((g - 128) * contrast) + 128;
            b = ((b - 128) * contrast) + 128;

            // Clamp values
            data[i] = Math.min(255, Math.max(0, r));
            data[i + 1] = Math.min(255, Math.max(0, g));
            data[i + 2] = Math.min(255, Math.max(0, b));
        }

        // Apply binarization if requested
        if (binarize) {
            for (let i = 0; i < data.length; i += 4) {
                const gray = (data[i] + data[i + 1] + data[i + 2]) / 3;
                const value = gray > threshold ? 255 : 0;
                data[i] = data[i + 1] = data[i + 2] = value;
            }
        }

        this.ctx.putImageData(imageData, 0, 0);

        // Apply sharpening if requested
        if (sharpen) {
            this.sharpenImage();
        }

        // Apply denoising if requested
        if (denoise) {
            this.denoiseImage();
        }
    }

    /**
     * Sharpen image using convolution
     */
    sharpenImage() {
        if (!this.ctx || !this.canvas) {
            return;
        }

        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        const data = imageData.data;
        const width = this.canvas.width;
        const height = this.canvas.height;

        // Sharpening kernel
        const kernel = [
            0, -1, 0,
            -1, 5, -1,
            0, -1, 0
        ];

        const output = new Uint8ClampedArray(data);

        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                for (let c = 0; c < 3; c++) { // RGB channels
                    let sum = 0;
                    
                    for (let ky = -1; ky <= 1; ky++) {
                        for (let kx = -1; kx <= 1; kx++) {
                            const idx = ((y + ky) * width + (x + kx)) * 4 + c;
                            const kernelIdx = (ky + 1) * 3 + (kx + 1);
                            sum += data[idx] * kernel[kernelIdx];
                        }
                    }
                    
                    const outputIdx = (y * width + x) * 4 + c;
                    output[outputIdx] = Math.min(255, Math.max(0, sum));
                }
            }
        }

        // Copy output back to imageData
        for (let i = 0; i < data.length; i += 4) {
            data[i] = output[i];
            data[i + 1] = output[i + 1];
            data[i + 2] = output[i + 2];
        }

        this.ctx.putImageData(imageData, 0, 0);
    }

    /**
     * Denoise image using median filter
     */
    denoiseImage() {
        if (!this.ctx || !this.canvas) {
            return;
        }

        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        const data = imageData.data;
        const width = this.canvas.width;
        const height = this.canvas.height;

        const output = new Uint8ClampedArray(data);
        const windowSize = 1; // 3x3 window

        for (let y = windowSize; y < height - windowSize; y++) {
            for (let x = windowSize; x < width - windowSize; x++) {
                for (let c = 0; c < 3; c++) { // RGB channels
                    const values = [];
                    
                    for (let ky = -windowSize; ky <= windowSize; ky++) {
                        for (let kx = -windowSize; kx <= windowSize; kx++) {
                            const idx = ((y + ky) * width + (x + kx)) * 4 + c;
                            values.push(data[idx]);
                        }
                    }
                    
                    values.sort((a, b) => a - b);
                    const median = values[Math.floor(values.length / 2)];
                    
                    const outputIdx = (y * width + x) * 4 + c;
                    output[outputIdx] = median;
                }
            }
        }

        // Copy output back to imageData
        for (let i = 0; i < data.length; i += 4) {
            data[i] = output[i];
            data[i + 1] = output[i + 1];
            data[i + 2] = output[i + 2];
        }

        this.ctx.putImageData(imageData, 0, 0);
    }

    /**
     * Convert to grayscale
     */
    toGrayscale() {
        if (!this.ctx || !this.canvas) {
            return;
        }

        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        const data = imageData.data;

        for (let i = 0; i < data.length; i += 4) {
            const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
            data[i] = data[i + 1] = data[i + 2] = gray;
        }

        this.ctx.putImageData(imageData, 0, 0);
    }

    /**
     * Apply adaptive threshold (local binarization)
     */
    adaptiveThreshold(blockSize = 11, constant = 2) {
        if (!this.ctx || !this.canvas) {
            return;
        }

        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        const data = imageData.data;
        const width = this.canvas.width;
        const height = this.canvas.height;

        // Convert to grayscale first
        const gray = new Uint8Array(width * height);
        for (let i = 0; i < data.length; i += 4) {
            const grayValue = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
            gray[i / 4] = grayValue;
        }

        // Calculate integral image for fast local mean calculation
        const integral = this.calculateIntegralImage(gray, width, height);

        const halfBlock = Math.floor(blockSize / 2);

        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const x1 = Math.max(0, x - halfBlock);
                const y1 = Math.max(0, y - halfBlock);
                const x2 = Math.min(width - 1, x + halfBlock);
                const y2 = Math.min(height - 1, y + halfBlock);

                const count = (x2 - x1 + 1) * (y2 - y1 + 1);
                const sum = this.getIntegralSum(integral, x1, y1, x2, y2, width);
                const mean = sum / count;

                const idx = y * width + x;
                const threshold = mean - constant;
                const value = gray[idx] > threshold ? 255 : 0;

                const dataIdx = idx * 4;
                data[dataIdx] = data[dataIdx + 1] = data[dataIdx + 2] = value;
            }
        }

        this.ctx.putImageData(imageData, 0, 0);
    }

    /**
     * Calculate integral image for fast summation
     */
    calculateIntegralImage(gray, width, height) {
        const integral = new Float64Array((width + 1) * (height + 1));

        for (let y = 1; y <= height; y++) {
            let rowSum = 0;
            for (let x = 1; x <= width; x++) {
                const grayIdx = (y - 1) * width + (x - 1);
                rowSum += gray[grayIdx];
                const integralIdx = y * (width + 1) + x;
                integral[integralIdx] = rowSum + integral[(y - 1) * (width + 1) + x];
            }
        }

        return integral;
    }

    /**
     * Get sum of rectangle using integral image
     */
    getIntegralSum(integral, x1, y1, x2, y2, width) {
        const w = width + 1;
        return integral[(y2 + 1) * w + (x2 + 1)]
             - integral[y1 * w + (x2 + 1)]
             - integral[(y2 + 1) * w + x1]
             + integral[y1 * w + x1];
    }

    /**
     * Resize image to fit within max dimensions
     */
    resize(maxWidth, maxHeight) {
        if (!this.canvas) {
            return;
        }

        const width = this.canvas.width;
        const height = this.canvas.height;

        let newWidth = width;
        let newHeight = height;

        if (width > maxWidth) {
            newWidth = maxWidth;
            newHeight = (height * maxWidth) / width;
        }

        if (newHeight > maxHeight) {
            newHeight = maxHeight;
            newWidth = (width * maxHeight) / height;
        }

        if (newWidth !== width || newHeight !== height) {
            const resizedCanvas = document.createElement('canvas');
            resizedCanvas.width = newWidth;
            resizedCanvas.height = newHeight;
            const resizedCtx = resizedCanvas.getContext('2d');
            
            resizedCtx.drawImage(this.canvas, 0, 0, newWidth, newHeight);
            
            this.canvas = resizedCanvas;
            this.ctx = resizedCtx;
        }
    }

    /**
     * Get processed canvas
     */
    getCanvas() {
        return this.canvas;
    }

    /**
     * Get processed image as blob
     */
    async getBlob(type = 'image/png', quality = 0.92) {
        if (!this.canvas) {
            throw new Error('No canvas available');
        }

        return new Promise((resolve, reject) => {
            this.canvas.toBlob((blob) => {
                if (blob) {
                    resolve(blob);
                } else {
                    reject(new Error('Failed to create blob'));
                }
            }, type, quality);
        });
    }

    /**
     * Get processed image as data URL
     */
    getDataURL(type = 'image/png', quality = 0.92) {
        if (!this.canvas) {
            throw new Error('No canvas available');
        }

        return this.canvas.toDataURL(type, quality);
    }

    /**
     * Get processed image as file
     */
    async getFile(filename = 'processed.png', type = 'image/png', quality = 0.92) {
        const blob = await this.getBlob(type, quality);
        return new File([blob], filename, { type });
    }

    /**
     * Process image with all enhancements
     */
    async process(options = {}) {
        const {
            deskew = true,
            enhance = true,
            grayscale = false,
            adaptiveThreshold = false,
            resize = null,
            enhanceOptions = {}
        } = options;

        console.log('Processing image with options:', options);

        // Resize if needed
        if (resize && resize.maxWidth && resize.maxHeight) {
            this.resize(resize.maxWidth, resize.maxHeight);
        }

        // Deskew
        if (deskew) {
            const angle = await this.deskew();
            console.log('Deskewed by angle:', angle);
        }

        // Enhance
        if (enhance) {
            this.enhanceImage(enhanceOptions);
            console.log('Image enhanced');
        }

        // Convert to grayscale
        if (grayscale) {
            this.toGrayscale();
            console.log('Converted to grayscale');
        }

        // Apply adaptive threshold
        if (adaptiveThreshold) {
            this.adaptiveThreshold();
            console.log('Applied adaptive threshold');
        }

        return this.getCanvas();
    }
}

/**
 * Utility functions for quick processing
 */
const ImageProcessingUtils = {
    /**
     * Quick process file with default options
     */
    async processFile(file, options = {}) {
        const processor = new ImagePreprocessor();
        await processor.loadImage(file);
        await processor.process(options);
        return processor.getFile(file.name, file.type);
    },

    /**
     * Detect if image needs deskewing
     */
    async detectSkew(file) {
        const processor = new ImagePreprocessor();
        await processor.loadImage(file);
        return processor.detectSkewAngle();
    },

    /**
     * Create thumbnail
     */
    async createThumbnail(file, maxSize = 200) {
        const processor = new ImagePreprocessor();
        await processor.loadImage(file);
        processor.resize(maxSize, maxSize);
        return processor.getBlob('image/jpeg', 0.8);
    },

    /**
     * Optimize image for upload
     */
    async optimizeForUpload(file, maxSize = 2048) {
        const processor = new ImagePreprocessor();
        await processor.loadImage(file);
        processor.resize(maxSize, maxSize);
        
        // Determine output format
        const outputType = file.type === 'image/png' ? 'image/png' : 'image/jpeg';
        const quality = outputType === 'image/jpeg' ? 0.85 : 0.92;
        
        return processor.getFile(file.name, outputType, quality);
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ImagePreprocessor, ImageProcessingUtils };
}

// Global export
window.ImagePreprocessor = ImagePreprocessor;
window.ImageProcessingUtils = ImageProcessingUtils;

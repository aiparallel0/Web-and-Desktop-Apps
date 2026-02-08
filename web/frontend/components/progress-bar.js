/**
 * Progress Bar Web Component
 * Real-time progress updates with status messages
 */

class ProgressBar extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.progress = 0;
        this.status = 'Initializing...';
    }

    connectedCallback() {
        this.render();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                }

                .progress-container {
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 32px;
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                }

                .progress-header {
                    text-align: center;
                    margin-bottom: 24px;
                }

                .progress-icon {
                    width: 64px;
                    height: 64px;
                    margin: 0 auto 16px;
                    color: #3B82F6;
                    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
                }

                @keyframes pulse {
                    0%, 100% {
                        opacity: 1;
                    }
                    50% {
                        opacity: .5;
                    }
                }

                .progress-title {
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: #111827;
                    margin-bottom: 8px;
                }

                .progress-status {
                    font-size: 1rem;
                    color: #6B7280;
                }

                .progress-bar-wrapper {
                    position: relative;
                    width: 100%;
                    height: 12px;
                    background: #E5E7EB;
                    border-radius: 9999px;
                    overflow: hidden;
                    margin-bottom: 16px;
                }

                .progress-bar-fill {
                    height: 100%;
                    background: #3B82F6;
                    border-radius: 9999px;
                    transition: width 0.3s ease;
                    position: relative;
                    overflow: hidden;
                }

                .progress-bar-fill::after {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255, 255, 255, 0.2);
                    animation: shimmer 2s infinite;
                }

                @keyframes shimmer {
                    0% {
                        transform: translateX(-100%);
                    }
                    100% {
                        transform: translateX(100%);
                    }
                }

                .progress-percentage {
                    text-align: center;
                    font-size: 2rem;
                    font-weight: 700;
                    color: #111827;
                    margin-bottom: 8px;
                }

                .progress-steps {
                    display: flex;
                    justify-content: space-between;
                    margin-top: 24px;
                    gap: 8px;
                }

                .step {
                    flex: 1;
                    text-align: center;
                    padding: 12px 8px;
                    background: #F3F4F6;
                    border-radius: 8px;
                    font-size: 0.875rem;
                    color: #9CA3AF;
                    transition: all 0.3s ease;
                }

                .step.active {
                    background: #DBEAFE;
                    color: #3B82F6;
                    font-weight: 600;
                }

                .step.completed {
                    background: #D1FAE5;
                    color: #10B981;
                }

                .step-icon {
                    display: block;
                    font-size: 1.5rem;
                    margin-bottom: 4px;
                }

                @media (max-width: 640px) {
                    .progress-container {
                        padding: 24px 16px;
                    }

                    .progress-steps {
                        flex-direction: column;
                    }

                    .step {
                        display: flex;
                        align-items: center;
                        gap: 12px;
                        text-align: left;
                    }

                    .step-icon {
                        margin-bottom: 0;
                    }
                }
            </style>

            <div class="progress-container">
                <div class="progress-header">
                    <svg class="progress-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                    </svg>
                    <h2 class="progress-title">Processing Receipt</h2>
                    <p class="progress-status" id="statusText">Initializing...</p>
                </div>

                <div class="progress-percentage" id="percentageText">0%</div>

                <div class="progress-bar-wrapper">
                    <div class="progress-bar-fill" id="progressFill" style="width: 0%"></div>
                </div>

                <div class="progress-steps">
                    <div class="step" id="step1">
                        <span class="step-icon">📤</span>
                        <span>Upload</span>
                    </div>
                    <div class="step" id="step2">
                        <span class="step-icon">🔍</span>
                        <span>Analyze</span>
                    </div>
                    <div class="step" id="step3">
                        <span class="step-icon">🤖</span>
                        <span>Extract</span>
                    </div>
                    <div class="step" id="step4">
                        <span class="step-icon">✅</span>
                        <span>Complete</span>
                    </div>
                </div>
            </div>
        `;
    }

    setProgress(percent, status) {
        this.progress = Math.max(0, Math.min(100, percent));
        this.status = status || this.status;

        const progressFill = this.shadowRoot.getElementById('progressFill');
        const statusText = this.shadowRoot.getElementById('statusText');
        const percentageText = this.shadowRoot.getElementById('percentageText');

        if (progressFill) progressFill.style.width = `${this.progress}%`;
        if (statusText) statusText.textContent = this.status;
        if (percentageText) percentageText.textContent = `${Math.round(this.progress)}%`;

        // Update steps
        this.updateSteps();
    }

    updateSteps() {
        const steps = [
            { id: 'step1', threshold: 0 },
            { id: 'step2', threshold: 25 },
            { id: 'step3', threshold: 50 },
            { id: 'step4', threshold: 90 }
        ];

        steps.forEach(step => {
            const element = this.shadowRoot.getElementById(step.id);
            if (!element) return;

            element.classList.remove('active', 'completed');

            if (this.progress >= step.threshold) {
                if (this.progress > step.threshold + 20 || this.progress === 100) {
                    element.classList.add('completed');
                } else {
                    element.classList.add('active');
                }
            }
        });
    }

    reset() {
        this.setProgress(0, 'Initializing...');
    }
}

customElements.define('progress-bar', ProgressBar);

/**
 * Authentication Handler
 * Manages all authentication workflows including login, register, password reset
 * @version 2.0.0
 */

(function(window) {
    'use strict';

    class AuthHandler {
        constructor() {
            this.isProcessing = false;
            this.passwordStrength = {
                score: 0,
                feedback: ''
            };
            this.init();
        }

        /**
         * Initialize auth handler
         */
        init() {
            // Check if we're on an auth page
            const isLoginPage = window.location.pathname.includes('login');
            const isRegisterPage = window.location.pathname.includes('register');

            if (isLoginPage) {
                this.setupLoginPage();
            } else if (isRegisterPage) {
                this.setupRegisterPage();
            }

            // Check if already authenticated
            this.checkAuthentication();
        }

        /**
         * Setup login page
         */
        setupLoginPage() {
            const form = document.getElementById('loginForm');
            if (!form) return;

            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLogin(form);
            });

            // Add enter key listener
            form.querySelectorAll('input').forEach(input => {
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        this.handleLogin(form);
                    }
                });
            });

            // Show/hide password toggle
            this.setupPasswordToggle();

            // Social login buttons
            this.setupSocialLogin();

            // Remember me checkbox
            this.loadRememberMe();
        }

        /**
         * Setup register page
         */
        setupRegisterPage() {
            const form = document.getElementById('registerForm');
            if (!form) return;

            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleRegister(form);
            });

            // Password strength indicator
            const passwordInput = form.querySelector('input[name="password"]');
            if (passwordInput) {
                passwordInput.addEventListener('input', (e) => {
                    this.updatePasswordStrength(e.target.value);
                });
            }

            // Confirm password validation
            const confirmPasswordInput = form.querySelector('input[name="confirmPassword"]');
            const passwordField = form.querySelector('input[name="password"]');
            if (confirmPasswordInput && passwordField) {
                confirmPasswordInput.addEventListener('input', () => {
                    this.validatePasswordMatch(passwordField.value, confirmPasswordInput.value);
                });
            }

            // Show/hide password toggles
            this.setupPasswordToggle();

            // Social signup buttons
            this.setupSocialLogin();

            // Terms and conditions checkbox
            this.setupTermsCheckbox();
        }

        /**
         * Handle login
         */
        async handleLogin(form) {
            if (this.isProcessing) return;

            const formData = new FormData(form);
            const email = formData.get('email');
            const password = formData.get('password');
            const rememberMe = formData.get('rememberMe') === 'on';

            // Validate inputs
            if (!this.validateEmail(email)) {
                this.showError('Please enter a valid email address');
                return;
            }

            if (!password || password.length < 6) {
                this.showError('Password must be at least 6 characters');
                return;
            }

            this.isProcessing = true;
            this.showLoading(true);

            try {
                // Call API
                const response = await this.loginAPI(email, password, rememberMe);

                if (response.success) {
                    // Save tokens
                    localStorage.setItem('access_token', response.access_token);
                    localStorage.setItem('user_data', JSON.stringify(response.user));
                    
                    if (response.refresh_token) {
                        localStorage.setItem('refresh_token', response.refresh_token);
                    }

                    // Save remember me preference
                    if (rememberMe) {
                        localStorage.setItem('remember_email', email);
                    } else {
                        localStorage.removeItem('remember_email');
                    }

                    // Show success and redirect
                    this.showSuccess('Login successful! Redirecting...');
                    
                    setTimeout(() => {
                        window.location.href = 'dashboard.html';
                    }, 1000);
                } else {
                    this.showError(response.message || 'Login failed. Please check your credentials.');
                }
            } catch (error) {
                console.error('Login error:', error);
                this.showError('An error occurred during login. Please try again.');
            } finally {
                this.isProcessing = false;
                this.showLoading(false);
            }
        }

        /**
         * Handle registration
         */
        async handleRegister(form) {
            if (this.isProcessing) return;

            const formData = new FormData(form);
            const name = formData.get('name');
            const email = formData.get('email');
            const password = formData.get('password');
            const confirmPassword = formData.get('confirmPassword');
            const agreeToTerms = formData.get('terms') === 'on';

            // Validate inputs
            if (!name || name.trim().length < 2) {
                this.showError('Please enter your full name');
                return;
            }

            if (!this.validateEmail(email)) {
                this.showError('Please enter a valid email address');
                return;
            }

            if (!password || password.length < 8) {
                this.showError('Password must be at least 8 characters');
                return;
            }

            if (password !== confirmPassword) {
                this.showError('Passwords do not match');
                return;
            }

            if (!agreeToTerms) {
                this.showError('You must agree to the Terms of Service and Privacy Policy');
                return;
            }

            // Check password strength
            if (this.passwordStrength.score < 3) {
                this.showError('Please choose a stronger password');
                return;
            }

            this.isProcessing = true;
            this.showLoading(true);

            try {
                // Call API
                const response = await this.registerAPI({
                    name,
                    email,
                    password
                });

                if (response.success) {
                    // Save tokens
                    localStorage.setItem('access_token', response.access_token);
                    localStorage.setItem('user_data', JSON.stringify(response.user));
                    
                    if (response.refresh_token) {
                        localStorage.setItem('refresh_token', response.refresh_token);
                    }

                    // Show success and redirect
                    this.showSuccess('Registration successful! Redirecting to dashboard...');
                    
                    setTimeout(() => {
                        window.location.href = 'dashboard.html';
                    }, 1500);
                } else {
                    this.showError(response.message || 'Registration failed. Please try again.');
                }
            } catch (error) {
                console.error('Registration error:', error);
                this.showError('An error occurred during registration. Please try again.');
            } finally {
                this.isProcessing = false;
                this.showLoading(false);
            }
        }

        /**
         * Login API call
         */
        async loginAPI(email, password, rememberMe) {
            // For demo purposes, simulate API call
            // In production, replace with actual API endpoint
            
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Simulate successful login
                    if (email && password) {
                        resolve({
                            success: true,
                            access_token: 'demo_token_' + Date.now(),
                            refresh_token: 'demo_refresh_' + Date.now(),
                            user: {
                                id: 'user_' + Date.now(),
                                name: email.split('@')[0],
                                email: email,
                                plan: 'free',
                                avatar: null
                            }
                        });
                    } else {
                        resolve({
                            success: false,
                            message: 'Invalid credentials'
                        });
                    }
                }, 1000);
            });

            // Actual implementation would look like:
            /*
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password, remember_me: rememberMe })
            });
            return await response.json();
            */
        }

        /**
         * Register API call
         */
        async registerAPI(userData) {
            // For demo purposes, simulate API call
            // In production, replace with actual API endpoint
            
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Simulate successful registration
                    resolve({
                        success: true,
                        access_token: 'demo_token_' + Date.now(),
                        refresh_token: 'demo_refresh_' + Date.now(),
                        user: {
                            id: 'user_' + Date.now(),
                            name: userData.name,
                            email: userData.email,
                            plan: 'free',
                            avatar: null
                        }
                    });
                }, 1000);
            });

            // Actual implementation would look like:
            /*
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });
            return await response.json();
            */
        }

        /**
         * Check if user is authenticated
         */
        checkAuthentication() {
            const token = localStorage.getItem('access_token');
            const userData = localStorage.getItem('user_data');

            if (token && userData) {
                // User is authenticated
                const user = JSON.parse(userData);
                
                // Update UI if on auth pages
                const isAuthPage = window.location.pathname.includes('login') || 
                                  window.location.pathname.includes('register');
                
                if (isAuthPage) {
                    // Redirect to dashboard if already logged in
                    window.location.href = 'dashboard.html';
                }

                return user;
            }

            return null;
        }

        /**
         * Validate email
         */
        validateEmail(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        }

        /**
         * Validate password match
         */
        validatePasswordMatch(password, confirmPassword) {
            const matchIndicator = document.getElementById('passwordMatchIndicator');
            if (!matchIndicator) return;

            if (!confirmPassword) {
                matchIndicator.style.display = 'none';
                return;
            }

            matchIndicator.style.display = 'block';
            
            if (password === confirmPassword) {
                matchIndicator.textContent = '✓ Passwords match';
                matchIndicator.style.color = '#10b981';
            } else {
                matchIndicator.textContent = '✕ Passwords do not match';
                matchIndicator.style.color = '#ef4444';
            }
        }

        /**
         * Update password strength indicator
         */
        updatePasswordStrength(password) {
            const indicator = document.getElementById('passwordStrength');
            const strengthBar = document.getElementById('strengthBar');
            const strengthText = document.getElementById('strengthText');
            
            if (!indicator || !strengthBar || !strengthText) return;

            if (!password) {
                indicator.style.display = 'none';
                return;
            }

            indicator.style.display = 'block';

            // Calculate password strength
            let score = 0;
            let feedback = [];

            // Length check
            if (password.length >= 8) score++;
            if (password.length >= 12) score++;
            else feedback.push('Use at least 12 characters');

            // Complexity checks
            if (/[a-z]/.test(password)) score++;
            else feedback.push('Add lowercase letters');

            if (/[A-Z]/.test(password)) score++;
            else feedback.push('Add uppercase letters');

            if (/[0-9]/.test(password)) score++;
            else feedback.push('Add numbers');

            if (/[^a-zA-Z0-9]/.test(password)) score++;
            else feedback.push('Add special characters');

            // Update strength indicator
            const strengths = [
                { label: 'Very Weak', color: '#ef4444', width: '20%' },
                { label: 'Weak', color: '#f59e0b', width: '40%' },
                { label: 'Fair', color: '#f59e0b', width: '60%' },
                { label: 'Good', color: '#10b981', width: '80%' },
                { label: 'Strong', color: '#10b981', width: '100%' }
            ];

            const strength = strengths[Math.min(score - 1, 4)];
            
            strengthBar.style.width = strength.width;
            strengthBar.style.background = strength.color;
            strengthText.textContent = strength.label;
            strengthText.style.color = strength.color;

            // Store score for validation
            this.passwordStrength = {
                score: score,
                feedback: feedback.join(', ')
            };

            // Show feedback if password is weak
            const feedbackEl = document.getElementById('passwordFeedback');
            if (feedbackEl) {
                if (score < 3 && feedback.length > 0) {
                    feedbackEl.textContent = feedback.join(', ');
                    feedbackEl.style.display = 'block';
                } else {
                    feedbackEl.style.display = 'none';
                }
            }
        }

        /**
         * Setup password toggle
         */
        setupPasswordToggle() {
            const toggleButtons = document.querySelectorAll('.password-toggle');
            
            toggleButtons.forEach(button => {
                button.addEventListener('click', () => {
                    const input = button.previousElementSibling;
                    if (!input) return;

                    if (input.type === 'password') {
                        input.type = 'text';
                        button.textContent = '🙈';
                        button.setAttribute('aria-label', 'Hide password');
                    } else {
                        input.type = 'password';
                        button.textContent = '👁️';
                        button.setAttribute('aria-label', 'Show password');
                    }
                });
            });
        }

        /**
         * Setup social login
         */
        setupSocialLogin() {
            const socialButtons = document.querySelectorAll('[data-social-login]');
            
            socialButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    const provider = button.getAttribute('data-social-login');
                    this.handleSocialLogin(provider);
                });
            });
        }

        /**
         * Handle social login
         */
        handleSocialLogin(provider) {
            console.log('Social login with:', provider);
            
            // In production, this would redirect to OAuth provider
            this.showInfo(`${provider} login coming soon! This feature requires backend OAuth integration.`);
            
            // Example OAuth flow:
            /*
            const oauthUrls = {
                google: '/api/auth/google',
                github: '/api/auth/github',
                microsoft: '/api/auth/microsoft'
            };
            
            if (oauthUrls[provider]) {
                window.location.href = oauthUrls[provider];
            }
            */
        }

        /**
         * Setup terms checkbox
         */
        setupTermsCheckbox() {
            const checkbox = document.querySelector('input[name="terms"]');
            if (!checkbox) return;

            checkbox.addEventListener('change', (e) => {
                const submitBtn = document.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = !e.target.checked;
                    submitBtn.style.opacity = e.target.checked ? '1' : '0.5';
                }
            });
        }

        /**
         * Load remember me preference
         */
        loadRememberMe() {
            const email = localStorage.getItem('remember_email');
            const checkbox = document.querySelector('input[name="rememberMe"]');
            const emailInput = document.querySelector('input[name="email"]');

            if (email) {
                if (emailInput) emailInput.value = email;
                if (checkbox) checkbox.checked = true;
            }
        }

        /**
         * Show error message
         */
        showError(message) {
            this.showMessage(message, 'error');
        }

        /**
         * Show success message
         */
        showSuccess(message) {
            this.showMessage(message, 'success');
        }

        /**
         * Show info message
         */
        showInfo(message) {
            this.showMessage(message, 'info');
        }

        /**
         * Show message
         */
        showMessage(message, type = 'info') {
            // Try to use toast if available
            if (window.UIComponents) {
                window.UIComponents.alert(message, type === 'error' ? 'Error' : type === 'success' ? 'Success' : 'Info', type);
                return;
            }

            // Fallback to alert element
            const alertEl = document.getElementById('authAlert');
            if (alertEl) {
                alertEl.textContent = message;
                alertEl.className = `alert alert-${type}`;
                alertEl.style.display = 'block';
                
                setTimeout(() => {
                    alertEl.style.display = 'none';
                }, 5000);
            } else {
                // Last resort - native alert
                alert(message);
            }
        }

        /**
         * Show/hide loading
         */
        showLoading(show = true) {
            const submitBtn = document.querySelector('button[type="submit"]');
            const loadingOverlay = document.getElementById('loadingOverlay');

            if (submitBtn) {
                submitBtn.disabled = show;
                submitBtn.textContent = show ? 'Processing...' : submitBtn.getAttribute('data-original-text') || 'Submit';
                
                if (!show) {
                    submitBtn.removeAttribute('data-original-text');
                } else {
                    submitBtn.setAttribute('data-original-text', submitBtn.textContent);
                }
            }

            if (loadingOverlay) {
                if (show) {
                    loadingOverlay.classList.remove('hidden');
                } else {
                    loadingOverlay.classList.add('hidden');
                }
            }
        }

        /**
         * Handle forgot password
         */
        handleForgotPassword() {
            // Get email from form
            const emailInput = document.querySelector('input[name="email"]');
            const email = emailInput ? emailInput.value : '';

            if (window.UIComponents) {
                const content = document.createElement('div');
                const emailField = window.UIComponents.createFormField({
                    type: 'email',
                    label: 'Email Address',
                    name: 'resetEmail',
                    value: email,
                    placeholder: 'your@email.com',
                    required: true
                });
                content.appendChild(emailField.wrapper);

                const footer = document.createElement('div');
                const resetBtn = window.UIComponents.createButton('Send Reset Link', 'primary');
                resetBtn.addEventListener('click', () => {
                    const resetEmail = emailField.input.value;
                    if (this.validateEmail(resetEmail)) {
                        this.sendPasswordResetEmail(resetEmail);
                    } else {
                        this.showError('Please enter a valid email address');
                    }
                });
                footer.appendChild(resetBtn);

                window.UIComponents.createModal({
                    title: 'Reset Password',
                    content,
                    footer,
                    size: 'small'
                });
            } else {
                const resetEmail = prompt('Enter your email address to receive a password reset link:', email);
                if (resetEmail && this.validateEmail(resetEmail)) {
                    this.sendPasswordResetEmail(resetEmail);
                }
            }
        }

        /**
         * Send password reset email
         */
        async sendPasswordResetEmail(email) {
            this.showLoading(true);

            try {
                // Simulate API call
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                this.showSuccess(`Password reset link has been sent to ${email}`);
                
                // In production:
                /*
                const response = await fetch('/api/auth/forgot-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                const data = await response.json();
                */
            } catch (error) {
                this.showError('Failed to send password reset email. Please try again.');
            } finally {
                this.showLoading(false);
            }
        }

        /**
         * Logout
         */
        logout() {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user_data');
            
            window.location.href = 'index.html';
        }
    }

    // Create global instance
    window.AuthHandler = new AuthHandler();

    // Export for ES6 modules
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = AuthHandler;
    }

})(window);

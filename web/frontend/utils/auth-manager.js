/**
 * Authentication Manager
 * Handles user authentication, token management, and session persistence
 */

class AuthManager {
    constructor() {
        this.accessToken = null;
        this.refreshToken = null;
        this.user = null;
        this.tokenRefreshTimer = null;
        this.listeners = new Set();
        
        // Load saved tokens
        this.loadFromStorage();
        
        // Set up automatic token refresh
        if (this.accessToken) {
            this.scheduleTokenRefresh();
        }
    }

    /**
     * Register a listener for auth state changes
     */
    addAuthListener(callback) {
        this.listeners.add(callback);
        // Immediately notify with current state
        callback(this.isAuthenticated());
    }

    /**
     * Remove an auth state listener
     */
    removeAuthListener(callback) {
        this.listeners.delete(callback);
    }

    /**
     * Notify all listeners of auth state change
     */
    notifyListeners() {
        const isAuth = this.isAuthenticated();
        this.listeners.forEach(callback => {
            try {
                callback(isAuth);
            } catch (error) {
                console.error('Error in auth listener:', error);
            }
        });
    }

    /**
     * Load tokens and user data from localStorage
     */
    loadFromStorage() {
        try {
            this.accessToken = localStorage.getItem('access_token');
            this.refreshToken = localStorage.getItem('refresh_token');
            const userData = localStorage.getItem('user_data');
            if (userData) {
                this.user = JSON.parse(userData);
            }
        } catch (error) {
            console.error('Error loading auth data:', error);
            this.clearStorage();
        }
    }

    /**
     * Save tokens and user data to localStorage
     */
    saveToStorage() {
        try {
            if (this.accessToken) {
                localStorage.setItem('access_token', this.accessToken);
            }
            if (this.refreshToken) {
                localStorage.setItem('refresh_token', this.refreshToken);
            }
            if (this.user) {
                localStorage.setItem('user_data', JSON.stringify(this.user));
            }
        } catch (error) {
            console.error('Error saving auth data:', error);
        }
    }

    /**
     * Clear all auth data from storage
     */
    clearStorage() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        this.accessToken = null;
        this.refreshToken = null;
        this.user = null;
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.accessToken && !!this.user;
    }

    /**
     * Get current user
     */
    getUser() {
        return this.user;
    }

    /**
     * Get access token
     */
    getAccessToken() {
        return this.accessToken;
    }

    /**
     * Login with email and password
     */
    async login(email, password, rememberMe = true) {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Login failed');
            }

            const data = await response.json();
            
            this.accessToken = data.access_token;
            this.refreshToken = data.refresh_token;
            this.user = data.user;

            if (rememberMe) {
                this.saveToStorage();
            }

            this.scheduleTokenRefresh();
            this.notifyListeners();

            return { success: true, user: this.user };
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Register new user
     */
    async register(userData) {
        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Registration failed');
            }

            const data = await response.json();
            
            // Auto-login after registration
            this.accessToken = data.access_token;
            this.refreshToken = data.refresh_token;
            this.user = data.user;

            this.saveToStorage();
            this.scheduleTokenRefresh();
            this.notifyListeners();

            return { success: true, user: this.user };
        } catch (error) {
            console.error('Registration error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            // Call logout endpoint to invalidate tokens on server
            if (this.accessToken) {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.accessToken}`
                    }
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local state regardless of API call success
            this.clearStorage();
            
            if (this.tokenRefreshTimer) {
                clearTimeout(this.tokenRefreshTimer);
                this.tokenRefreshTimer = null;
            }

            this.notifyListeners();
        }
    }

    /**
     * Refresh access token using refresh token
     */
    async refreshAccessToken() {
        if (!this.refreshToken) {
            await this.logout();
            return false;
        }

        try {
            const response = await fetch('/api/auth/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: this.refreshToken })
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            this.accessToken = data.access_token;
            
            this.saveToStorage();
            this.scheduleTokenRefresh();

            return true;
        } catch (error) {
            console.error('Token refresh error:', error);
            await this.logout();
            return false;
        }
    }

    /**
     * Schedule automatic token refresh
     * Tokens are typically valid for 15 minutes, refresh after 10 minutes
     */
    scheduleTokenRefresh() {
        if (this.tokenRefreshTimer) {
            clearTimeout(this.tokenRefreshTimer);
        }

        // Refresh token after 10 minutes
        const refreshInterval = 10 * 60 * 1000;
        this.tokenRefreshTimer = setTimeout(() => {
            this.refreshAccessToken();
        }, refreshInterval);
    }

    /**
     * Make authenticated API request
     */
    async fetchWithAuth(url, options = {}) {
        if (!this.accessToken) {
            throw new Error('Not authenticated');
        }

        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${this.accessToken}`
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        // If unauthorized, try to refresh token and retry
        if (response.status === 401) {
            const refreshed = await this.refreshAccessToken();
            if (refreshed) {
                // Retry with new token
                headers['Authorization'] = `Bearer ${this.accessToken}`;
                return fetch(url, {
                    ...options,
                    headers
                });
            }
        }

        return response;
    }

    /**
     * Get user profile
     */
    async fetchUserProfile() {
        try {
            const response = await this.fetchWithAuth('/api/auth/me');
            
            if (!response.ok) {
                throw new Error('Failed to fetch user profile');
            }

            const data = await response.json();
            this.user = data.user;
            this.saveToStorage();

            return { success: true, user: this.user };
        } catch (error) {
            console.error('Error fetching user profile:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Update user profile
     */
    async updateProfile(updates) {
        try {
            const response = await this.fetchWithAuth('/api/auth/update-profile', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updates)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Profile update failed');
            }

            const data = await response.json();
            this.user = data.user;
            this.saveToStorage();

            return { success: true, user: this.user };
        } catch (error) {
            console.error('Profile update error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Change password
     */
    async changePassword(currentPassword, newPassword) {
        try {
            const response = await this.fetchWithAuth('/api/auth/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Password change failed');
            }

            return { success: true };
        } catch (error) {
            console.error('Password change error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Request password reset
     */
    async requestPasswordReset(email) {
        try {
            const response = await fetch('/api/auth/forgot-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Password reset request failed');
            }

            return { success: true };
        } catch (error) {
            console.error('Password reset request error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Reset password with token
     */
    async resetPassword(token, newPassword) {
        try {
            const response = await fetch('/api/auth/reset-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token,
                    new_password: newPassword
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Password reset failed');
            }

            return { success: true };
        } catch (error) {
            console.error('Password reset error:', error);
            return { success: false, error: error.message };
        }
    }
}

// Create singleton instance
const authManager = new AuthManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = authManager;
}

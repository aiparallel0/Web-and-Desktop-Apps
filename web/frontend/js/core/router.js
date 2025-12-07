/**
 * Client-Side Router
 * Handles navigation and route management
 */

class Router {
    constructor() {
        this.routes = new Map();
        this.middlewares = [];
        this.currentRoute = null;
        this.history = [];
        this.hooks = {
            beforeEach: [],
            afterEach: []
        };

        this.init();
    }

    init() {
        window.addEventListener('popstate', (e) => {
            this.navigate(window.location.pathname, { replace: true });
        });

        window.addEventListener('load', () => {
            this.navigate(window.location.pathname, { replace: true });
        });

        // Intercept link clicks
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href]');
            if (link && this.shouldIntercept(link)) {
                e.preventDefault();
                this.navigate(link.getAttribute('href'));
            }
        });
    }

    shouldIntercept(link) {
        const href = link.getAttribute('href');
        
        // Don't intercept external links
        if (link.hasAttribute('target')) return false;
        if (href.startsWith('http')) return false;
        if (href.startsWith('mailto:')) return false;
        if (href.startsWith('tel:')) return false;
        
        return true;
    }

    /**
     * Define a route
     */
    route(path, handler, options = {}) {
        const pattern = this.pathToRegex(path);
        
        this.routes.set(path, {
            path,
            pattern,
            handler,
            name: options.name,
            meta: options.meta || {},
            beforeEnter: options.beforeEnter
        });

        return this;
    }

    /**
     * Convert path to regex pattern
     */
    pathToRegex(path) {
        const pattern = path
            .replace(/\//g, '\/')
            .replace(/:\w+/g, '([^/]+)')
            .replace(/\*/g, '(.*)');
        
        return new RegExp(`^${pattern}$`);
    }

    /**
     * Navigate to path
     */
    async navigate(path, options = {}) {
        const replace = options.replace || false;
        
        // Run before hooks
        for (const hook of this.hooks.beforeEach) {
            const result = await hook(path, this.currentRoute);
            if (result === false) return; // Cancel navigation
        }

        // Find matching route
        const route = this.matchRoute(path);
        
        if (!route) {
            console.warn(`No route found for: ${path}`);
            return;
        }

        // Extract params
        const params = this.extractParams(route, path);
        
        // Run route guard
        if (route.beforeEnter) {
            const result = await route.beforeEnter(params, route);
            if (result === false) return;
        }

        // Run middlewares
        for (const mw of this.middlewares) {
            const result = await mw(route, params);
            if (result === false) return;
        }

        // Update browser history
        if (!replace) {
            window.history.pushState({}, '', path);
        }

        // Execute route handler
        try {
            await route.handler(params, route);
            
            // Update current route
            this.currentRoute = {
                path,
                params,
                route
            };

            // Add to history
            this.history.push(this.currentRoute);
            if (this.history.length > 50) {
                this.history.shift();
            }

            // Run after hooks
            for (const hook of this.hooks.afterEach) {
                await hook(this.currentRoute);
            }

        } catch (error) {
            console.error('Route handler error:', error);
        }
    }

    /**
     * Match path to route
     */
    matchRoute(path) {
        for (const [key, route] of this.routes) {
            if (route.pattern.test(path)) {
                return route;
            }
        }
        return null;
    }

    /**
     * Extract params from path
     */
    extractParams(route, path) {
        const match = route.pattern.exec(path);
        if (!match) return {};

        const params = {};
        const paramNames = route.path.match(/:\w+/g) || [];
        
        paramNames.forEach((name, index) => {
            params[name.substring(1)] = match[index + 1];
        });

        return params;
    }

    /**
     * Add middleware
     */
    use(middleware) {
        this.middlewares.push(middleware);
        return this;
    }

    /**
     * Add navigation hook
     */
    beforeEach(hook) {
        this.hooks.beforeEach.push(hook);
        return this;
    }

    afterEach(hook) {
        this.hooks.afterEach.push(hook);
        return this;
    }

    /**
     * Go back
     */
    back() {
        window.history.back();
    }

    /**
     * Go forward
     */
    forward() {
        window.history.forward();
    }

    /**
     * Replace current route
     */
    replace(path) {
        this.navigate(path, { replace: true });
    }
}

const router = new Router();

if (typeof window !== 'undefined') {
    window.Router = router;
}

export default router;

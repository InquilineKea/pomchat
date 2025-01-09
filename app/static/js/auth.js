class AuthManager {
    constructor() {
        this.initializeElements();
        this.initializeEventListeners();
    }
    
    initializeElements() {
        this.loginBtn = document.getElementById('login-btn');
        this.logoutBtn = document.getElementById('logout-btn');
        this.getStartedBtn = document.getElementById('get-started-btn');
    }
    
    initializeEventListeners() {
        if (this.loginBtn) {
            this.loginBtn.addEventListener('click', () => this.showLoginPrompt());
        }
        
        if (this.logoutBtn) {
            this.logoutBtn.addEventListener('click', () => this.logout());
        }
        
        if (this.getStartedBtn) {
            this.getStartedBtn.addEventListener('click', () => this.showLoginPrompt());
        }
    }
    
    async showLoginPrompt() {
        const username = prompt('Enter your username:');
        if (username) {
            await this.login(username);
        }
    }
    
    async login(username) {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
        
        if (response.ok) {
            window.location.href = '/chat';
        } else {
            const data = await response.json();
            if (data.error === 'user not found') {
                await this.register(username);
            } else {
                alert('Login failed. Please try again.');
            }
        }
    }
    
    async register(username) {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
        
        if (response.ok) {
            window.location.href = '/chat';
        } else {
            alert('Registration failed. Please try again.');
        }
    }
    
    async logout() {
        const response = await fetch('/auth/logout', {
            method: 'POST'
        });
        
        if (response.ok) {
            window.location.href = '/';
        }
    }
}

// Initialize auth manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const auth = new AuthManager();
});

class AdminDashboardManager {
    constructor() {
        this.initializeDashboard();
        this.setupEventHandlers();
    }

    initializeDashboard() {
        this.refreshMetrics();
        this.initializeUI();
    }

    async refreshMetrics() {
        try {
            const metrics = await this.fetchAdminMetrics();
            this.updateDashboardMetrics(metrics);
            this.updateStatusIndicators();
        } catch (error) {
            this.handleAdminError('Failed to refresh metrics', error);
        }
    }

    async fetchAdminMetrics() {
        const response = await fetch('/admin/api/metrics', {
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        });
        if (!response.ok) {
            throw new Error('Failed to fetch admin metrics');
        }
        return response.json();
    }

    setupEventHandlers() {
        document.querySelectorAll('.admin-action-button').forEach(button => {
            button.addEventListener('click', (e) => this.handleAdminAction(e));
        });
    }

    handleAdminError(message, error) {
        console.error(`Admin Error: ${message}`, error);
        this.showAdminNotification('error', message);
    }
}

// Initialize admin dashboard
document.addEventListener('DOMContentLoaded', () => {
    const adminDashboard = new AdminDashboardManager();
}); 
// Funções utilitárias globais
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips do Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Adicionar classe de animação aos elementos
    const animatedElements = document.querySelectorAll('.card, .btn, .list-group-item');
    animatedElements.forEach(el => {
        el.classList.add('fade-in');
    });

    // Sistema de notificações
    window.showNotification = function(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';

        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Adicionar ao topo da página
        const container = document.querySelector('main');
        container.insertBefore(notification, container.firstChild);

        // Remover automaticamente após 5 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    };

    // Verificar autenticação em páginas que requerem login
    const protectedPages = ['/profile', '/challenge/'];
    const currentPath = window.location.pathname;
    
    if (protectedPages.some(page => currentPath.startsWith(page)) && !window.userLoggedIn) {
        // Redirecionar para login se não estiver autenticado
        window.location.href = '/login?next=' + encodeURIComponent(currentPath);
    }
});

// Função para formatar código
function formatCode(code, language) {
    // Implementação básica de formatação
    // Em produção, use uma biblioteca como Prism.js ou Highlight.js
    return code;
}

// Sistema de progresso local
const ProgressManager = {
    getProgress: function() {
        return JSON.parse(localStorage.getItem('challengeProgress') || '{}');
    },

    setProgress: function(challengeId, status, code = '', language = '') {
        const progress = this.getProgress();
        progress[challengeId] = {
            status: status,
            code: code,
            language: language,
            updatedAt: new Date().toISOString()
        };
        localStorage.setItem('challengeProgress', JSON.stringify(progress));
        return progress[challengeId];
    },

    getChallengeStatus: function(challengeId) {
        const progress = this.getProgress();
        return progress[challengeId] || { status: 'pending' };
    },

    getCompletedCount: function() {
        const progress = this.getProgress();
        return Object.values(progress).filter(item => item.status === 'completed').length;
    }
};

// Exportar para uso global
window.ProgressManager = ProgressManager;
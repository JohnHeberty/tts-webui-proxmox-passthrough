/**
 * Toast Notification Utility
 * Sprint 7: Extracted from app.js
 * 
 * Manages Bootstrap toast notifications for user feedback
 */

/**
 * Show a toast notification
 * 
 * @param {string} title - Toast title
 * @param {string} message - Toast message content
 * @param {string} type - Toast type: 'success', 'danger', 'warning', 'info', 'primary'
 * @param {number} duration - Auto-hide delay in ms (0 = no auto-hide, default: 5000)
 */
function showToast(title, message = '', type = 'info', duration = 5000) {
    const toastContainer = document.getElementById('toast-container');
    
    // Create container if it doesn't exist
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    // Map type to Bootstrap classes
    const typeClasses = {
        'success': 'bg-success text-white',
        'danger': 'bg-danger text-white',
        'warning': 'bg-warning text-dark',
        'info': 'bg-info text-white',
        'primary': 'bg-primary text-white'
    };

    const toastClass = typeClasses[type] || typeClasses['info'];

    // Create toast element
    const toastId = `toast-${Date.now()}`;
    const toastHTML = `
        <div id="${toastId}" class="toast ${toastClass}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header ${toastClass}">
                <strong class="me-auto">${escapeHtml(title)}</strong>
                <button type="button" class="btn-close ${type === 'warning' ? '' : 'btn-close-white'}" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            ${message ? `<div class="toast-body">${escapeHtml(message)}</div>` : ''}
        </div>
    `;

    // Add to container
    const container = document.getElementById('toast-container');
    container.insertAdjacentHTML('beforeend', toastHTML);

    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: duration > 0,
        delay: duration
    });

    // Remove from DOM after hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });

    toast.show();

    return toast;
}

/**
 * Show success toast
 */
function showSuccess(message, title = 'Sucesso') {
    return showToast(title, message, 'success');
}

/**
 * Show error toast
 */
function showError(message, title = 'Erro') {
    return showToast(title, message, 'danger');
}

/**
 * Show warning toast
 */
function showWarning(message, title = 'Atenção') {
    return showToast(title, message, 'warning');
}

/**
 * Show info toast
 */
function showInfo(message, title = 'Informação') {
    return showToast(title, message, 'info');
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export for module systems or attach to window
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        showToast, 
        showSuccess, 
        showError, 
        showWarning, 
        showInfo 
    };
} else {
    window.ToastNotifier = { 
        showToast, 
        showSuccess, 
        showError, 
        showWarning, 
        showInfo 
    };
}

// static/js/script.js - Global App Script

document.addEventListener('DOMContentLoaded', () => {
    // Mobile navigation drawer toggle
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const mobileDrawer = document.getElementById('mobileDrawer');
    if (mobileBtn && mobileDrawer) {
        mobileBtn.addEventListener('click', () => {
            mobileDrawer.classList.toggle('open');
        });
    }

    // Auto dismiss flash alerts after 5 seconds
    const flashAlerts = document.querySelectorAll('.flash-alert');
    if (flashAlerts.length > 0) {
        setTimeout(() => {
            flashAlerts.forEach(alert => {
                alert.style.transition = 'opacity 0.5s ease';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            });
        }, 5000);
    }
});

// Toggle password visibility
function togglePasswordVisibility(inputId = 'password', iconId = 'pwdEyeIcon') {
    const input = document.getElementById(inputId);
    const eyeIcon = document.getElementById(iconId);
    if (!input || !eyeIcon) return;

    if (input.type === 'password') {
        input.type = 'text';
        eyeIcon.classList.remove('fa-eye');
        eyeIcon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        eyeIcon.classList.remove('fa-eye-slash');
        eyeIcon.classList.add('fa-eye');
    }
}

// Global Slip Preview Modal
function openSlipModal(imageUrl) {
    const modal = document.getElementById('slipModal');
    const img = document.getElementById('modalSlipImg');
    if (modal && img) {
        img.src = imageUrl;
        modal.classList.add('open');
    }
}

function closeSlipModal(event) {
    if (event && event.target && event.target.id !== 'slipModal' && !event.target.classList.contains('btn-close-modal') && !event.target.classList.contains('btn-secondary')) {
        return;
    }
    const modal = document.getElementById('slipModal');
    if (modal) {
        modal.classList.remove('open');
    }
}

// Global Delete Confirmation Modal
function openDeleteModal(txId) {
    const modal = document.getElementById('deleteModal');
    const form = document.getElementById('deleteForm');
    if (modal && form) {
        form.action = `/api/delete-transaction/${txId}`;
        modal.classList.add('open');
    }
}

function closeDeleteModal(event) {
    if (event && event.target && event.target.id !== 'deleteModal' && !event.target.classList.contains('btn-close-modal') && !event.target.classList.contains('btn-secondary')) {
        return;
    }
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.classList.remove('open');
    }
}

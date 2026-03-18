/**
 * TheSevenRPG — Utilities
 * Toast, Loading, DOM 헬퍼, 포맷터
 */

// ── Toast ──

let toastContainer = null;

function initToast() {
    toastContainer = document.getElementById('toast-container');
}

/**
 * 토스트 메시지 표시
 * @param {string} message
 * @param {'success'|'warning'|'error'|'info'} type
 * @param {number} duration - ms (기본 3초)
 */
export function showToast(message, type = 'info', duration = 3000) {
    if (!toastContainer) initToast();

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add('show'));

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ── Loading ──

let loadingOverlay = null;
let loadingCount = 0;

function initLoading() {
    loadingOverlay = document.getElementById('loading-overlay');
}

export function showLoading() {
    if (!loadingOverlay) initLoading();
    loadingCount++;
    loadingOverlay.classList.add('show');
}

export function hideLoading() {
    if (!loadingOverlay) initLoading();
    loadingCount = Math.max(0, loadingCount - 1);
    if (loadingCount === 0) {
        loadingOverlay.classList.remove('show');
    }
}

// ── DOM 헬퍼 ──

/** XSS 방지용 HTML 이스케이프 */
export function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ── 포맷터 ──

/** 골드 포맷 (1000 → "1,000 G") */
export function formatGold(gold) {
    return `${gold.toLocaleString()} G`;
}

/**
 * TheSevenTactics — App Entry
 * 2화면 전환: Login ↔ Main
 */
import { isLoggedIn } from './session.js';
import { loadMetaData } from './meta-data.js';
import LoginScreen from './screens/login.js';
import MainScreen from './main.js';

let currentView = null; // 'login' | 'main'
let appContainer = null;

/** 화면 전환 */
export function switchView(viewName) {
    if (viewName === currentView) return;

    // 현재 화면 언마운트
    if (currentView === 'login' && LoginScreen.unmount) {
        LoginScreen.unmount();
    } else if (currentView === 'main' && MainScreen.unmount) {
        MainScreen.unmount();
    }

    // 기존 화면 비활성화
    const existing = appContainer.querySelector('.view.active');
    if (existing) existing.classList.remove('active');

    currentView = viewName;

    // 새 화면 마운트
    let viewEl = appContainer.querySelector(`[data-view="${viewName}"]`);
    if (!viewEl) {
        viewEl = document.createElement('div');
        viewEl.className = 'view';
        viewEl.dataset.view = viewName;
        appContainer.appendChild(viewEl);
    }

    if (viewName === 'login') {
        LoginScreen.mount(viewEl);
    } else if (viewName === 'main') {
        MainScreen.mount(viewEl);
    }

    viewEl.classList.add('active');
}

// ── visibilitychange ──
function handleVisibilityChange() {
    if (!currentView) return;

    if (currentView === 'main' && MainScreen.onVisibilityChange) {
        MainScreen.onVisibilityChange(document.hidden);
    }
}

// ── Service Worker ──
function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(() => console.log('[App] Service Worker 등록 완료'))
            .catch((err) => console.warn('[App] Service Worker 등록 실패:', err));
    }
}

// ── 초기화 ──
async function init() {
    appContainer = document.getElementById('app');

    await loadMetaData();

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // 세션 유무에 따라 초기 화면 결정
    if (isLoggedIn()) {
        switchView('main');
    } else {
        switchView('login');
    }

    registerServiceWorker();
    console.log('[App] TheSevenTactics 클라이언트 초기화 완료');
}

document.addEventListener('DOMContentLoaded', () => init());

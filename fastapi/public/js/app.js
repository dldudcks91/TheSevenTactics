/**
 * TheSevenTactics — App Entry
 * SceneManager 기반 씬 전환: Splash → Login/Prologue → Walking → Main
 */
import { isLoggedIn } from './session.js';
import { loadMetaData } from './meta-data.js';
import { SceneManager } from './scene-manager.js';
import SplashScene from './scenes/splash.js';
import LoginScreen from './screens/login.js';
import PrologueScene from './scenes/prologue.js';
import WalkingScene from './scenes/walking.js';
import MainScreen from './main.js';

let appContainer = null;

/** 글로벌 씬 전환 (다른 모듈에서 import해서 사용) */
export function switchScene(name, data) {
    return SceneManager.resetTo(name, data);
}

/** 기존 switchView 호환 (login ↔ main) */
export function switchView(viewName) {
    return SceneManager.resetTo(viewName);
}

// ── visibilitychange ──
function handleVisibilityChange() {
    const current = SceneManager.current();
    if (current === 'main' && MainScreen.onVisibilityChange) {
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

    // SceneManager 초기화 + 씬 등록
    SceneManager.init(appContainer);
    SceneManager.register('splash', SplashScene);
    SceneManager.register('login', LoginScreen);
    SceneManager.register('prologue', PrologueScene);
    SceneManager.register('walking', WalkingScene);
    SceneManager.register('main', MainScreen);

    await loadMetaData();

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // 세션 유무에 따라 초기 화면 결정
    if (isLoggedIn()) {
        await SceneManager.push('main');
    } else {
        await SceneManager.push('splash');
    }

    registerServiceWorker();
    console.log('[App] TheSevenTactics 클라이언트 초기화 완료');
}

document.addEventListener('DOMContentLoaded', () => init());

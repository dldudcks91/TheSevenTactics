/**
 * TheSevenTactics — Splash Scene
 * 타이틀 표시 + 메타데이터 로딩 + 자동 전환
 */
import { loadMetaData } from '../meta-data.js';
import { isLoggedIn } from '../session.js';
import { SceneManager } from '../scene-manager.js';

const SplashScene = {
    el: null,
    refs: {},

    mount(el) {
        this.el = el;

        el.innerHTML = `
            <div class="splash-screen">
                <div class="splash-title-area">
                    <h1 class="splash-title">THE SEVEN</h1>
                    <p class="splash-subtitle">TACTICS</p>
                </div>
                <div class="splash-loading-area">
                    <div class="splash-progress-track">
                        <div class="splash-progress-bar" id="splash-progress"></div>
                    </div>
                    <p class="splash-status" id="splash-status">초기화 중...</p>
                </div>
            </div>
        `;

        this.refs = {
            progress: el.querySelector('#splash-progress'),
            status: el.querySelector('#splash-status'),
        };

        this._load();
    },

    unmount() {
        this.refs = {};
    },

    async _load() {
        try {
            this._setProgress(10, '데이터 로딩 중...');
            await loadMetaData();
            this._setProgress(80, '준비 완료');

            await this._delay(400);
            this._setProgress(100, '시작합니다');
            await this._delay(300);

            if (isLoggedIn()) {
                SceneManager.replace('main');
            } else {
                SceneManager.replace('login');
            }
        } catch (err) {
            console.error('[Splash] Loading failed:', err);
            this._setProgress(0, '로딩 실패');
        }
    },

    _setProgress(percent, text) {
        if (this.refs.progress) this.refs.progress.style.width = `${percent}%`;
        if (this.refs.status) this.refs.status.textContent = text;
    },

    _delay(ms) {
        return new Promise(r => setTimeout(r, ms));
    },
};

export default SplashScene;

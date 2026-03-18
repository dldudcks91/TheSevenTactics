/**
 * TheSevenTactics — Main Screen
 * 상단 바 + 좌측 패널 + 우측 메인뷰 (마을)
 */
import TopBar from './main/top-bar.js';
import LeftPanel from './main/left-panel.js';
import TownView from './main/views/town-view.js';
import { apiCall } from './api.js';
import { Store } from './store.js';
import { showLoading, hideLoading } from './utils.js';

// 우측 뷰 모듈 맵
const VIEW_MODULES = {
    town: TownView,
};

const MainScreen = {
    el: null,
    _rightViewMode: null,
    _rightViewModule: null,

    mount(el) {
        this.el = el;

        if (!el.dataset.initialized) {
            el.innerHTML = `
                <div class="main-screen">
                    <div class="main-top-bar" id="main-top-bar"></div>
                    <div class="main-body">
                        <div class="main-left-panel" id="main-left-panel"></div>
                        <div class="main-right-view" id="main-right-view"></div>
                    </div>
                </div>
            `;
            el.dataset.initialized = 'true';
        }

        TopBar.mount(el.querySelector('#main-top-bar'));
        LeftPanel.mount(el.querySelector('#main-left-panel'));

        // 우측 뷰: 기본 마을 모드
        this.switchRightView('town');

        this._loadUserData();
    },

    unmount() {
        TopBar.unmount();
        LeftPanel.unmount();
        if (this._rightViewModule && this._rightViewModule.unmount) {
            this._rightViewModule.unmount();
        }
        this._rightViewModule = null;
        this._rightViewMode = null;
    },

    onVisibilityChange(hidden) {
        if (this._rightViewModule && this._rightViewModule.onVisibilityChange) {
            this._rightViewModule.onVisibilityChange(hidden);
        }
    },

    /** 우측 뷰 전환 */
    switchRightView(mode, data) {
        const rightEl = this.el.querySelector('#main-right-view');

        if (this._rightViewModule && this._rightViewModule.unmount) {
            this._rightViewModule.unmount();
        }

        this._rightViewMode = mode;
        rightEl.innerHTML = '';
        delete rightEl.dataset.initialized;

        const module = VIEW_MODULES[mode];
        if (module) {
            this._rightViewModule = module;
            module.mount(rightEl, data);
        } else {
            this._rightViewModule = null;
            rightEl.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted)">${mode} (준비 중)</div>`;
        }
    },

    /** 유저 데이터 로드 (API 1004) */
    async _loadUserData() {
        showLoading();
        try {
            const result = await apiCall(1004, {});
            if (result?.success) {
                const d = result.data;
                Store.set('user.name', d.user_name);
                Store.set('user.level', d.level);
                Store.set('user.gold', d.gold);
                Store.set('user.exp', d.exp);
                Store.set('user.stat_points', d.stat_points);
                Store.set('user.current_stage', d.current_stage);
                Store.merge(d.stats, 'stats');
            }
        } finally {
            hideLoading();
        }
    },
};

export default MainScreen;

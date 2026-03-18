/**
 * TheSevenTactics — Left Panel (탭 구조)
 * 탭: 스탯 / 영웅 / 파티 / 장비 / 스킬트리
 */

const TABS = [
    { id: 'stat', icon: '📊', label: '스탯' },
    { id: 'hero', icon: '⚔️', label: '영웅' },
    { id: 'party', icon: '👥', label: '파티' },
    { id: 'equip', icon: '🛡️', label: '장비' },
    { id: 'skill', icon: '🔮', label: '스킬' },
];

const LeftPanel = {
    el: null,
    _currentTab: 'stat',

    mount(el) {
        this.el = el;

        el.innerHTML = `
            <div class="left-panel">
                <div class="left-panel-tabs">
                    ${TABS.map(t => `
                        <button class="lp-tab ${t.id === 'stat' ? 'active' : ''}" data-action="tab" data-tab="${t.id}">
                            <span class="lp-tab-icon">${t.icon}</span>
                            <span class="lp-tab-label">${t.label}</span>
                        </button>
                    `).join('')}
                </div>
                <div class="left-panel-content" id="lp-content">
                    <div class="lp-tab-placeholder">스탯 (준비 중)</div>
                </div>
            </div>
        `;

        this._handleEvent = this._onEvent.bind(this);
        el.addEventListener('pointerdown', this._handleEvent);
    },

    unmount() {
        if (this._handleEvent) {
            this.el.removeEventListener('pointerdown', this._handleEvent);
        }
    },

    _onEvent(e) {
        const target = e.target.closest('[data-action]');
        if (!target) return;

        if (target.dataset.action === 'tab') {
            const tabId = target.dataset.tab;
            if (tabId === this._currentTab) return;

            // 탭 활성화 전환
            this.el.querySelectorAll('.lp-tab').forEach(btn => btn.classList.remove('active'));
            target.classList.add('active');

            this._currentTab = tabId;
            const content = this.el.querySelector('#lp-content');
            const tab = TABS.find(t => t.id === tabId);
            content.innerHTML = `<div class="lp-tab-placeholder">${tab?.label || tabId} (준비 중)</div>`;
        }
    },
};

export default LeftPanel;

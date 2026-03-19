/**
 * TheSevenTactics — Left Panel (탭 구조)
 * 탭: 스탯 / 영웅 / 파티 / 장비 / 스킬트리
 */
import StatTab from './tabs/stat.js';
import HeroTab from './tabs/hero.js';
import PartyTab from './tabs/party.js';
import EquipTab from './tabs/equip.js';
import SkillTab from './tabs/skill.js';

const TABS = [
    { id: 'stat', icon: '📊', label: '스탯', module: StatTab },
    { id: 'hero', icon: '⚔️', label: '영웅', module: HeroTab },
    { id: 'party', icon: '👥', label: '파티', module: PartyTab },
    { id: 'equip', icon: '🛡️', label: '장비', module: EquipTab },
    { id: 'skill', icon: '🔮', label: '스킬', module: SkillTab },
];

const LeftPanel = {
    el: null,
    _currentTab: 'stat',
    _currentModule: null,

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
                <div class="left-panel-content" id="lp-content"></div>
            </div>
        `;

        this._handleEvent = this._onEvent.bind(this);
        el.addEventListener('pointerdown', this._handleEvent);

        // 초기 탭 마운트
        this._mountTab('stat');
    },

    unmount() {
        if (this._currentModule && this._currentModule.unmount) {
            this._currentModule.unmount();
        }
        if (this._handleEvent) {
            this.el.removeEventListener('pointerdown', this._handleEvent);
        }
    },

    _onEvent(e) {
        const target = e.target.closest('[data-action="tab"]');
        if (!target) return;

        const tabId = target.dataset.tab;
        if (tabId === this._currentTab) return;

        this.el.querySelectorAll('.lp-tab').forEach(btn => btn.classList.remove('active'));
        target.classList.add('active');

        this._mountTab(tabId);
    },

    _mountTab(tabId) {
        if (this._currentModule && this._currentModule.unmount) {
            this._currentModule.unmount();
        }

        this._currentTab = tabId;
        const content = this.el.querySelector('#lp-content');
        const tab = TABS.find(t => t.id === tabId);

        if (tab?.module) {
            content.innerHTML = '';
            this._currentModule = tab.module;
            tab.module.mount(content);
        } else {
            this._currentModule = null;
            content.innerHTML = `<div class="lp-tab-placeholder">${tab?.label || tabId} (준비 중)</div>`;
        }
    },
};

export default LeftPanel;

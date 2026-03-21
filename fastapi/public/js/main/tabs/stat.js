/**
 * TheSevenTactics — Stat Tab
 * 바알 지휘관 버프 + 유저 레벨 표시
 */
import { Store } from '../../store.js';

const COMMANDER_BUFFS = [
    { key: 'atk_pct', label: '공격력 %', perLevel: 1, unit: '%' },
    { key: 'def_pct', label: '방어력 %', perLevel: 1, unit: '%' },
    { key: 'hp_pct', label: '최대 HP %', perLevel: 0.5, unit: '%' },
    { key: 'crit', label: '치명타 보정', perLevel: 0.2, unit: '' },
];

const StatTab = {
    el: null,
    _unsubs: [],

    mount(el) {
        this.el = el;
        this._render();
        this._unsubs.push(Store.subscribe('user.level', () => this._render()));
    },

    unmount() {
        this._unsubs.forEach(u => u());
        this._unsubs = [];
    },

    _render() {
        const level = Store.get('user.level') || 1;

        let html = `<div class="stat-tab">
            <div class="stat-commander-header">
                <div class="stat-commander-title">지휘관 바알</div>
                <div class="stat-commander-level">Lv.${level}</div>
            </div>
            <div class="stat-commander-desc">전투 밖에서 파티 전체에 레벨 기반 버프를 제공합니다.</div>
            <div class="stat-buff-list">`;

        for (const buff of COMMANDER_BUFFS) {
            const value = +(level * buff.perLevel).toFixed(1);
            html += `<div class="stat-row">
                <span class="stat-label">${buff.label}</span>
                <span class="stat-value">+${value}${buff.unit}</span>
            </div>`;
        }

        html += '</div></div>';
        this.el.innerHTML = html;
    },
};

export default StatTab;

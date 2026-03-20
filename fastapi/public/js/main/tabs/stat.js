/**
 * TheSevenTactics — Stat Tab
 * 바알(본캐) 5스탯 표시
 */
import { Store } from '../../store.js';

const STATS = [
    { key: 'str', label: 'STR', desc: '물리 공격력' },
    { key: 'dex', label: 'DEX', desc: '공격속도·명중·회피' },
    { key: 'vit', label: 'VIT', desc: 'HP·물리 방어' },
    { key: 'lck', label: 'LCK', desc: '치명타 확률·데미지' },
    { key: 'int', label: 'INT', desc: '마법 공격력·스킬 증폭' },
];

const StatTab = {
    el: null,
    _unsubs: [],

    mount(el) {
        this.el = el;
        this._render();
        for (const s of STATS) {
            this._unsubs.push(Store.subscribe(`stats.${s.key}`, () => this._render()));
        }
        this._unsubs.push(Store.subscribe('user.stat_points', () => this._render()));
    },

    unmount() {
        this._unsubs.forEach(u => u());
        this._unsubs = [];
    },

    _render() {
        const sp = Store.get('user.stat_points') || 0;

        let html = '<div class="stat-tab">';
        for (const s of STATS) {
            const val = Store.get(`stats.${s.key}`) ?? 0;
            html += `<div class="stat-row">
                <span class="stat-label">${s.label}</span>
                <span class="stat-desc">${s.desc}</span>
                <span class="stat-value">${val}</span>
            </div>`;
        }
        html += `<div class="stat-sp-row">
            <span class="stat-sp-label">잔여 포인트</span>
            <span class="stat-sp-value">${sp}</span>
        </div></div>`;

        this.el.innerHTML = html;
    },
};

export default StatTab;

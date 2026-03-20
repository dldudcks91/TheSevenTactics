/**
 * TheSevenTactics — Top Bar Component
 * 닉네임, 레벨, 스탯 칩(str/int/agi/vit/will), EXP 바, 골드, 로그아웃
 */
import { Store } from '../store.js';
import { formatGold } from '../utils.js';
import { clearSession } from '../session.js';
import { switchView } from '../app.js';

const TopBar = {
    el: null,
    refs: {},
    _unsubscribers: [],

    mount(el) {
        this.el = el;

        el.innerHTML = `
            <div class="top-bar">
                <div class="top-bar-row">
                    <div class="top-bar-left">
                        <span class="top-bar-name" id="tb-name">-</span>
                        <span class="top-bar-level" id="tb-level">Lv.1</span>
                    </div>
                    <div class="top-bar-stats" id="tb-stats"></div>
                    <div class="top-bar-right">
                        <span class="top-bar-gold" id="tb-gold">0 G</span>
                        <button class="top-bar-logout" data-action="logout">로그아웃</button>
                    </div>
                </div>
                <div class="top-bar-exp">
                    <div class="top-bar-exp-fill" id="tb-exp-fill" style="width: 0%"></div>
                </div>
            </div>
        `;

        this.refs = {
            name: el.querySelector('#tb-name'),
            level: el.querySelector('#tb-level'),
            stats: el.querySelector('#tb-stats'),
            gold: el.querySelector('#tb-gold'),
            expFill: el.querySelector('#tb-exp-fill'),
        };

        this._handleEvent = this._onEvent.bind(this);
        el.addEventListener('pointerdown', this._handleEvent);

        // Store 구독 — TheSevenTactics 5스탯
        this._unsubscribers.push(
            Store.subscribe('user.name', (v) => { this.refs.name.textContent = v; }),
            Store.subscribe('user.level', (v) => { this.refs.level.textContent = `Lv.${v}`; }),
            Store.subscribe('user.gold', (v) => { this.refs.gold.textContent = formatGold(v); }),
            Store.subscribe('user.exp', () => { this._renderExp(); }),
            Store.subscribe('user.stat_points', () => { this._renderStats(); }),
            Store.subscribe('stats.str', () => { this._renderStats(); }),
            Store.subscribe('stats.int', () => { this._renderStats(); }),
            Store.subscribe('stats.dex', () => { this._renderStats(); }),
            Store.subscribe('stats.vit', () => { this._renderStats(); }),
            Store.subscribe('stats.lck', () => { this._renderStats(); }),
        );
    },

    unmount() {
        if (this._handleEvent) {
            this.el.removeEventListener('pointerdown', this._handleEvent);
        }
        this._unsubscribers.forEach(unsub => unsub());
        this._unsubscribers = [];
    },

    _onEvent(e) {
        const target = e.target.closest('[data-action]');
        if (!target) return;

        if (target.dataset.action === 'logout') {
            clearSession();
            switchView('login');
        }
    },

    _renderStats() {
        const stats = [
            { label: 'STR', key: 'stats.str' },
            { label: 'INT', key: 'stats.int' },
            { label: 'DEX', key: 'stats.dex' },
            { label: 'VIT', key: 'stats.vit' },
            { label: 'LCK', key: 'stats.lck' },
        ];

        let html = stats.map(s =>
            `<span class="top-bar-stat-chip"><span>${s.label}</span> <span class="stat-val">${Store.get(s.key) ?? 0}</span></span>`
        ).join('');

        const sp = Store.get('user.stat_points');
        if (sp > 0) {
            html += `<span class="top-bar-stat-chip sp"><span>SP</span> <span class="stat-val">${sp}</span></span>`;
        }

        this.refs.stats.innerHTML = html;
    },

    _renderExp() {
        const exp = Store.get('user.exp') || 0;
        const pct = exp > 0 ? Math.min(100, (exp % 1000) / 10) : 0;
        this.refs.expFill.style.width = pct + '%';
    },
};

export default TopBar;

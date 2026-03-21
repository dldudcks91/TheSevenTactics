/**
 * TheSevenTactics — Top Bar Component
 * 닉네임, 레벨, 스탯 칩(str/int/agi/vit/will), EXP 바, 골드, 로그아웃
 */
import { Store } from '../store.js';
import { formatGold } from '../utils.js';
import { clearSession } from '../session.js';
import { switchScene } from '../app.js';

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

        // Store 구독
        this._unsubscribers.push(
            Store.subscribe('user.name', (v) => { this.refs.name.textContent = v; }),
            Store.subscribe('user.level', (v) => {
                this.refs.level.textContent = `Lv.${v}`;
                this._renderStats();
            }),
            Store.subscribe('user.gold', (v) => { this.refs.gold.textContent = formatGold(v); }),
            Store.subscribe('user.exp', () => { this._renderExp(); }),
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
            switchScene('login');
        }
    },

    _renderStats() {
        const level = Store.get('user.level') || 1;
        const atkBuff = level * 1;
        const defBuff = level * 1;

        this.refs.stats.innerHTML = `
            <span class="top-bar-stat-chip"><span>지휘관</span></span>
            <span class="top-bar-stat-chip"><span>ATK</span> <span class="stat-val">+${atkBuff}%</span></span>
            <span class="top-bar-stat-chip"><span>DEF</span> <span class="stat-val">+${defBuff}%</span></span>
        `;
    },

    _renderExp() {
        const exp = Store.get('user.exp') || 0;
        const pct = exp > 0 ? Math.min(100, (exp % 1000) / 10) : 0;
        this.refs.expFill.style.width = pct + '%';
    },
};

export default TopBar;

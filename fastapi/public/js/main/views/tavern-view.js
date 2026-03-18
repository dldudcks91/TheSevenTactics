/**
 * TheSevenTactics — Tavern View (선술집)
 */
import { apiCall } from '../../api.js';
import { showToast, formatGold } from '../../utils.js';
import { Store } from '../../store.js';

const GRADE_CLASS = { common: 'grade-common', uncommon: 'grade-uncommon', rare: 'grade-rare', legendary: 'grade-legendary' };

const TavernView = {
    el: null,
    _data: null,

    mount(el) {
        this.el = el;
        el.innerHTML = '<div class="tavern-view"><div class="tavern-empty">로딩 중...</div></div>';
        this._load();
    },
    unmount() {},

    async _load() {
        const result = await apiCall(5001, {});
        if (result?.success) {
            this._data = result.data;
            this._render();
        }
    },

    _render() {
        const d = this._data;
        if (!d || !d.has_visitor) {
            this.el.innerHTML = '<div class="tavern-view"><div class="tavern-panel"><div class="tavern-title">선술집</div><div class="tavern-empty">지금은 방문한 영웅이 없습니다.</div></div></div>';
            return;
        }

        const gc = GRADE_CLASS[d.grade] || '';
        this.el.innerHTML = `
            <div class="tavern-view">
                <div class="tavern-panel">
                    <div class="tavern-title">선술집</div>
                    <div class="tavern-hero-name ${gc}">${d.hero_name || d.hero_id}</div>
                    <div class="tavern-hero-meta">${d.grade} · ${d.faction}</div>
                    <div class="tavern-hero-skills">
                        스킬트리: ${d.skill_tree_1} / ${d.skill_tree_2}<br>
                        패시브: ${d.passive_name || '-'} · 액티브: ${d.active_name || '-'}
                    </div>
                    <div class="tavern-cost">${formatGold(d.recruit_cost)}</div>
                    <div class="tavern-buttons">
                        <button class="btn btn-primary tavern-btn-recruit" data-action="recruit">영입</button>
                        <button class="btn tavern-btn-dismiss" data-action="dismiss">돌려보내기</button>
                    </div>
                </div>
            </div>`;

        this.el.onclick = async (e) => {
            const action = e.target.closest('[data-action]')?.dataset.action;
            if (action === 'recruit') {
                const res = await apiCall(5002, {});
                if (res?.success) {
                    showToast(res.message, 'success');
                    Store.set('user.gold', res.data.gold);
                    await this._load();
                }
            } else if (action === 'dismiss') {
                const res = await apiCall(5003, {});
                if (res?.success) {
                    showToast(res.message, 'info');
                    await this._load();
                }
            }
        };
    },
};

export default TavernView;

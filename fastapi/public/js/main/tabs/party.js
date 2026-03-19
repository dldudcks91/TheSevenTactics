/**
 * TheSevenTactics — Party Tab
 * 3인 파티 편성 + 시너지 미리보기
 */
import { apiCall } from '../../api.js';
import { showToast } from '../../utils.js';

const PartyTab = {
    el: null,
    _party: null,
    _heroes: [],
    _pickingSlot: null,

    mount(el) {
        this.el = el;
        el.innerHTML = '<div class="party-tab">로딩 중...</div>';
        this._load();
    },
    unmount() {},

    async _load() {
        const [partyRes, heroRes] = await Promise.all([
            apiCall(6001, {}),
            apiCall(4001, {}),
        ]);
        if (partyRes?.success) this._party = partyRes.data;
        if (heroRes?.success) this._heroes = heroRes.data.heroes || [];
        this._render();
    },

    _render() {
        if (!this._party) { this.el.innerHTML = '<div class="party-tab">파티 정보 없음</div>'; return; }
        const slots = this._party.slots || [];
        const synergy = this._party.synergy || {};

        let html = '<div class="party-tab"><div class="party-slots">';
        for (let i = 0; i < 3; i++) {
            const slot = slots[i] || {};
            const isBaal = i === 0;
            const filled = !!slot.hero_uid;
            html += `<div class="party-slot ${filled ? 'filled' : ''} ${isBaal ? 'slot-baal' : ''}"
                ${!isBaal ? `data-action="pick-slot" data-slot="${i + 1}"` : ''}>
                <div class="party-slot-label">슬롯 ${i + 1}${isBaal ? ' (바알)' : ''}</div>
                ${filled ? `<div class="party-slot-name">${slot.hero_id || '?'}</div>
                    <div class="party-slot-meta">${slot.grade || ''} · ${slot.faction || ''}</div>` :
                    `<div class="party-slot-name" style="color:var(--text-muted)">${isBaal ? '바알' : '비어있음'}</div>`}
            </div>`;
        }
        html += '</div>';

        if (synergy.name) {
            html += `<div class="party-synergy">
                <div class="party-synergy-name">${synergy.name}</div>
                <div class="party-synergy-desc">${synergy.bonus}</div>
            </div>`;
        }

        if (this._pickingSlot) {
            html += `<div class="party-hero-picker" style="position:relative">
                <button class="close-x" data-action="close-picker" style="top:-2px;right:-2px;width:22px;height:22px;font-size:11px">✕</button>
                <div class="party-picker-title">슬롯 ${this._pickingSlot}에 배치할 영웅 선택</div>
                <div class="party-picker-item" data-action="clear-slot">비우기</div>`;
            for (const h of this._heroes) {
                if (h.hero_id === 'baal') continue;
                html += `<div class="party-picker-item" data-action="assign-hero" data-uid="${h.hero_uid}">
                    ${h.hero_name} (${h.grade} · ${h.faction})
                </div>`;
            }
            html += '</div>';
        }

        html += '</div>';
        this.el.innerHTML = html;

        this.el.onclick = (e) => {
            const pickSlot = e.target.closest('[data-action="pick-slot"]');
            if (pickSlot) {
                this._pickingSlot = parseInt(pickSlot.dataset.slot);
                this._render();
                return;
            }
            const assign = e.target.closest('[data-action="assign-hero"]');
            if (assign) { this._assign(parseInt(assign.dataset.uid)); return; }
            const clear = e.target.closest('[data-action="clear-slot"]');
            if (clear) { this._assign(null); return; }
            const closePicker = e.target.closest('[data-action="close-picker"]');
            if (closePicker) { this._pickingSlot = null; this._render(); return; }
        };
    },

    async _assign(heroUid) {
        const slot = this._pickingSlot;
        if (!slot) return;

        const slots = this._party?.slots || [];
        const current2 = slots[1]?.hero_uid || null;
        const current3 = slots[2]?.hero_uid || null;

        const payload = {
            slot_2: slot === 2 ? heroUid : current2,
            slot_3: slot === 3 ? heroUid : current3,
        };

        const result = await apiCall(6002, payload);
        if (result?.success) {
            showToast('파티가 편성되었습니다.', 'success');
            this._pickingSlot = null;
            await this._load();
        }
    },
};

export default PartyTab;

/**
 * TheSevenTactics — Pre-Battle View
 * 전투 전 설정: 파티 확인 + 출전 버튼
 * 향후 확장: 스킬 우선순위, 타겟 설정, 진형 배치
 */
import { apiCall } from '../../api.js';
import { Store } from '../../store.js';

const FACTION_ICON = { human: '🧑', demon: '😈', celestial: '👼' };
const GRADE_CLASS = { common: 'grade-common', uncommon: 'grade-uncommon', rare: 'grade-rare', legendary: 'grade-legendary' };

const CHAPTERS = {
    1: { sin: '분노', name: '불타는 전장' },
    2: { sin: '질투', name: '뒤틀린 숲' },
    3: { sin: '탐욕', name: '황금 사막' },
    4: { sin: '나태', name: '망각의 동토' },
    5: { sin: '폭식', name: '심연의 동굴' },
    6: { sin: '색욕', name: '타락한 궁전' },
    7: { sin: '교만', name: '천상의 폐허' },
};
const STAGE_NAMES = { 1: '외곽 탐색', 2: '내부 침투', 3: '핵심부 돌파', 4: '보스전' };

const PreBattleView = {
    el: null,
    _stageId: null,
    _party: null,

    mount(el, data) {
        this.el = el;
        this._stageId = data?.stageId;
        this._party = null;
        el.innerHTML = '<div class="prebattle-view"><div class="pb-loading">파티 정보 로딩 중...</div></div>';
        this._load();
    },

    unmount() {},

    async _load() {
        const res = await apiCall(6001, {});
        if (res?.success) {
            this._party = res.data;
            this._render();
        }
    },

    _render() {
        const ch = Math.floor(this._stageId / 100);
        const stNum = this._stageId % 100;
        const chInfo = CHAPTERS[ch] || {};
        const isBoss = stNum === 4;
        const p = this._party;

        let html = `<div class="prebattle-view" style="position:relative">
            <button class="close-x" data-action="back">✕</button>
            <div class="pb-header">
                <div class="pb-stage-name">${ch}-${stNum}: ${STAGE_NAMES[stNum] || ''}${isBoss ? ' (BOSS)' : ''}</div>
                <div class="pb-chapter-name">${chInfo.name || ''} — ${chInfo.sin || ''}</div>
            </div>
            <div class="pb-section-title">출전 파티</div>
            <div class="pb-party">`;

        const slots = [
            { label: '슬롯 1', data: p?.slot_1_info },
            { label: '슬롯 2', data: p?.slot_2_info },
            { label: '슬롯 3', data: p?.slot_3_info },
        ];

        for (const slot of slots) {
            const h = slot.data;
            if (h) {
                const icon = FACTION_ICON[h.faction] || '❓';
                const gc = GRADE_CLASS[h.grade] || '';
                html += `<div class="pb-slot filled">
                    <div class="pb-slot-icon">${icon}</div>
                    <div class="pb-slot-info">
                        <div class="pb-slot-name ${gc}">${h.hero_name || h.hero_id}</div>
                        <div class="pb-slot-meta">Lv.${h.level} · ${h.grade} · ${h.faction}</div>
                    </div>
                </div>`;
            } else {
                html += `<div class="pb-slot empty"><span class="pb-slot-empty">— 비어있음 —</span></div>`;
            }
        }

        html += `</div>`;

        // 시너지 표시
        if (p?.synergy) {
            html += `<div class="pb-synergy">
                <span class="pb-syn-label">${p.synergy.label}</span> ${p.synergy.desc}
            </div>`;
        }

        html += `<div class="pb-actions">
            <button class="btn btn-primary pb-btn-go" data-action="go">출전!</button>
            <button class="btn pb-btn-back" data-action="back">뒤로</button>
        </div></div>`;

        this.el.innerHTML = html;

        this.el.onclick = (e) => {
            const a = e.target.closest('[data-action]')?.dataset?.action;
            if (a === 'go') {
                import('../../main.js').then(m => m.default.switchRightView('battle', { stageId: this._stageId }));
            } else if (a === 'back') {
                import('../../main.js').then(m => m.default.switchRightView('town'));
            }
        };
    },
};

export default PreBattleView;

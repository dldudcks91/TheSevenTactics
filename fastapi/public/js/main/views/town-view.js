/**
 * TheSevenTactics — Town View (림보 거점)
 * 거점 시설 핫스팟 + 출정문 스테이지 선택 팝업
 */
import { Store } from '../../store.js';
import { showToast } from '../../utils.js';
import { getConfigs } from '../../meta-data.js';

/* 챕터 정보 (CSV 없는 경우 폴백) */
const CHAPTERS = [
    { id: 1, sin: '분노', name: '불타는 전장', boss: '사탄', stages: 4 },
    { id: 2, sin: '질투', name: '뒤틀린 숲', boss: '레비아탄', stages: 4 },
    { id: 3, sin: '탐욕', name: '황금 사막', boss: '마몬', stages: 4 },
    { id: 4, sin: '나태', name: '망각의 동토', boss: '벨페고르', stages: 4 },
    { id: 5, sin: '폭식', name: '심연의 동굴', boss: '벨제붑', stages: 4 },
    { id: 6, sin: '색욕', name: '타락한 궁전', boss: '아스모데우스', stages: 4 },
    { id: 7, sin: '교만', name: '천상의 폐허', boss: '루시퍼', stages: 4 },
];

const STAGE_NAMES = ['외곽 탐색', '내부 침투', '핵심부 돌파', '보스전'];

const TownView = {
    el: null,
    _handleEvent: null,
    _popupOpen: false,

    mount(el) {
        this.el = el;

        el.innerHTML = `
            <div class="town-view">
                <div class="tv-bg">
                    <div class="tv-hotspot" data-npc="gate" style="left:40%;top:10%;width:20%;height:15%">
                        <span class="tv-hotspot-label">출정문</span>
                    </div>
                    <div class="tv-hotspot" data-npc="forge" style="left:5%;top:35%;width:18%;height:20%">
                        <span class="tv-hotspot-label">다곤의 대장간</span>
                    </div>
                    <div class="tv-hotspot" data-npc="inn" style="left:75%;top:35%;width:18%;height:20%">
                        <span class="tv-hotspot-label">노인의 객잔</span>
                    </div>
                    <div class="tv-hotspot" data-npc="tavern" style="left:5%;top:65%;width:18%;height:20%">
                        <span class="tv-hotspot-label">선술집</span>
                    </div>
                    <div class="tv-hotspot locked" data-npc="arena" style="left:75%;top:65%;width:18%;height:20%">
                        <span class="tv-hotspot-label">투기장</span>
                    </div>
                </div>
                <div class="tv-stage-overlay" id="tv-stage-overlay">
                    <div class="tv-stage-popup" id="tv-stage-popup"></div>
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
        /* 오버레이 배경 클릭 → 닫기 */
        if (e.target.id === 'tv-stage-overlay') {
            this._closeStagePopup();
            return;
        }

        /* 닫기 버튼 */
        if (e.target.closest('[data-action="close-popup"]')) {
            this._closeStagePopup();
            return;
        }

        /* 챕터 탭 */
        const chBtn = e.target.closest('[data-action="ch-tab"]');
        if (chBtn) {
            const chId = parseInt(chBtn.dataset.ch);
            this._renderChapterStages(chId);
            return;
        }

        /* 스테이지 입장 → 전투 전 설정 화면 */
        const stageBtn = e.target.closest('[data-action="enter-stage"]');
        if (stageBtn) {
            const stageId = parseInt(stageBtn.dataset.stage);
            this._closeStagePopup();
            import('../../main.js').then(m => {
                m.default.switchRightView('prebattle', { stageId });
            });
            return;
        }

        /* 핫스팟 */
        const hotspot = e.target.closest('.tv-hotspot');
        if (!hotspot || this._popupOpen) return;
        if (hotspot.classList.contains('locked')) return;

        const npc = hotspot.dataset.npc;
        import('../../main.js').then(m => {
            const MS = m.default;
            switch (npc) {
                case 'gate':
                    this._openStagePopup();
                    break;
                case 'tavern':
                    MS.switchRightView('tavern');
                    break;
                default:
                    showToast(`${npc} (준비 중)`, 'info');
                    break;
            }
        });
    },

    /* ── 스테이지 선택 팝업 ─── */

    _openStagePopup() {
        this._popupOpen = true;
        const overlay = this.el.querySelector('#tv-stage-overlay');
        overlay.classList.add('show');

        const currentStage = Store.get('user.current_stage') || 101;
        const currentCh = Math.floor(currentStage / 100);

        this._renderStagePopup(currentCh);
    },

    _closeStagePopup() {
        this._popupOpen = false;
        const overlay = this.el.querySelector('#tv-stage-overlay');
        if (overlay) overlay.classList.remove('show');
    },

    _renderStagePopup(selectedCh) {
        const popup = this.el.querySelector('#tv-stage-popup');
        const currentStage = Store.get('user.current_stage') || 101;

        let html = `
            <div class="tv-stage-popup-header" style="position:relative">
                <span class="tv-stage-popup-title">출정 — 스테이지 선택</span>
                <button class="close-x" data-action="close-popup">✕</button>
            </div>
            <div class="tv-stage-popup-chapters">`;

        for (const ch of CHAPTERS) {
            const unlocked = currentStage >= ch.id * 100 + 1;
            const active = ch.id === selectedCh;
            html += `<button class="tv-popup-ch-btn${active ? ' active' : ''}${unlocked ? '' : ' locked'}"
                data-action="${unlocked ? 'ch-tab' : ''}" data-ch="${ch.id}"
                ${unlocked ? '' : 'disabled'}>
                ${ch.id}장 ${ch.sin}
            </button>`;
        }

        html += `</div>`;

        // 챕터 정보
        const ch = CHAPTERS.find(c => c.id === selectedCh);
        if (ch) {
            html += `<div class="tv-stage-popup-info">
                <div class="tv-popup-info-name">${ch.id}장: ${ch.name}</div>
                <div class="tv-popup-info-sin">${ch.sin}(${ch.boss}) — 4스테이지</div>
            </div>`;
        }

        // 스테이지 목록
        html += `<div class="tv-stage-popup-list" id="tv-stage-list">`;
        html += this._buildStageList(selectedCh, currentStage);
        html += `</div>`;

        popup.innerHTML = html;
    },

    _renderChapterStages(chId) {
        // 챕터 탭만 교체
        const currentStage = Store.get('user.current_stage') || 101;

        // 탭 활성화
        this.el.querySelectorAll('.tv-popup-ch-btn').forEach(b => b.classList.remove('active'));
        const activeBtn = this.el.querySelector(`[data-ch="${chId}"]`);
        if (activeBtn) activeBtn.classList.add('active');

        // 챕터 정보 갱신
        const ch = CHAPTERS.find(c => c.id === chId);
        const infoEl = this.el.querySelector('.tv-stage-popup-info');
        if (infoEl && ch) {
            infoEl.innerHTML = `
                <div class="tv-popup-info-name">${ch.id}장: ${ch.name}</div>
                <div class="tv-popup-info-sin">${ch.sin}(${ch.boss}) — 4스테이지</div>`;
        }

        // 스테이지 목록 갱신
        const listEl = this.el.querySelector('#tv-stage-list');
        if (listEl) listEl.innerHTML = this._buildStageList(chId, currentStage);
    },

    _buildStageList(chId, currentStage) {
        let html = '';
        for (let s = 1; s <= 4; s++) {
            const stageId = chId * 100 + s;
            const cleared = stageId < currentStage;
            const unlocked = stageId <= currentStage;
            const isBoss = s === 4;
            const name = STAGE_NAMES[s - 1] || `스테이지 ${s}`;

            html += `<div class="tv-popup-stage${cleared ? ' cleared' : ''}${unlocked ? '' : ' locked'}">
                <div class="tv-popup-stage-left">
                    <div class="tv-popup-stage-name">${chId}-${s}: ${name}</div>
                    <div class="tv-popup-stage-type">${isBoss ? 'BOSS' : '일반'}</div>
                </div>
                <div class="tv-popup-stage-right">
                    ${unlocked
                        ? `${cleared ? '<span class="tv-popup-status cleared">클리어</span>' : ''}
                           <button class="tv-popup-enter" data-action="enter-stage" data-stage="${stageId}">입장</button>`
                        : '<span class="tv-popup-status">잠김</span>'
                    }
                </div>
            </div>`;
        }
        return html;
    },
};

export default TownView;

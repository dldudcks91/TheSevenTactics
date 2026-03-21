/**
 * TheSevenTactics — Stage Select View (대체 스테이지 선택)
 */
import { Store } from '../../store.js';
import MainScreen from '../../main.js';

const CHAPTERS = [
    { id: 1, sin: '분노', region: '불타는 전장', boss: '사탄' },
    { id: 2, sin: '질투', region: '뒤틀린 숲', boss: '레비아탄' },
    { id: 3, sin: '탐욕', region: '황금 사막', boss: '마몬' },
    { id: 4, sin: '나태', region: '망각의 동토', boss: '벨페고르' },
    { id: 5, sin: '폭식', region: '심연의 동굴', boss: '벨제붑' },
    { id: 6, sin: '색욕', region: '타락한 궁전', boss: '아스모데우스' },
    { id: 7, sin: '교만', region: '천상의 폐허', boss: '루시퍼' },
];

const STAGE_NAMES = {
    1: '외곽 탐색', 2: '내부 침투', 3: '핵심부 돌파', 4: '보스전',
};

const StageSelectView = {
    el: null,
    _selectedChapter: 1,

    mount(el) {
        this.el = el;

        el.innerHTML = `
            <div class="ssv-screen">
                <div class="ssv-header">
                    <button class="ssv-back-btn" data-action="back">\u2190 \ub9c8\uc744\ub85c</button>
                    <span class="ssv-title">\uc2a4\ud14c\uc774\uc9c0 \uc120\ud0dd</span>
                </div>
                <div class="ssv-chapter-bar" id="ssv-chapters">
                    ${CHAPTERS.map(ch => `
                        <button class="ssv-chapter-btn ${ch.id === 1 ? 'active' : ''}"
                                data-action="chapter" data-chapter="${ch.id}">
                            ${ch.id}. ${ch.sin}
                        </button>
                    `).join('')}
                </div>
                <div class="ssv-chapter-info" id="ssv-info"></div>
                <div class="ssv-stage-list" id="ssv-list"></div>
            </div>
        `;

        this._handleEvent = this._onEvent.bind(this);
        el.addEventListener('pointerdown', this._handleEvent);

        this._selectedChapter = 1;
        this._renderChapter();
    },

    unmount() {
        if (this._handleEvent && this.el) this.el.removeEventListener('pointerdown', this._handleEvent);
    },

    _onEvent(e) {
        const target = e.target.closest('[data-action]');
        if (!target) return;

        switch (target.dataset.action) {
            case 'back':
                MainScreen.switchRightView('town');
                break;
            case 'chapter':
                this._selectChapter(parseInt(target.dataset.chapter));
                break;
            case 'enter-stage':
                MainScreen.switchRightView('prebattle', { stageId: parseInt(target.dataset.stageId) });
                break;
        }
    },

    _selectChapter(chapterId) {
        const currentStage = Store.get('user.current_stage') || 101;
        const maxChapter = Math.floor((currentStage - 1) / 100) + 1;
        if (chapterId > maxChapter) return;

        this._selectedChapter = chapterId;
        this.el.querySelectorAll('.ssv-chapter-btn').forEach(btn => {
            const ch = parseInt(btn.dataset.chapter);
            btn.classList.toggle('active', ch === chapterId);
            btn.classList.toggle('locked', ch > maxChapter);
        });
        this._renderChapter();
    },

    _renderChapter() {
        const chapter = CHAPTERS.find(c => c.id === this._selectedChapter);
        if (!chapter) return;

        const currentStage = Store.get('user.current_stage') || 101;
        const maxChapter = Math.floor((currentStage - 1) / 100) + 1;

        this.el.querySelectorAll('.ssv-chapter-btn').forEach(btn => {
            btn.classList.toggle('locked', parseInt(btn.dataset.chapter) > maxChapter);
        });

        this.el.querySelector('#ssv-info').innerHTML = `
            <div class="ssv-info-name">${chapter.region}</div>
            <div class="ssv-info-sin">제${chapter.id}장: ${chapter.sin}</div>
            <div class="ssv-info-boss">보스: ${chapter.boss}</div>
        `;

        // 4 stages per chapter
        const stages = [1, 2, 3, 4].map(num => ({
            stageId: chapter.id * 100 + num,
            stageNum: num,
            stageName: `${chapter.id}-${num}: ${STAGE_NAMES[num] || ''}`,
        }));

        this.el.querySelector('#ssv-list').innerHTML = stages.map(stage => {
            const isUnlocked = stage.stageId <= currentStage;
            const isCleared = stage.stageId < currentStage;

            return `
                <div class="ssv-stage-card ${!isUnlocked ? 'locked' : ''} ${isCleared ? 'cleared' : ''}"
                     ${isUnlocked ? `data-action="enter-stage" data-stage-id="${stage.stageId}"` : ''}>
                    <div class="ssv-stage-left">
                        <span class="ssv-stage-name">${stage.stageName}</span>
                        <span class="ssv-stage-type">Stage ${stage.stageNum}</span>
                    </div>
                    <div class="ssv-stage-right">
                        ${isCleared
                            ? '<span class="ssv-status cleared">\u2713 \ud074\ub9ac\uc5b4</span>'
                            : isUnlocked
                                ? `<button class="ssv-enter-btn" data-action="enter-stage" data-stage-id="${stage.stageId}">\uc785\uc7a5</button>`
                                : '<span class="ssv-status">\ud83d\udd12 \uc7a0\uae40</span>'
                        }
                    </div>
                </div>
            `;
        }).join('');
    },
};

export default StageSelectView;

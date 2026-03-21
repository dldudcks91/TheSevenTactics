/**
 * TheSevenTactics — Prologue Scene
 * 5씬 텍스트 내레이션. 회원가입 후 최초 1회만 표시.
 */
import { SceneManager } from '../scene-manager.js';
import story from '../story-data.js';

const PrologueScene = {
    el: null,
    refs: {},
    _sceneIdx: 0,
    _lineIdx: 0,
    _typing: false,
    _typeTimer: null,
    _replayMode: false,

    mount(el, data) {
        this.el = el;
        this._sceneIdx = 0;
        this._lineIdx = 0;
        this._replayMode = data?.replay === true;

        const scenes = story.prologue_scenes;

        el.innerHTML = `
            <div class="prologue-screen" data-action="advance">
                <div class="prologue-particles" id="pro-particles"></div>
                <div class="prologue-header">
                    <span class="prologue-scene-num" id="pro-scene-num">1 / ${scenes.length}</span>
                    <span class="prologue-title" id="pro-title"></span>
                    <button class="prologue-skip" data-action="skip">SKIP</button>
                </div>
                <div class="prologue-body" id="pro-body"></div>
                <div class="prologue-footer">
                    <span class="prologue-hint" id="pro-hint">클릭하여 진행</span>
                </div>
            </div>
        `;

        this.refs = {
            sceneNum: el.querySelector('#pro-scene-num'),
            title: el.querySelector('#pro-title'),
            body: el.querySelector('#pro-body'),
            hint: el.querySelector('#pro-hint'),
        };

        this._handleEvent = this._onEvent.bind(this);
        el.addEventListener('pointerdown', this._handleEvent);
        this._handleKeydown = this._onKeydown.bind(this);
        document.addEventListener('keydown', this._handleKeydown);

        this._createParticles();
        this._renderScene();
    },

    unmount() {
        if (this._handleEvent) this.el.removeEventListener('pointerdown', this._handleEvent);
        if (this._handleKeydown) document.removeEventListener('keydown', this._handleKeydown);
        if (this._typeTimer) clearTimeout(this._typeTimer);
        this.refs = {};
    },

    _onEvent(e) {
        const target = e.target.closest('[data-action]');
        if (!target) return;
        if (target.dataset.action === 'skip') { this._finish(); return; }
        if (target.dataset.action === 'advance') this._advance();
    },

    _onKeydown(e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); this._advance(); }
    },

    _advance() {
        if (this._typing) { this._finishTyping(); return; }
        this._nextLine();
    },

    _renderScene() {
        const scenes = story.prologue_scenes;
        const scene = scenes[this._sceneIdx];
        this._lineIdx = 0;

        this.refs.sceneNum.textContent = `${this._sceneIdx + 1} / ${scenes.length}`;
        this.refs.title.textContent = scene.title;
        this.refs.body.innerHTML = '';
        this.refs.hint.textContent = '클릭하여 진행';

        this._showNextLine();
    },

    _nextLine() {
        const scenes = story.prologue_scenes;
        const scene = scenes[this._sceneIdx];

        if (this._lineIdx < scene.lines.length) {
            this._showNextLine();
        } else {
            this._sceneIdx++;
            if (this._sceneIdx < scenes.length) {
                this._fadeToNextScene();
            } else {
                this._finish();
            }
        }
    },

    _showNextLine() {
        const scenes = story.prologue_scenes;
        const scene = scenes[this._sceneIdx];
        const line = scene.lines[this._lineIdx];
        this._lineIdx++;

        if (!line) {
            const br = document.createElement('div');
            br.className = 'prologue-line prologue-blank';
            this.refs.body.appendChild(br);
            this._scrollToBottom();
            this._nextLine();
            return;
        }

        const lineEl = document.createElement('div');
        lineEl.className = 'prologue-line';
        this.refs.body.appendChild(lineEl);

        this._typing = true;
        this._currentLineEl = lineEl;
        this._currentText = line;
        this._currentCharIdx = 0;
        this._typeNextChar();
    },

    _typeNextChar() {
        if (this._currentCharIdx >= this._currentText.length) {
            this._typing = false;
            this._scrollToBottom();
            return;
        }

        this._currentLineEl.textContent = this._currentText.substring(0, this._currentCharIdx + 1);
        this._currentCharIdx++;
        this._scrollToBottom();
        this._typeTimer = setTimeout(() => this._typeNextChar(), 40);
    },

    _finishTyping() {
        if (this._typeTimer) clearTimeout(this._typeTimer);
        this._currentLineEl.textContent = this._currentText;
        this._typing = false;
        this._scrollToBottom();
    },

    _fadeToNextScene() {
        const body = this.refs.body;
        body.classList.add('prologue-fade-out');
        setTimeout(() => {
            body.classList.remove('prologue-fade-out');
            this._renderScene();
        }, 400);
    },

    _finish() {
        if (this._replayMode) { SceneManager.pop(); return; }
        SceneManager.replace('walking');
    },

    _scrollToBottom() {
        const body = this.refs.body;
        body.scrollTop = body.scrollHeight;
    },

    _createParticles() {
        const container = this.el.querySelector('#pro-particles');
        if (!container) return;
        for (let i = 0; i < 12; i++) {
            const p = document.createElement('div');
            p.className = 'prologue-particle';
            p.style.left = `${10 + Math.random() * 80}%`;
            p.style.bottom = `${Math.random() * 20}%`;
            p.style.animationDelay = `${Math.random() * 5}s`;
            p.style.animationDuration = `${4 + Math.random() * 4}s`;
            container.appendChild(p);
        }
    },
};

export default PrologueScene;

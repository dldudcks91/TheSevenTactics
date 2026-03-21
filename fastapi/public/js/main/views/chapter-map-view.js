/**
 * TheSevenTactics — Chapter Map View (분기 월드맵)
 */
import { Store } from '../../store.js';
import { apiCall } from '../../api.js';
import { showLoading, hideLoading } from '../../utils.js';
import { getChapterMap } from '../../map-data.js';
import MainScreen from '../../main.js';

const CHAPTERS = [
    { id: 1, sin: '분노' },
    { id: 2, sin: '질투' },
    { id: 3, sin: '탐욕' },
    { id: 4, sin: '나태' },
    { id: 5, sin: '폭식' },
    { id: 6, sin: '색욕' },
    { id: 7, sin: '교만' },
];

const ChapterMapView = {
    el: null,
    refs: {},
    _selectedChapter: 1,
    _characterNodeId: null,
    _animating: false,

    mount(el) {
        this.el = el;

        el.innerHTML = `
            <div class="cmap-screen">
                <div class="cmap-header">
                    <button class="cmap-back-btn" data-action="back">\u2190 \ub9c8\uc744\ub85c</button>
                    <div class="cmap-chapter-tabs" id="cmap-tabs"></div>
                </div>
                <div class="cmap-title-bar" id="cmap-title"></div>
                <div class="cmap-container" id="cmap-container">
                    <svg class="cmap-svg" id="cmap-svg"></svg>
                    <div class="cmap-nodes" id="cmap-nodes"></div>
                    <div class="cmap-character" id="cmap-char">
                        <div class="cmap-char-sprite"></div>
                    </div>
                </div>
            </div>
        `;

        this.refs = {
            tabs: el.querySelector('#cmap-tabs'),
            title: el.querySelector('#cmap-title'),
            container: el.querySelector('#cmap-container'),
            svg: el.querySelector('#cmap-svg'),
            nodes: el.querySelector('#cmap-nodes'),
            character: el.querySelector('#cmap-char'),
        };

        this._handleEvent = this._onEvent.bind(this);
        el.addEventListener('pointerdown', this._handleEvent);

        this._selectedChapter = 1;
        this._renderTabs();
        this._renderMap();
    },

    unmount() {
        if (this._handleEvent && this.el) this.el.removeEventListener('pointerdown', this._handleEvent);
        this.refs = {};
    },

    _onEvent(e) {
        const target = e.target.closest('[data-action]');
        if (!target) return;

        switch (target.dataset.action) {
            case 'back':
                MainScreen.switchRightView('town');
                break;
            case 'select-chapter':
                this._selectChapter(parseInt(target.dataset.chapter));
                break;
            case 'node-click':
                this._onNodeClick(target.dataset.nodeId);
                break;
        }
    },

    _renderTabs() {
        const currentStage = Store.get('user.current_stage') || 101;
        const maxChapter = Math.floor((currentStage - 1) / 100) + 1;

        this.refs.tabs.innerHTML = CHAPTERS.map(ch => `
            <button class="cmap-tab ${ch.id === this._selectedChapter ? 'active' : ''} ${ch.id > maxChapter ? 'locked' : ''}"
                    data-action="select-chapter" data-chapter="${ch.id}"
                    ${ch.id > maxChapter ? 'disabled' : ''}>
                ${ch.id}
            </button>
        `).join('');
    },

    _selectChapter(chapterId) {
        const currentStage = Store.get('user.current_stage') || 101;
        const maxChapter = Math.floor((currentStage - 1) / 100) + 1;
        if (chapterId > maxChapter) return;

        this._selectedChapter = chapterId;
        this._renderTabs();
        this._renderMap();
    },

    _renderMap() {
        const mapData = getChapterMap(this._selectedChapter);
        if (!mapData) {
            this.refs.title.textContent = '맵 데이터 없음';
            this.refs.svg.innerHTML = '';
            this.refs.nodes.innerHTML = '';
            return;
        }

        const currentStage = Store.get('user.current_stage') || 101;
        const sinClass = mapData.sin || 'wrath';

        this.refs.title.innerHTML = `
            <span class="cmap-title-sin sin-${sinClass}">제${this._selectedChapter}장</span>
            <span class="cmap-title-name">${mapData.name}</span>
        `;

        this.refs.container.style.backgroundColor = mapData.bgColor || '';
        this.refs.container.dataset.sin = sinClass;

        const nodeStates = this._calcNodeStates(mapData, currentStage);
        this._renderEdges(mapData, nodeStates);
        this._renderNodes(mapData, nodeStates);
        this._placeCharacter(mapData, nodeStates);
    },

    _calcNodeStates(mapData, currentStage) {
        const states = {};
        for (const node of mapData.nodes) {
            if (node.type === 'town') { states[node.id] = 'completed'; continue; }
            if (node.stageId < currentStage) states[node.id] = 'completed';
            else if (node.stageId === currentStage) states[node.id] = 'unlocked';
            else states[node.id] = 'locked';
        }

        for (const node of mapData.nodes) {
            if (states[node.id] !== 'unlocked') continue;
            const predecessors = mapData.edges.filter(e => e.to === node.id).map(e => e.from);
            if (predecessors.length > 0 && !predecessors.some(pid => states[pid] === 'completed')) {
                states[node.id] = 'locked';
            }
        }
        return states;
    },

    _renderEdges(mapData, nodeStates) {
        const nodeMap = {};
        for (const n of mapData.nodes) nodeMap[n.id] = n;

        const lines = mapData.edges.map(edge => {
            const from = nodeMap[edge.from];
            const to = nodeMap[edge.to];
            if (!from || !to) return '';

            const isActive = nodeStates[edge.from] === 'completed';
            const cls = isActive ? 'cmap-edge active' : 'cmap-edge';
            const dx = to.x - from.x;
            const dy = to.y - from.y;

            if (Math.abs(dy) > 10) {
                const cx1 = from.x + dx * 0.4, cy1 = from.y;
                const cx2 = from.x + dx * 0.6, cy2 = to.y;
                return `<path class="${cls}" d="M ${from.x} ${from.y} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${to.x} ${to.y}" />`;
            }
            return `<line class="${cls}" x1="${from.x}" y1="${from.y}" x2="${to.x}" y2="${to.y}" />`;
        }).join('');

        this.refs.svg.setAttribute('viewBox', '0 0 100 100');
        this.refs.svg.setAttribute('preserveAspectRatio', 'none');
        this.refs.svg.innerHTML = lines;
    },

    _renderNodes(mapData, nodeStates) {
        this.refs.nodes.innerHTML = mapData.nodes.map(node => {
            const state = nodeStates[node.id];
            const isClickable = state === 'unlocked' || state === 'completed';
            const icons = { town: '\ud83c\udfe0', hunt: '\u2694\ufe0f', boss: '\ud83d\udc80' };

            return `
                <div class="cmap-node cmap-node-${node.type} cmap-state-${state}"
                     style="left:${node.x}%;top:${node.y}%"
                     ${isClickable ? `data-action="node-click" data-node-id="${node.id}"` : ''}
                     title="${node.name}">
                    <div class="cmap-node-icon">${icons[node.type] || '\u25cf'}</div>
                    <div class="cmap-node-label">${node.name}</div>
                    ${state === 'completed' ? '<div class="cmap-node-check">\u2713</div>' : ''}
                    ${state === 'locked' ? '<div class="cmap-node-lock">\ud83d\udd12</div>' : ''}
                </div>
            `;
        }).join('');
    },

    _placeCharacter(mapData, nodeStates) {
        let targetNode = mapData.nodes.find(n => nodeStates[n.id] === 'unlocked')
            || [...mapData.nodes].reverse().find(n => nodeStates[n.id] === 'completed')
            || mapData.nodes[0];

        this._characterNodeId = targetNode.id;
        this._moveCharacterTo(targetNode.x, targetNode.y, false);
    },

    _moveCharacterTo(x, y, animate = true) {
        const char = this.refs.character;
        if (animate) char.classList.add('cmap-char-moving');
        else char.classList.remove('cmap-char-moving');
        char.style.left = `${x}%`;
        char.style.top = `${y}%`;
    },

    _onNodeClick(nodeId) {
        if (this._animating) return;
        const mapData = getChapterMap(this._selectedChapter);
        if (!mapData) return;
        const node = mapData.nodes.find(n => n.id === nodeId);
        if (!node || !node.stageId) return;

        if (this._characterNodeId !== nodeId) {
            this._animating = true;
            this._moveCharacterTo(node.x, node.y, true);
            this._characterNodeId = nodeId;
            setTimeout(() => {
                this._animating = false;
                this._enterStage(node.stageId);
            }, 400);
        } else {
            this._enterStage(node.stageId);
        }
    },

    async _enterStage(stageId) {
        MainScreen.switchRightView('prebattle', { stageId });
    },
};

export default ChapterMapView;

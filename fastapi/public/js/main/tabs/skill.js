/**
 * TheSevenTactics — Skill Tree Tab
 * 영웅 선택 → 2개 스킬트리 시각화 + 포인트 배분
 */
import { apiCall } from '../../api.js';
import { showToast } from '../../utils.js';

const TREE_LABEL = {
    wrath: '분노', envy: '질투', greed: '탐욕',
    sloth: '나태', gluttony: '폭식', lust: '색욕', pride: '교만',
};

const SkillTab = {
    el: null,
    _heroes: [],
    _selectedUid: null,
    _detail: null,
    _handleEvent: null,

    mount(el) {
        this.el = el;
        el.innerHTML = '<div class="skill-tab"><div class="skill-empty">로딩 중...</div></div>';
        this._handleEvent = this._onEvent.bind(this);
        el.addEventListener('pointerdown', this._handleEvent);
        this._load();
    },

    unmount() {
        if (this._handleEvent) {
            this.el.removeEventListener('pointerdown', this._handleEvent);
        }
    },

    async _load() {
        const result = await apiCall(4001, {});
        if (result?.success) {
            this._heroes = result.data.heroes || [];
            if (this._heroes.length && !this._selectedUid) {
                this._selectedUid = this._heroes[0].hero_uid;
            }
            if (this._selectedUid) {
                await this._loadDetail(this._selectedUid);
            } else {
                this._render();
            }
        }
    },

    async _loadDetail(heroUid) {
        const result = await apiCall(4002, { hero_uid: heroUid });
        if (result?.success) {
            this._detail = result.data;
            this._render();
        }
    },

    _render() {
        if (!this._heroes.length) {
            this.el.innerHTML = '<div class="skill-tab"><div class="skill-empty">보유한 영웅이 없습니다</div></div>';
            return;
        }

        const d = this._detail;
        let html = '<div class="skill-tab">';

        // 영웅 선택 버튼
        html += '<div class="skill-hero-select">';
        for (const h of this._heroes) {
            const active = h.hero_uid === this._selectedUid ? ' active' : '';
            html += `<button class="skill-hero-btn${active}" data-action="pick-hero" data-uid="${h.hero_uid}">${h.hero_name}</button>`;
        }
        html += '</div>';

        if (!d) {
            html += '<div class="skill-empty">영웅을 선택하세요</div></div>';
            this.el.innerHTML = html;
            return;
        }

        // 스킬 포인트 잔여
        const spUsed1 = this._countPoints(d.tree1_points);
        const spUsed2 = this._countPoints(d.tree2_points);
        const spTotal = d.level || 1;
        const spRemain = spTotal - spUsed1 - spUsed2;
        html += `<div class="skill-hero-sp">스킬 포인트: ${spRemain} / ${spTotal}</div>`;

        // 스킬트리 2개
        html += '<div class="skill-trees">';
        html += this._renderTree(1, d.skill_tree_1, d.skill_trees.tree1, d.tree1_points, d.hero_uid, spRemain);
        html += this._renderTree(2, d.skill_tree_2, d.skill_trees.tree2, d.tree2_points, d.hero_uid, spRemain);
        html += '</div>';

        html += '</div>';
        this.el.innerHTML = html;
    },

    _renderTree(treeNum, treeId, skills, points, heroUid, spRemain) {
        const label = TREE_LABEL[treeId] || treeId;
        const pts = points || {};
        const totalInvested = this._countPoints(pts);

        let html = `<div class="skill-tree-panel">`;
        html += `<div class="skill-tree-header">
            <span class="skill-tree-name ${treeId}">${label}(${treeId.toUpperCase()}) 트리</span>
            <span class="skill-tree-total">투자: ${totalInvested}pt</span>
        </div>`;
        html += '<div class="skill-list">';

        if (!skills || !skills.length) {
            html += '<div class="skill-empty">스킬 데이터 없음</div>';
        } else {
            for (const sk of skills) {
                const curLv = pts[sk.skill_id] || 0;
                const maxLv = parseInt(sk.max_level || 5);
                const isMax = curLv >= maxLv;
                const cost = parseInt(sk.cost_per_level || 1);
                const canInvest = !isMax && spRemain >= cost;

                html += `<div class="skill-item${isMax ? ' maxed' : ''}">`;
                html += `<div class="skill-item-info">
                    <div class="skill-item-name">${sk.skill_name}</div>
                    <div class="skill-item-desc">${sk.skill_desc || ''}</div>
                    <div class="skill-item-effect">${sk.per_level_effect || ''}</div>
                </div>`;
                html += '<div class="skill-item-right">';

                // 레벨 핍
                html += '<div class="skill-level-pips">';
                for (let i = 0; i < maxLv; i++) {
                    html += `<div class="skill-pip${i < curLv ? ' filled' : ''}"></div>`;
                }
                html += '</div>';

                // 투자 버튼
                if (!isMax) {
                    html += `<button class="skill-invest-btn" data-action="invest"
                        data-hero-uid="${heroUid}" data-tree-num="${treeNum}" data-skill-id="${sk.skill_id}"
                        ${canInvest ? '' : 'disabled'}>+${cost}</button>`;
                }

                html += '</div></div>';
            }
        }

        html += '</div></div>';
        return html;
    },

    _countPoints(pts) {
        if (!pts) return 0;
        return Object.values(pts).reduce((sum, v) => sum + (v || 0), 0);
    },

    _onEvent(e) {
        const pick = e.target.closest('[data-action="pick-hero"]');
        if (pick) {
            const uid = parseInt(pick.dataset.uid);
            if (uid !== this._selectedUid) {
                this._selectedUid = uid;
                this._loadDetail(uid);
            }
            return;
        }

        const invest = e.target.closest('[data-action="invest"]');
        if (invest && !invest.disabled) {
            this._investSkill(
                parseInt(invest.dataset.heroUid),
                parseInt(invest.dataset.treeNum),
                invest.dataset.skillId
            );
        }
    },

    async _investSkill(heroUid, treeNum, skillId) {
        const result = await apiCall(4003, { hero_uid: heroUid, tree_num: treeNum, skill_id: skillId });
        if (result?.success) {
            showToast(result.message, 'success');
            await this._loadDetail(heroUid);
        }
    },
};

export default SkillTab;

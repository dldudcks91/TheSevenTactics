/**
 * TheSevenTactics — Town View (림보 거점)
 * 거점 시설 핫스팟 배치
 */

const TownView = {
    el: null,

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
                    <div class="tv-hotspot locked" data-npc="tavern" style="left:5%;top:65%;width:18%;height:20%">
                        <span class="tv-hotspot-label">선술집</span>
                    </div>
                    <div class="tv-hotspot locked" data-npc="arena" style="left:75%;top:65%;width:18%;height:20%">
                        <span class="tv-hotspot-label">투기장</span>
                    </div>
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
        const hotspot = e.target.closest('.tv-hotspot');
        if (!hotspot) return;

        if (hotspot.classList.contains('locked')) return;

        const npc = hotspot.dataset.npc;
        console.log(`[TownView] NPC 클릭: ${npc}`);
        // TODO: Phase 3~4에서 NPC별 상호작용 구현
    },
};

export default TownView;

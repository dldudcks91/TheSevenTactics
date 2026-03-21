/**
 * TheSevenTactics — Chapter Map Data
 * 챕터별 분기 월드맵 노드 & 엣지 정의
 */

function buildChapterMaps() {
    return {
        1: {
            name: '불타는 전장',
            sin: 'wrath',
            bgColor: '#1a0808',
            nodes: [
                { id: 'start',     type: 'town', x: 8,  y: 50, name: '림보' },
                { id: 'stage_101', type: 'hunt', x: 28, y: 50, name: '전초 기지',     stageId: 101 },
                { id: 'stage_102', type: 'hunt', x: 50, y: 24, name: '전쟁터 상단',   stageId: 102 },
                { id: 'stage_105', type: 'hunt', x: 50, y: 76, name: '전쟁터 하단',   stageId: 102 },
                { id: 'stage_103', type: 'hunt', x: 72, y: 50, name: '묘지',           stageId: 103 },
                { id: 'stage_104', type: 'boss', x: 92, y: 50, name: '분노의 문',     stageId: 104 },
            ],
            edges: [
                { from: 'start',     to: 'stage_101' },
                { from: 'stage_101', to: 'stage_102' },
                { from: 'stage_101', to: 'stage_105' },
                { from: 'stage_102', to: 'stage_103' },
                { from: 'stage_105', to: 'stage_103' },
                { from: 'stage_103', to: 'stage_104' },
            ],
        },
        2: {
            name: '뒤틀린 숲',
            sin: 'envy',
            bgColor: '#081a0a',
            nodes: [
                { id: 'start',     type: 'town', x: 8,  y: 50, name: '림보' },
                { id: 'stage_201', type: 'hunt', x: 28, y: 50, name: '숲 입구',       stageId: 201 },
                { id: 'stage_202', type: 'hunt', x: 50, y: 30, name: '독안개 늪',     stageId: 202 },
                { id: 'stage_205', type: 'hunt', x: 50, y: 70, name: '뒤틀린 뿌리',   stageId: 202 },
                { id: 'stage_203', type: 'hunt', x: 72, y: 50, name: '심연의 호수',   stageId: 203 },
                { id: 'stage_204', type: 'boss', x: 92, y: 50, name: '질투의 심장',   stageId: 204 },
            ],
            edges: [
                { from: 'start',     to: 'stage_201' },
                { from: 'stage_201', to: 'stage_202' },
                { from: 'stage_201', to: 'stage_205' },
                { from: 'stage_202', to: 'stage_203' },
                { from: 'stage_205', to: 'stage_203' },
                { from: 'stage_203', to: 'stage_204' },
            ],
        },
    };
}

export function getChapterMap(chapterId) {
    const maps = buildChapterMaps();
    return maps[chapterId] || null;
}

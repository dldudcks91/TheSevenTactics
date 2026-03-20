# TheSevenTactics - 아트 디자인 문서

> 최종 업데이트: 2026-03-20

---

## 1. 아트 컨셉

- **스타일**: 16-bit 도트(픽셀 아트)
- **톤**: 다크 판타지, 고딕
- **참고**: 파이널 판타지 6, 택틱스 오우거, 로맨싱 사가 시리즈

---

## 2. 카드 일러스트 규격

| 항목 | 사양 |
|------|------|
| 해상도 | 64×64px (원본), 게임 내 2~4배 스케일 |
| 스타일 | 16-bit 픽셀 아트 (SNES 시대 도트) |
| 구도 | 얼굴 또는 상반신 초상화 (face/bust portrait) |
| 배경 | 단색 (진영별 컬러) |
| 테두리 | 없음 (게임 UI에서 등급 프레임 오버레이) |
| 팔레트 제한 | 캐릭터당 최대 16색 |

---

## 3. 진영별 컬러 팔레트

| 진영 | 주요 컬러 | 보조 컬러 | 분위기 |
|------|----------|----------|--------|
| **악마** | 검정, 짙은 적색 (#8B0000) | 주황, 자주 | 지옥불, 타락, 어둠 |
| **인간** | 강철색, 갈색 (#8B7355) | 금색, 흰색 | 전장, 기사, 생존 |
| **천상** | 황금, 순백 (#FFD700) | 하늘색, 연보라 | 신성, 빛, 심판 |

---

## 4. 등급별 카드 프레임

| 등급 | 프레임 색상 | 효과 |
|------|-----------|------|
| Common | 회색 (#808080) | 단순 1px 테두리 |
| Uncommon | 초록 (#228B22) | 1px 테두리 + 모서리 장식 |
| Rare | 파랑 (#4169E1) | 2px 테두리 + 모서리 보석 |
| Legendary | 금색 (#FFD700) | 2px 테두리 + 빛나는 모서리 + 후광 |

---

## 5. 7죄종 컬러 모티프

| 죄종 | 컬러 | 시각 모티프 |
|------|------|-----------|
| 분노 (Wrath) | 붉은색 | 불꽃, 균열 |
| 나태 (Sloth) | 보라색 | 안개, 거미줄 |
| 탐욕 (Greed) | 금색 | 동전, 보석 |
| 질투 (Envy) | 녹색 | 뱀, 독 |
| 폭식 (Gluttony) | 주황색 | 이빨, 피 |
| 색욕 (Lust) | 분홍색 | 장미, 가시 |
| 교만 (Pride) | 흰색/은색 | 왕관, 거울 |

---

## 6. 이미지 생성 프롬프트 가이드

Stable Diffusion (HuggingFace Inference API) 사용 시 공통 프롬프트:

```
공통 접두사: "16-bit pixel art, SNES style sprite, retro RPG character portrait"
공통 접미사: "limited color palette, clean pixels, no anti-aliasing, black background"
```

### 진영별 프롬프트 키워드

- **악마**: `demon, dark horns, glowing red eyes, hellfire, crimson and black palette`
- **인간**: `human warrior, steel armor, battle scars, brown and silver palette`
- **천상**: `angelic being, golden halo, white wings, gold and white palette`

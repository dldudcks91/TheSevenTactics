import math
import random
import logging
from database import SessionLocal
from models import User, UserStat, Hero, Party
from services.system.GameDataManager import GameDataManager
from services.system.ErrorCode import ErrorCode, error_response

logger = logging.getLogger("RPG_SERVER")

# 전투 상수
BASE_HP_PER_VIT = 5
BASE_ATK_PER_STR = 2
BASE_MATK_PER_INT = 2
BASE_ACTION_SPEED = 10  # 기본 행동력 회복 /초
ACTION_PER_AGI = 0.3
BASE_DEF_PER_VIT = 0.5
CRIT_BASE = 5  # 기본 치명타 확률 %
CRIT_PER_AGI = 0.5


class BattleManager:
    """3v3 파티 자동전투 시뮬레이션 (API 3xxx)"""

    @classmethod
    async def battle_start(cls, user_no: int, data: dict):
        """API 3001: 전투 시작 (스테이지 진입 + 전투 시뮬레이션 + 결과 반환)"""
        stage_id = data.get("stage_id")
        if not stage_id:
            return error_response(ErrorCode.INVALID_REQUEST, "stage_id가 필요합니다.")

        # 스테이지 메타 확인
        stages = GameDataManager.REQUIRE_CONFIGS.get("stages", {})
        stage_meta = stages.get(stage_id) or stages.get(str(stage_id))
        if not stage_meta:
            return error_response(ErrorCode.STAGE_NOT_FOUND, f"스테이지 {stage_id}을(를) 찾을 수 없습니다.")

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.user_no == user_no).first()
            if not user:
                return error_response(ErrorCode.USER_NOT_FOUND, "유저를 찾을 수 없습니다.")

            stat = db.query(UserStat).filter(UserStat.user_no == user_no).first()
            if not stat:
                return error_response(ErrorCode.USER_NOT_FOUND, "유저 스탯 없음")

            # 파티 구성
            party = db.query(Party).filter(Party.user_no == user_no).first()
            if not party:
                return error_response(ErrorCode.INVALID_REQUEST, "파티가 편성되지 않았습니다.")

            # 아군 유닛 생성
            allies = []
            for slot_uid in [party.slot_1, party.slot_2, party.slot_3]:
                if slot_uid is None:
                    continue
                hero = db.query(Hero).filter(Hero.hero_uid == slot_uid, Hero.user_no == user_no).first()
                if hero:
                    unit = cls._build_ally_unit(hero, stat)
                    allies.append(unit)

            if not allies:
                return error_response(ErrorCode.INVALID_REQUEST, "파티에 영웅이 없습니다.")

            # 적 유닛 생성
            enemies = cls._build_enemies(stage_meta)

            # 전투 시뮬레이션
            battle_log, result = cls._simulate_battle(allies, enemies)

            # 보상 계산
            rewards = {"exp": 0, "gold": 0}
            if result == "victory":
                rewards["exp"] = len(enemies) * 50 * int(str(stage_id)[:1])  # 챕터 번호 비례
                rewards["gold"] = len(enemies) * 30 * int(str(stage_id)[:1])

                # 경험치/골드 지급
                stat.exp += rewards["exp"]
                user.gold += rewards["gold"]

                # 레벨업 체크
                level_config = GameDataManager.REQUIRE_CONFIGS.get("level_config", {})
                leveled_up = False
                while True:
                    lv_data = level_config.get(stat.level)
                    if not lv_data:
                        break
                    required = lv_data.get("required_exp", stat.level * 1000)
                    if stat.exp >= required:
                        stat.exp -= required
                        stat.level += 1
                        stat.stat_points += lv_data.get("stat_points", 5)
                        leveled_up = True
                    else:
                        break

                # 스테이지 진행 업데이트
                if int(stage_id) >= user.current_stage:
                    user.current_stage = int(stage_id) + 1

                db.commit()

            return {
                "success": True,
                "message": "승리!" if result == "victory" else "패배...",
                "data": {
                    "result": result,
                    "battle_log": battle_log[-20:],  # 최근 20턴만
                    "rewards": rewards,
                    "user": {
                        "level": stat.level,
                        "exp": stat.exp,
                        "gold": user.gold,
                        "stat_points": stat.stat_points,
                        "current_stage": user.current_stage,
                    },
                },
            }
        except Exception as e:
            db.rollback()
            logger.error(f"[BattleManager] battle_start 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "전투 처리 중 오류가 발생했습니다.")
        finally:
            db.close()

    # ── 유닛 빌드 ──

    @classmethod
    def _build_ally_unit(cls, hero: Hero, user_stat: UserStat) -> dict:
        hero_base = GameDataManager.REQUIRE_CONFIGS.get("hero_bases", {}).get(hero.hero_id, {})

        base_str = int(hero_base.get("base_str", 10))
        base_int = int(hero_base.get("base_int", 10))
        base_agi = int(hero_base.get("base_agi", 10))
        base_vit = int(hero_base.get("base_vit", 10))
        base_will = int(hero_base.get("base_will", 10))

        # 레벨 보정
        lv = hero.level
        total_str = base_str + lv * 2
        total_int = base_int + lv * 2
        total_agi = base_agi + lv * 2
        total_vit = base_vit + lv * 2

        # 의지 보정 (본캐 스탯 기반)
        will_bonus = 1.0 + user_stat.stat_will * 0.005

        # 등급 배율
        grade_mult = {"common": 1.0, "uncommon": 1.15, "rare": 1.3, "legendary": 1.5}
        mult = grade_mult.get(hero.grade, 1.0) * will_bonus

        hp = int(total_vit * BASE_HP_PER_VIT * mult)
        atk = int(total_str * BASE_ATK_PER_STR * mult)
        matk = int(total_int * BASE_MATK_PER_INT * mult)
        defense = int(total_vit * BASE_DEF_PER_VIT * mult)
        speed = BASE_ACTION_SPEED + total_agi * ACTION_PER_AGI
        crit = CRIT_BASE + total_agi * CRIT_PER_AGI

        return {
            "name": hero_base.get("hero_name", hero.hero_id),
            "side": "ally",
            "hp": hp,
            "max_hp": hp,
            "atk": max(atk, matk),
            "defense": defense,
            "speed": speed,
            "crit": min(crit, 80),
            "action_gauge": 0,
            "alive": True,
        }

    @classmethod
    def _build_enemies(cls, stage_meta: dict) -> list:
        monsters = GameDataManager.REQUIRE_CONFIGS.get("monsters", {})
        waves = stage_meta.get("waves", {})
        enemies = []

        for wave_num, monster_idx in waves.items():
            monster = monsters.get(int(monster_idx)) or monsters.get(str(monster_idx))
            if monster:
                enemies.append({
                    "name": monster.get("name", f"몬스터#{monster_idx}"),
                    "side": "enemy",
                    "hp": int(float(monster.get("base_hp", 100))),
                    "max_hp": int(float(monster.get("base_hp", 100))),
                    "atk": int(float(monster.get("base_atk", 20))),
                    "defense": int(float(monster.get("base_def", 5))),
                    "speed": 10 + float(monster.get("atk_speed", 1.0)) * 3,
                    "crit": 5,
                    "action_gauge": 0,
                    "alive": True,
                })

        # 몬스터 메타 없으면 기본 적 생성
        if not enemies:
            for i in range(3):
                enemies.append({
                    "name": f"적 {i+1}",
                    "side": "enemy",
                    "hp": 80, "max_hp": 80,
                    "atk": 15, "defense": 3,
                    "speed": 10, "crit": 5,
                    "action_gauge": 0, "alive": True,
                })

        return enemies

    # ── 전투 시뮬레이션 ──

    @classmethod
    def _simulate_battle(cls, allies: list, enemies: list, max_turns: int = 50) -> tuple:
        """턴제 자동전투. (battle_log, 'victory'|'defeat') 반환"""
        all_units = allies + enemies
        battle_log = []
        turn = 0

        while turn < max_turns:
            turn += 1

            # 행동 게이지 충전
            for unit in all_units:
                if unit["alive"]:
                    unit["action_gauge"] += unit["speed"]

            # 행동 게이지 100 이상인 유닛 행동 (속도순)
            actors = sorted(
                [u for u in all_units if u["alive"] and u["action_gauge"] >= 100],
                key=lambda u: u["action_gauge"],
                reverse=True
            )

            for actor in actors:
                if not actor["alive"]:
                    continue

                actor["action_gauge"] -= 100

                # 타겟 선택 (적 진영 중 HP 가장 낮은 생존자)
                if actor["side"] == "ally":
                    targets = [u for u in enemies if u["alive"]]
                else:
                    targets = [u for u in allies if u["alive"]]

                if not targets:
                    break

                target = min(targets, key=lambda t: t["hp"])

                # 데미지 계산
                is_crit = random.random() * 100 < actor["crit"]
                raw_dmg = max(1, actor["atk"] - target["defense"])
                if is_crit:
                    raw_dmg = int(raw_dmg * 1.5)

                target["hp"] = max(0, target["hp"] - raw_dmg)

                log_entry = {
                    "turn": turn,
                    "actor": actor["name"],
                    "target": target["name"],
                    "damage": raw_dmg,
                    "crit": is_crit,
                    "target_hp": target["hp"],
                }
                battle_log.append(log_entry)

                if target["hp"] <= 0:
                    target["alive"] = False

                # 승패 체크
                if not any(u["alive"] for u in enemies):
                    return battle_log, "victory"
                if not any(u["alive"] for u in allies):
                    return battle_log, "defeat"

        # 턴 초과 = 패배
        return battle_log, "defeat"

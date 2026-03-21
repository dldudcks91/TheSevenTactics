import random
import logging
from datetime import datetime, timedelta
from database import SessionLocal
from models import User, Hero, Tavern
from services.system.GameDataManager import GameDataManager
from services.system.ErrorCode import ErrorCode, error_response

logger = logging.getLogger("RPG_SERVER")

SKILL_TREE_IDS = ["wrath", "envy", "greed", "sloth", "gluttony", "lust", "pride"]


class TavernManager:
    """선술집 — 영웅 방문/영입/거절 (API 5xxx)"""

    @classmethod
    async def get_tavern(cls, user_no: int, data: dict):
        """API 5001: 선술집 현재 상태 조회"""
        db = SessionLocal()
        try:
            tavern = db.query(Tavern).filter(Tavern.user_no == user_no).first()

            # 최초 방문 — Tavern 행 생성
            if not tavern:
                tavern = Tavern(user_no=user_no)
                db.add(tavern)
                db.commit()

            # 만료된 영웅 제거
            if tavern.hero_id and tavern.expires_at and datetime.utcnow() > tavern.expires_at:
                tavern.hero_id = None
                tavern.grade = None
                tavern.faction = None
                tavern.skill_tree_1 = None
                tavern.skill_tree_2 = None
                tavern.passive_id = None
                tavern.active_id = None
                tavern.arrived_at = None
                tavern.expires_at = None
                db.commit()

            # 비어있으면 새 영웅 생성
            if not tavern.hero_id:
                cls._generate_visitor(tavern)
                db.commit()

            hero_base = cls._get_hero_base(tavern.hero_id) if tavern.hero_id else None
            recruit_cost = cls._get_recruit_cost(tavern.grade) if tavern.grade else 0

            return {
                "success": True,
                "message": "선술집 조회",
                "data": {
                    "has_visitor": tavern.hero_id is not None,
                    "hero_id": tavern.hero_id,
                    "hero_name": hero_base.get("hero_name", tavern.hero_id) if hero_base else None,
                    "grade": tavern.grade,
                    "faction": tavern.faction,
                    "skill_tree_1": tavern.skill_tree_1,
                    "skill_tree_2": tavern.skill_tree_2,
                    "passive_name": hero_base.get("passive_name", "") if hero_base else "",
                    "active_name": hero_base.get("active_name", "") if hero_base else "",
                    "recruit_cost": recruit_cost,
                    "expires_at": tavern.expires_at.isoformat() if tavern.expires_at else None,
                },
            }
        except Exception as e:
            logger.error(f"[TavernManager] get_tavern 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "선술집 조회 중 오류가 발생했습니다.")
        finally:
            db.close()

    @classmethod
    async def recruit_hero(cls, user_no: int, data: dict):
        """API 5002: 영웅 영입"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.user_no == user_no).with_for_update().first()
            if not user:
                return error_response(ErrorCode.USER_NOT_FOUND, "유저를 찾을 수 없습니다.")

            tavern = db.query(Tavern).filter(Tavern.user_no == user_no).with_for_update().first()
            if not tavern or not tavern.hero_id:
                return error_response(ErrorCode.INVALID_REQUEST, "선술집에 영웅이 없습니다.")

            # 이미 보유한 영웅인지 확인
            existing = db.query(Hero).filter(
                Hero.user_no == user_no,
                Hero.hero_id == tavern.hero_id
            ).first()
            if existing:
                return error_response(ErrorCode.INVALID_REQUEST, "이미 보유한 영웅입니다.")

            # 골드 확인
            recruit_cost = cls._get_recruit_cost(tavern.grade)
            if user.gold < recruit_cost:
                return error_response(ErrorCode.INSUFFICIENT_GOLD,
                                      f"골드가 부족합니다. (필요: {recruit_cost}, 보유: {user.gold})")

            # 영입 실행
            user.gold -= recruit_cost

            hero_base = cls._get_hero_base(tavern.hero_id)

            new_hero = Hero(
                user_no=user_no,
                hero_id=tavern.hero_id,
                job=hero_base.get("job", "warrior") if hero_base else "warrior",
                grade=tavern.grade,
                faction=tavern.faction,
                skill_tree_1=tavern.skill_tree_1,
                skill_tree_2=tavern.skill_tree_2,
                tree1_points={},
                tree2_points={},
                passive_id=tavern.passive_id or (hero_base.get("passive_id") if hero_base else None),
                active_id=tavern.active_id or (hero_base.get("active_id") if hero_base else None),
            )
            db.add(new_hero)
            db.flush()

            # 선술집 비우기
            tavern.hero_id = None
            tavern.grade = None
            tavern.faction = None
            tavern.skill_tree_1 = None
            tavern.skill_tree_2 = None
            tavern.passive_id = None
            tavern.active_id = None
            tavern.arrived_at = None
            tavern.expires_at = None

            db.commit()

            logger.info(f"[TavernManager] 영웅 영입 (user={user_no}, hero={new_hero.hero_id}, grade={new_hero.grade}, cost={recruit_cost})")

            return {
                "success": True,
                "message": f"{hero_base.get('hero_name', new_hero.hero_id) if hero_base else new_hero.hero_id} 영입 완료!",
                "data": {
                    "hero_uid": new_hero.hero_uid,
                    "hero_id": new_hero.hero_id,
                    "grade": new_hero.grade,
                    "faction": new_hero.faction,
                    "gold": user.gold,
                    "recruit_cost": recruit_cost,
                },
            }
        except Exception as e:
            db.rollback()
            logger.error(f"[TavernManager] recruit_hero 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "영웅 영입 중 오류가 발생했습니다.")
        finally:
            db.close()

    @classmethod
    async def dismiss_visitor(cls, user_no: int, data: dict):
        """API 5003: 방문 영웅 거절 (다음 영웅 대기)"""
        db = SessionLocal()
        try:
            tavern = db.query(Tavern).filter(Tavern.user_no == user_no).first()
            if not tavern or not tavern.hero_id:
                return error_response(ErrorCode.INVALID_REQUEST, "선술집에 영웅이 없습니다.")

            tavern.hero_id = None
            tavern.grade = None
            tavern.faction = None
            tavern.skill_tree_1 = None
            tavern.skill_tree_2 = None
            tavern.passive_id = None
            tavern.active_id = None
            tavern.arrived_at = None
            tavern.expires_at = None

            db.commit()

            return {
                "success": True,
                "message": "영웅을 돌려보냈습니다.",
                "data": {},
            }
        except Exception as e:
            db.rollback()
            logger.error(f"[TavernManager] dismiss_visitor 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "선술집 처리 중 오류가 발생했습니다.")
        finally:
            db.close()

    # ── 헬퍼 ──

    @classmethod
    def _generate_visitor(cls, tavern: Tavern):
        """랜덤 영웅을 선술집에 배치"""
        config = GameDataManager.REQUIRE_CONFIGS.get("tavern_config", {})
        hero_bases = GameDataManager.REQUIRE_CONFIGS.get("hero_bases", {})

        if not hero_bases:
            return

        # 등급 결정
        grade_weights = {
            "common": float(config.get("grade_common_weight", {}).get("value", 50)),
            "uncommon": float(config.get("grade_uncommon_weight", {}).get("value", 30)),
            "rare": float(config.get("grade_rare_weight", {}).get("value", 15)),
            "legendary": float(config.get("grade_legendary_weight", {}).get("value", 5)),
        }
        grade = random.choices(
            list(grade_weights.keys()),
            weights=list(grade_weights.values()),
            k=1
        )[0]

        # 영웅 결정 (바알 제외)
        eligible = [hid for hid in hero_bases if hid != "baal"]
        if not eligible:
            return

        hero_id = random.choice(eligible)
        hero_base = hero_bases[hero_id]

        # 스킬트리 2개 랜덤 배정
        trees = random.sample(SKILL_TREE_IDS, 2)

        duration = int(config.get("visit_duration_minutes", {}).get("value", 120))
        now = datetime.utcnow()

        tavern.hero_id = hero_id
        tavern.grade = grade
        tavern.faction = hero_base.get("faction", "demon")
        tavern.skill_tree_1 = trees[0]
        tavern.skill_tree_2 = trees[1]
        tavern.passive_id = hero_base.get("passive_id")
        tavern.active_id = hero_base.get("active_id")
        tavern.arrived_at = now
        tavern.expires_at = now + timedelta(minutes=duration)

    @staticmethod
    def _get_hero_base(hero_id: str):
        return GameDataManager.REQUIRE_CONFIGS.get("hero_bases", {}).get(hero_id)

    @staticmethod
    def _get_recruit_cost(grade: str) -> int:
        config = GameDataManager.REQUIRE_CONFIGS.get("tavern_config", {})
        key = f"recruit_cost_{grade}"
        entry = config.get(key, {})
        return int(entry.get("value", 500))

import logging
from database import SessionLocal
from models import User, Hero, Party
from services.system.GameDataManager import GameDataManager
from services.system.ErrorCode import ErrorCode, error_response

logger = logging.getLogger("RPG_SERVER")


class PartyManager:
    """파티 편성/변경/조회 (API 6xxx)"""

    @classmethod
    async def get_party(cls, user_no: int, data: dict):
        """API 6001: 파티 편성 조회"""
        db = SessionLocal()
        try:
            party = db.query(Party).filter(Party.user_no == user_no).first()

            if not party:
                party = Party(user_no=user_no)
                db.add(party)
                db.commit()

            # 슬롯별 영웅 정보 조회
            hero_bases = GameDataManager.REQUIRE_CONFIGS.get("hero_bases", {})
            slots = []
            slot_infos = {}
            for slot_num, hero_uid in enumerate([party.slot_1, party.slot_2, party.slot_3], 1):
                if hero_uid:
                    hero = db.query(Hero).filter(
                        Hero.hero_uid == hero_uid,
                        Hero.user_no == user_no
                    ).first()
                    if hero:
                        hb = hero_bases.get(hero.hero_id, {})
                        info = {
                            "slot": slot_num,
                            "hero_uid": hero.hero_uid,
                            "hero_id": hero.hero_id,
                            "hero_name": hb.get("hero_name", hero.hero_id),
                            "grade": hero.grade,
                            "faction": hero.faction,
                            "level": hero.level,
                        }
                        slots.append(info)
                        slot_infos[f"slot_{slot_num}_info"] = info
                    else:
                        slots.append({"slot": slot_num, "hero_uid": None})
                        slot_infos[f"slot_{slot_num}_info"] = None
                else:
                    slots.append({"slot": slot_num, "hero_uid": None})
                    slot_infos[f"slot_{slot_num}_info"] = None

            # 시너지 계산
            factions = [s.get("faction") for s in slots if s.get("faction")]
            synergy = cls._calc_synergy(factions)

            return {
                "success": True,
                "message": "파티 조회",
                "data": {
                    "slots": slots,
                    "synergy": synergy,
                    **slot_infos,
                },
            }
        except Exception as e:
            logger.error(f"[PartyManager] get_party 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "파티 조회 중 오류가 발생했습니다.")
        finally:
            db.close()

    @classmethod
    async def set_party(cls, user_no: int, data: dict):
        """API 6002: 파티 편성 변경 — 3슬롯 자유 편성 (바알은 지휘관, 파티 밖)"""
        slot_1 = data.get("slot_1")  # hero_uid or None
        slot_2 = data.get("slot_2")  # hero_uid or None
        slot_3 = data.get("slot_3")  # hero_uid or None

        db = SessionLocal()
        try:
            # 모든 슬롯 영웅 소유권 확인
            slot_uids = [uid for uid in [slot_1, slot_2, slot_3] if uid is not None]
            for uid in slot_uids:
                hero = db.query(Hero).filter(
                    Hero.hero_uid == uid,
                    Hero.user_no == user_no
                ).first()
                if not hero:
                    return error_response(ErrorCode.ITEM_NOT_FOUND, f"영웅(uid={uid})을 찾을 수 없습니다.")

            # 중복 확인
            if len(slot_uids) != len(set(slot_uids)):
                return error_response(ErrorCode.INVALID_REQUEST, "같은 영웅을 중복 배치할 수 없습니다.")

            # 파티 업데이트
            party = db.query(Party).filter(Party.user_no == user_no).first()
            if not party:
                party = Party(user_no=user_no)
                db.add(party)

            party.slot_1 = slot_1
            party.slot_2 = slot_2
            party.slot_3 = slot_3
            db.commit()

            logger.info(f"[PartyManager] 파티 변경 (user={user_no}, slots=[{slot_1},{slot_2},{slot_3}])")

            return {
                "success": True,
                "message": "파티가 편성되었습니다.",
                "data": {
                    "slot_1": slot_1,
                    "slot_2": slot_2,
                    "slot_3": slot_3,
                },
            }
        except Exception as e:
            db.rollback()
            logger.error(f"[PartyManager] set_party 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "파티 편성 중 오류가 발생했습니다.")
        finally:
            db.close()

    # ── 헬퍼 ──

    @staticmethod
    def _calc_synergy(factions: list) -> dict:
        """진영 시너지 계산"""
        if len(factions) < 2:
            return {"name": None, "bonus": None}

        from collections import Counter
        counts = Counter(factions)

        # 3동진영
        for faction, count in counts.items():
            if count >= 3:
                bonuses = {
                    "human": {"name": "인간의 결속", "bonus": "전 스탯 +10%"},
                    "demon": {"name": "지옥의 서약", "bonus": "공격력 +15%"},
                    "celestial": {"name": "천상의 축복", "bonus": "받는 데미지 -15%"},
                }
                return bonuses.get(faction, {"name": None, "bonus": None})

        # 3종 혼합
        if len(counts) == 3:
            return {"name": "균형의 힘", "bonus": "전 스탯 +5%, 골드 +20%"}

        # 2종 조합
        if len(counts) == 2:
            pair = tuple(sorted(counts.keys()))
            pair_bonuses = {
                ("demon", "human"): {"name": "타락한 동맹", "bonus": "치명타 +10%"},
                ("celestial", "demon"): {"name": "천지의 갈등", "bonus": "스킬 데미지 +10%"},
                ("celestial", "human"): {"name": "신의 은총", "bonus": "HP 회복 +15%"},
            }
            return pair_bonuses.get(pair, {"name": None, "bonus": None})

        return {"name": None, "bonus": None}

import logging
from database import SessionLocal
from models import User, UserStat
from services.redis_manager.RedisManager import RedisManager, RedisUnavailable
from services.system.ErrorCode import ErrorCode, error_response

logger = logging.getLogger("RPG_SERVER")


class UserInfoManager:
    """유저 정보 관리 (API 1004, 1005)"""

    INITIAL_STAT_VALUE = 10           # 스탯 초기값 (5종 모두 동일)
    STAT_RESET_COST_PER_LEVEL = 500  # 스탯 리셋 비용 = 레벨 × 이 값 (나르키소스 거울의 방)

    @classmethod
    async def get_user_info(cls, user_no: int, data: dict):
        """
        유저 캐릭터 정보 반환
        - User: gold, current_stage
        - UserStat: level, exp, 5스탯 (STR/DEX/VIT/LCK/INT)
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.user_no == user_no).first()
            if not user:
                return error_response(ErrorCode.USER_NOT_FOUND, "유저를 찾을 수 없습니다.")

            stat = db.query(UserStat).filter(UserStat.user_no == user_no).first()
            if not stat:
                return error_response(ErrorCode.USER_NOT_FOUND, "유저 스탯 정보가 없습니다.")

            return {
                "success": True,
                "message": "유저 정보 조회 성공",
                "data": {
                    "user_no": user.user_no,
                    "user_name": user.user_name,
                    "gold": user.gold,
                    "current_stage": user.current_stage,
                    "level": stat.level,
                    "exp": stat.exp,
                    "stats": {
                        "str": stat.stat_str,
                        "int": stat.stat_int,
                        "dex": stat.stat_dex,
                        "vit": stat.stat_vit,
                        "lck": stat.stat_lck,
                    },
                    "stat_points": stat.stat_points,
                },
            }

        except Exception as e:
            logger.error(f"[UserInfoManager] get_user_info 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "유저 정보 조회 중 오류가 발생했습니다.")
        finally:
            db.close()

    @classmethod
    async def reset_stats(cls, user_no: int, data: dict):
        """
        API 1005: 스탯 리셋
        - 골드 소비 (레벨 × STAT_RESET_COST_PER_LEVEL)
        - 5종 스탯 → 초기값(10)으로 리셋
        - 투자한 포인트 전부 회수
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.user_no == user_no).with_for_update().first()
            if not user:
                return error_response(ErrorCode.USER_NOT_FOUND, "유저를 찾을 수 없습니다.")

            stat = db.query(UserStat).filter(UserStat.user_no == user_no).with_for_update().first()
            if not stat:
                return error_response(ErrorCode.USER_NOT_FOUND, "유저 스탯 정보가 없습니다.")

            # 비용 계산
            reset_cost = stat.level * cls.STAT_RESET_COST_PER_LEVEL
            if user.gold < reset_cost:
                return error_response(ErrorCode.INSUFFICIENT_GOLD, f"골드가 부족합니다. (필요: {reset_cost}, 보유: {user.gold})")

            # 이미 초기 상태인지 체크
            invested = (
                (stat.stat_str - cls.INITIAL_STAT_VALUE)
                + (stat.stat_int - cls.INITIAL_STAT_VALUE)
                + (stat.stat_dex - cls.INITIAL_STAT_VALUE)
                + (stat.stat_vit - cls.INITIAL_STAT_VALUE)
                + (stat.stat_lck - cls.INITIAL_STAT_VALUE)
            )
            if invested <= 0:
                return error_response(ErrorCode.INVALID_REQUEST, "리셋할 스탯이 없습니다.")

            # 비즈니스 로직
            user.gold -= reset_cost
            stat.stat_str = cls.INITIAL_STAT_VALUE
            stat.stat_int = cls.INITIAL_STAT_VALUE
            stat.stat_dex = cls.INITIAL_STAT_VALUE
            stat.stat_vit = cls.INITIAL_STAT_VALUE
            stat.stat_lck = cls.INITIAL_STAT_VALUE
            stat.stat_points += invested

            logger.info(f"[UserInfoManager] 스탯 리셋 완료 (user_no={user_no}, cost={reset_cost}, 회수 포인트={invested})")

            db.commit()

            try:
                await RedisManager.delete(f"user:{user_no}:battle_stats")
            except RedisUnavailable:
                logger.warning(f"[UserInfoManager] battle_stats 캐시 무효화 실패 (user_no={user_no})")

        except Exception as e:
            db.rollback()
            logger.error(f"[UserInfoManager] reset_stats 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "스탯 리셋 중 오류가 발생했습니다.")
        finally:
            db.close()

        return {
            "success": True,
            "message": "스탯이 초기화되었습니다.",
            "data": {
                "gold": user.gold,
                "stat_points": stat.stat_points,
                "stats": {
                    "str": stat.stat_str,
                    "int": stat.stat_int,
                    "dex": stat.stat_dex,
                    "vit": stat.stat_vit,
                    "lck": stat.stat_lck,
                },
                "reset_cost": reset_cost,
            },
        }

import logging
import bcrypt
from sqlalchemy.exc import IntegrityError
from database import SessionLocal
from models import User, UserStat, Party
from services.system.SessionManager import SessionManager
from services.system.ErrorCode import ErrorCode, error_response

logger = logging.getLogger("RPG_SERVER")


class UserInitManager:
    """회원가입 (API 1003) / 로그인 (API 1007)"""

    MIN_PASSWORD_LENGTH = 4
    MAX_PASSWORD_LENGTH = 100
    MIN_USERNAME_LENGTH = 2
    MAX_USERNAME_LENGTH = 20

    # ── 비밀번호 해싱 헬퍼 ──

    @staticmethod
    def _hash_password(plain: str) -> str:
        """bcrypt 해싱 — 평문 비밀번호를 해시로 변환"""
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def _verify_password(plain: str, hashed: str) -> bool:
        """bcrypt 검증 — 평문과 해시 비교"""
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

    # ── 입력 검증 헬퍼 ──

    @classmethod
    def _validate_user_name(cls, user_name: str):
        """유저 이름 검증. 실패 시 error_response 반환, 성공 시 None."""
        if not user_name:
            return error_response(ErrorCode.INVALID_REQUEST, "유저 이름이 필요합니다.")
        if len(user_name) < cls.MIN_USERNAME_LENGTH:
            return error_response(ErrorCode.INVALID_REQUEST, f"유저 이름은 {cls.MIN_USERNAME_LENGTH}자 이상이어야 합니다.")
        if len(user_name) > cls.MAX_USERNAME_LENGTH:
            return error_response(ErrorCode.INVALID_REQUEST, f"유저 이름은 {cls.MAX_USERNAME_LENGTH}자 이하여야 합니다.")
        return None

    @classmethod
    def _validate_password(cls, password: str):
        """비밀번호 검증. 실패 시 error_response 반환, 성공 시 None."""
        if not password:
            return error_response(ErrorCode.INVALID_PASSWORD, "비밀번호가 필요합니다.")
        if len(password) < cls.MIN_PASSWORD_LENGTH:
            return error_response(ErrorCode.INVALID_PASSWORD, f"비밀번호는 {cls.MIN_PASSWORD_LENGTH}자 이상이어야 합니다.")
        if len(password) > cls.MAX_PASSWORD_LENGTH:
            return error_response(ErrorCode.INVALID_PASSWORD, f"비밀번호는 {cls.MAX_PASSWORD_LENGTH}자 이하여야 합니다.")
        return None

    # ── API 1003: 회원가입 ──

    @classmethod
    async def create_new_user(cls, user_no: int, data: dict):
        """
        API 1003: 회원가입
        - user_name + password → 신규 유저 생성 + 세션 발급
        - 닉네임 중복 시 E2002
        """
        # ── [1] 입력 추출 & 검증 ──
        user_name = (data.get("user_name") or "").strip()
        password = data.get("password") or ""

        err = cls._validate_user_name(user_name)
        if err:
            return err

        err = cls._validate_password(password)
        if err:
            return err

        # ── [4] 비즈니스 로직 ──
        password_hash = cls._hash_password(password)

        db = SessionLocal()
        try:
            # ── [3] DB 검증 (닉네임 중복) ──
            existing = db.query(User).filter(User.user_name == user_name).first()
            if existing:
                return error_response(ErrorCode.USER_ALREADY_EXISTS, "이미 존재하는 닉네임입니다.")

            # 신규 유저 생성 (트랜잭션 1개)
            new_user = User(user_name=user_name, password_hash=password_hash)
            db.add(new_user)
            db.flush()

            new_stat = UserStat(user_no=new_user.user_no)
            db.add(new_stat)

            # 빈 파티 생성 (바알은 지휘관 — 파티 슬롯에 들어가지 않음)
            new_party = Party(user_no=new_user.user_no)
            db.add(new_party)

            # ── [5] 커밋 ──
            db.commit()

            logger.info(f"[UserInitManager] 회원가입 완료 (user_no={new_user.user_no}, user_name={user_name})")

            # 세션 발급
            session_id = await SessionManager.create_session(new_user.user_no)

            user_no_result = new_user.user_no
            user_name_result = new_user.user_name

        except IntegrityError:
            db.rollback()
            return error_response(ErrorCode.USER_ALREADY_EXISTS, "이미 존재하는 닉네임입니다.")
        except Exception as e:
            db.rollback()
            logger.error(f"[UserInitManager] create_new_user 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "회원가입 중 오류가 발생했습니다.")
        finally:
            db.close()

        # ── [6] 응답 반환 ──
        return {
            "success": True,
            "message": "캐릭터가 생성되었습니다.",
            "data": {
                "user_no": user_no_result,
                "user_name": user_name_result,
                "session_id": session_id,
            }
        }

    # ── API 1007: 로그인 ──

    @classmethod
    async def login(cls, user_no: int, data: dict):
        """
        API 1007: 로그인
        - user_name + password → 비밀번호 검증 → 세션 발급
        - 보안: 유저 없음/비밀번호 불일치 모두 동일한 에러 메시지
        """
        # ── [1] 입력 추출 ──
        user_name = (data.get("user_name") or "").strip()
        password = data.get("password") or ""

        if not user_name or not password:
            return error_response(ErrorCode.AUTH_FAILED, "아이디 또는 비밀번호를 확인해주세요.")

        # ── [3] DB 검증 ──
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.user_name == user_name).first()

            # 보안: 유저 없음과 비밀번호 불일치를 동일한 메시지로 반환
            if not user:
                return error_response(ErrorCode.AUTH_FAILED, "아이디 또는 비밀번호를 확인해주세요.")

            if not cls._verify_password(password, user.password_hash):
                return error_response(ErrorCode.AUTH_FAILED, "아이디 또는 비밀번호를 확인해주세요.")

            logger.info(f"[UserInitManager] 로그인 성공 (user_no={user.user_no}, user_name={user_name})")

            user_no_result = user.user_no
            user_name_result = user.user_name

        except Exception as e:
            logger.error(f"[UserInitManager] login 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "로그인 중 오류가 발생했습니다.")
        finally:
            db.close()

        # 세션 발급 (DB 세션 닫힌 후)
        session_id = await SessionManager.create_session(user_no_result)

        # ── [6] 응답 반환 ──
        return {
            "success": True,
            "message": "로그인 성공",
            "data": {
                "user_no": user_no_result,
                "user_name": user_name_result,
                "session_id": session_id,
            }
        }

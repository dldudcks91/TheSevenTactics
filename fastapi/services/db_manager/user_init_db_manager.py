# 레거시 파일 — Phase 2에서 UserInitManager가 직접 DB 세션을 관리하도록 변경됨
# 하위 호환을 위해 클래스 stub만 유지


class UserInitDBManager:
    """Deprecated: UserInitManager가 직접 DB 세션 관리"""
    def __init__(self, db_session=None):
        self.db = db_session

# DBManager.py (메인 매니저)
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from services.db_manager import UserInitDBManager


class DBManager:
    """DB 작업 관리자들의 중앙 접근점"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session

        self._user_init_manager = None
    



    def get_user_init_manager(self) -> UserInitDBManager:
        """유저 가입 DB 관리자 반환 (싱글톤 패턴)"""
        if self._user_init_manager is None:
            self._user_init_manager = UserInitDBManager(self.db_session)
        return self._user_init_manager


    
    def commit(self):
        """트랜잭션 커밋"""
        self.db_session.commit()
    
    def rollback(self):
        """트랜잭션 롤백"""
        self.db_session.rollback()
    
    def close(self):
        """세션 종료"""
        self.db_session.close()


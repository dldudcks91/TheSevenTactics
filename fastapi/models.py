# models.py — TheSevenTactics
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# ==========================================
# 1. User 테이블 (계정 메타 데이터)
# ==========================================
class User(Base):
    __tablename__ = "users"

    user_no = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime, default=func.now(), onupdate=func.now())
    status = Column(String(20), default="ACTIVE")

    gold = Column(BigInteger, default=0)
    current_stage = Column(Integer, default=101)

    # 관계 설정
    stat = relationship("UserStat", back_populates="user", uselist=False, cascade="all, delete-orphan")
    items = relationship("Item", back_populates="user", cascade="all, delete-orphan")

# ==========================================
# 2. UserStat 테이블 (5스탯: str/int/agi/vit/will)
# ==========================================
class UserStat(Base):
    __tablename__ = "user_stats"

    user_no = Column(Integer, ForeignKey("users.user_no"), primary_key=True)

    # 성장 데이터
    level = Column(Integer, default=1)
    exp = Column(BigInteger, default=0)

    # 순수 스탯 5종 (TheSevenTactics)
    stat_str = Column(Integer, default=5)    # 힘 — 물리 공격력
    stat_int = Column(Integer, default=5)    # 지능 — 마법 공격력, 마나
    stat_agi = Column(Integer, default=5)    # 민첩 — 행동력, 명중, 회피
    stat_vit = Column(Integer, default=5)    # 체력 — HP, 물리 방어
    stat_will = Column(Integer, default=5)   # 의지 — 용병 보정, 죄악 저항
    stat_points = Column(Integer, default=0)

    # 관계 설정
    user = relationship("User", back_populates="stat")

# ==========================================
# 3. Item 테이블 (장비 아이템 — 6부위)
# ==========================================
class Item(Base):
    __tablename__ = "items"

    item_uid = Column(String(36), primary_key=True)
    user_no = Column(Integer, ForeignKey("users.user_no"), index=True)

    base_item_id = Column(Integer, nullable=False)
    item_level = Column(Integer, default=1)
    rarity = Column(String(20), default="common")
    item_score = Column(Integer, default=0)
    prefix_id = Column(String(50), nullable=True)
    suffix_id = Column(String(50), nullable=True)
    set_id = Column(String(50), nullable=True)
    dynamic_options = Column(JSON, nullable=True)
    is_equipped = Column(Boolean, default=False, index=True)
    equip_slot = Column(String(20), nullable=True)  # weapon/armor/helmet/boots/gloves/accessory

    # 관계 설정
    user = relationship("User", back_populates="items")

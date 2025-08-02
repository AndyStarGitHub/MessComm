from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    func,
    ForeignKey,
    Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)  # noqa: VNE003
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")
    auto_comment_delay = Column(Integer, default=-1)


class Posht(Base):
    __tablename__ = "poshts"

    id = Column(Integer, primary_key=True, index=True)  # noqa: VNE003
    title = Column(String(15), index=True, nullable=False)
    posht_text = Column(String(1024), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="poshts")
    is_blocked = Column(Boolean, default=False)


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)  # noqa: VNE003
    comment_text = Column(String(1024), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    posht_id = Column(Integer, ForeignKey("poshts.id"), nullable=False)
    posht = relationship("Posht", backref="comments")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="comments")
    is_blocked = Column(Boolean, default=False)
    auto_created = Column(Boolean, default=False)

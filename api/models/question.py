from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    deal_room_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("deal_rooms.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text(), nullable=False)
    answer: Mapped[str] = mapped_column(Text(), nullable=False)
    citations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    deal_room: Mapped["DealRoom"] = relationship(back_populates="questions")  # noqa: F821

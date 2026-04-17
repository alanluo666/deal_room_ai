from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base


class DealRoom(Base):
    __tablename__ = "deal_rooms"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    owner_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="deal_rooms")  # noqa: F821
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        back_populates="deal_room",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    questions: Mapped[list["Question"]] = relationship(  # noqa: F821
        back_populates="deal_room",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

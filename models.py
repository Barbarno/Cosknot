from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Creator(Base):
    """Persona que hace cosplay. Tiene varias obras."""

    __tablename__ = "creators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    specialty: Mapped[str] = mapped_column(String(40), index=True)
    location: Mapped[str] = mapped_column(String(120))
    bio: Mapped[str] = mapped_column(Text)
    contact_email: Mapped[str] = mapped_column(String(200))
    accent: Mapped[int] = mapped_column(Integer, default=0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    works: Mapped[list["Work"]] = relationship(
        back_populates="creator",
        cascade="all, delete-orphan",
        order_by="Work.id",
    )

    def __repr__(self) -> str:
        return f"<Creator {self.slug}>"


class Work(Base):
    """Una pieza publicada por un creador."""

    __tablename__ = "works"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("creators.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    price_note: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="disponible")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    creator: Mapped[Creator] = relationship(back_populates="works")

    def __repr__(self) -> str:
        return f"<Work {self.slug}>"

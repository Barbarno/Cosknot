from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from flask_login import UserMixin

ROLES = ("comprador", "creador", "admin")


class Base(DeclarativeBase):
    pass


class User(UserMixin, Base):
    """Cuenta de la web. El rol decide qué puede hacer."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="comprador", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    creator: Mapped["Creator | None"] = relationship(back_populates="user", uselist=False)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_creator(self) -> bool:
        return self.role in ("creador", "admin")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"


class Creator(Base):
    """Persona que hace cosplay. Tiene varias obras."""

    __tablename__ = "creators"
    __table_args__ = (
        UniqueConstraint("stripe_account_id", name="uq_creators_stripe_account_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    specialty: Mapped[str] = mapped_column(String(40), index=True)
    location: Mapped[str] = mapped_column(String(120))
    bio: Mapped[str] = mapped_column(Text)
    contact_email: Mapped[str] = mapped_column(String(200))
    accent: Mapped[int] = mapped_column(Integer, default=0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    image_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_account_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    stripe_onboarding_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User | None] = relationship(back_populates="creator")
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
    price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(
        String(3), default="EUR", server_default="EUR", nullable=False
    )
    status: Mapped[str] = mapped_column(String(40), default="disponible")
    image_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    creator: Mapped[Creator] = relationship(back_populates="works")
    orders: Mapped[list["Order"]] = relationship(back_populates="work")

    def __repr__(self) -> str:
        return f"<Work {self.slug}>"


class Order(Base):
    """Encargo de una obra. El comprador lo pide y el creador lo acepta."""

    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("stripe_payment_intent_id", name="uq_orders_stripe_payment_intent"),
        UniqueConstraint(
            "stripe_checkout_session_id", name="uq_orders_stripe_checkout_session"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    work_id: Mapped[int] = mapped_column(ForeignKey("works.id"), index=True)
    status: Mapped[str] = mapped_column(
        String(20), default="solicitado", server_default="solicitado", index=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    application_fee_cents: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    buyer: Mapped[User] = relationship(foreign_keys=[buyer_id])
    work: Mapped[Work] = relationship(back_populates="orders")
    messages: Mapped[list["OrderMessage"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderMessage.id",
    )

    def __repr__(self) -> str:
        return f"<Order {self.id} {self.status}>"


class OrderMessage(Base):
    """Mensaje dentro de un pedido, entre comprador y creador."""

    __tablename__ = "order_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    order: Mapped[Order] = relationship(back_populates="messages")
    author: Mapped[User] = relationship(foreign_keys=[author_id])

    def __repr__(self) -> str:
        return f"<OrderMessage {self.id}>"


ESTADOS_AVISO = ("pendiente", "enviado", "fallido")


class EmailOutbox(Base):
    """Aviso que no salió en la petición y espera reintento.

    El estado vive en la base, no en memoria: si el dyno se reinicia a mitad de un
    reintento, la fila sigue `pendiente` y el hilo la recoge al volver. `clave` es
    el hash de destinatario, asunto y cuerpo, y es única: dos peticiones iguales
    (un doble clic, un reintento del navegador) no encolan el aviso dos veces.
    """

    __tablename__ = "email_outbox"
    __table_args__ = (UniqueConstraint("clave", name="uq_email_outbox_clave"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clave: Mapped[str] = mapped_column(String(64), index=True)
    destinatario: Mapped[str] = mapped_column(String(200), index=True)
    asunto: Mapped[str] = mapped_column(String(200))
    cuerpo: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(
        String(20), default="pendiente", server_default="pendiente", index=True
    )
    intentos: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    proximo_intento: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )
    ultimo_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    enviado_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<EmailOutbox {self.id} {self.estado} {self.destinatario}>"


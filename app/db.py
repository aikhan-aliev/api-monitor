import os
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, ForeignKey, select
)
from sqlalchemy.dialects.sqlite import JSON

from app.models import TargetIn, Target, CheckResult

# ---- Engine & Base ---------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/monitor.db")

Base = declarative_base()

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,   # set True to see SQL logs during debugging
    future=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    os.makedirs("./data", exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ---- ORM models ------------------------------------------------------------

class TargetORM(Base):
    __tablename__ = "targets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str] = mapped_column(String(16), default="GET", nullable=False)

    expected_statuses: Mapped[list] = mapped_column(JSON, default=[200, 201, 204])
    timeout_ms: Mapped[int] = mapped_column(Integer, default=3000, nullable=False)
    interval_s: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    retries: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    backoff_s: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="HIGH", nullable=False)

    results: Mapped[list["CheckResultORM"]] = relationship(
        "CheckResultORM",
        back_populates="target",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CheckResultORM(Base):
    __tablename__ = "check_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    checked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ok: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    target: Mapped["TargetORM"] = relationship("TargetORM", back_populates="results")

# ---- Converters (ORM <-> Pydantic) ----------------------------------------

def orm_to_target(t: TargetORM) -> Target:
    return Target(
        id=t.id,
        name=t.name,
        url=t.url,
        method=t.method,
        expected_statuses=t.expected_statuses or [200, 201, 204],
        timeout_ms=t.timeout_ms,
        interval_s=t.interval_s,
        retries=t.retries,
        backoff_s=t.backoff_s,
        headers=t.headers,
        enabled=t.enabled,
        severity=t.severity,
    )

def orm_to_check_result(r: CheckResultORM) -> CheckResult:
    return CheckResult(
        target_id=r.target_id,
        checked_at=r.checked_at,
        ok=r.ok,
        status=r.status,
        latency_ms=r.latency_ms,
        error=r.error,
    )

# ---- CRUD for Targets ------------------------------------------------------

import uuid

async def add_target_from_in(data: TargetIn) -> Target:
    new_id = str(uuid.uuid4())
    orm = TargetORM(
        id=new_id,
        name=data.name,
        url=str(data.url),
        method=data.method,
        expected_statuses=list(data.expected_statuses or []),
        timeout_ms=data.timeout_ms,
        interval_s=data.interval_s,
        retries=data.retries,
        backoff_s=float(data.backoff_s),
        headers=data.headers,
        enabled=bool(data.enabled),
        severity=data.severity,
    )
    async with SessionLocal() as session:
        session.add(orm)
        await session.commit()
        await session.refresh(orm)
    return orm_to_target(orm)

async def list_targets() -> List[Target]:
    async with SessionLocal() as session:
        res = await session.execute(select(TargetORM))
        return [orm_to_target(o) for o in res.scalars().all()]

async def get_target(target_id: str) -> Optional[Target]:
    async with SessionLocal() as session:
        res = await session.execute(select(TargetORM).where(TargetORM.id == target_id))
        orm = res.scalar_one_or_none()
        return orm_to_target(orm) if orm else None

async def remove_target(target_id: str) -> bool:
    async with SessionLocal() as session:
        res = await session.execute(select(TargetORM).where(TargetORM.id == target_id))
        orm = res.scalar_one_or_none()
        if not orm:
            return False
        await session.delete(orm)
        await session.commit()
        return True

async def get_or_create_demo_target() -> Target:
    async with SessionLocal() as session:
        res = await session.execute(
            select(TargetORM).where(TargetORM.url == "https://api.github.com/")
        )
        existing = res.scalar_one_or_none()
        if existing:
            return orm_to_target(existing)

    demo_in = TargetIn(
        name="GitHub API Root",
        url="https://api.github.com/",
        interval_s=60,
        timeout_ms=3000,
        expected_statuses=[200],
    )
    return await add_target_from_in(demo_in)

# ---- Checks (results) ------------------------------------------------------

async def insert_check_result(result: CheckResult) -> None:
    checked = result.checked_at
    if checked.tzinfo is not None:
        checked = checked.astimezone(timezone.utc).replace(tzinfo=None)

    orm = CheckResultORM(
        target_id=result.target_id,
        checked_at=checked,
        ok=result.ok,
        status=result.status,
        latency_ms=result.latency_ms,
        error=result.error,
    )
    async with SessionLocal() as session:
        session.add(orm)
        await session.commit()

async def get_last_result_for_target(target_id: str) -> Optional[CheckResult]:
    async with SessionLocal() as session:
        res = await session.execute(
            select(CheckResultORM)
            .where(CheckResultORM.target_id == target_id)
            .order_by(CheckResultORM.checked_at.desc(), CheckResultORM.id.desc())
            .limit(1)
        )
        orm = res.scalar_one_or_none()
        return orm_to_check_result(orm) if orm else None

async def list_last_results_for_all_targets() -> list[CheckResult | dict]:
    targets = await list_targets()
    out: list[CheckResult | dict] = []
    for t in targets:
        last = await get_last_result_for_target(t.id)
        if last:
            out.append(last)
        else:
            out.append({"target_id": t.id, "ok": None, "message": "No checks recorded yet"})
    return out

"""
Resolve or create internal User records for Telegram / WhatsApp / IVR users.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.channel_identity import ChannelIdentity


def normalize_external_id(channel: str, external_id: str) -> str:
    if channel == "whatsapp":
        return external_id.replace("whatsapp:", "").strip()
    return external_id.strip()


def synthetic_phone(channel: str, external_id: str) -> str:
    clean = normalize_external_id(channel, external_id)
    digits = "".join(c for c in clean if c.isdigit())[-15:] or clean.replace("+", "")[:15]
    return f"{channel[:2]}:{digits}"[:15]


async def get_user_for_channel(
    db: AsyncSession,
    channel: str,
    external_id: str,
) -> User | None:
    if not channel or not external_id:
        return None

    ext = normalize_external_id(channel, external_id)
    result = await db.execute(
        select(ChannelIdentity).where(
            ChannelIdentity.channel == channel,
            ChannelIdentity.external_id == ext,
        )
    )
    link = result.scalar_one_or_none()
    if link:
        user_result = await db.execute(select(User).where(User.id == link.user_id))
        return user_result.scalar_one_or_none()
    return None


async def get_or_create_channel_user(
    db: AsyncSession,
    channel: str,
    external_id: str,
    *,
    full_name: str | None = None,
    preferred_language: str = "hi",
) -> User:
    ext = normalize_external_id(channel, external_id)

    existing = await get_user_for_channel(db, channel, ext)
    if existing:
        return existing

    phone = synthetic_phone(channel, ext)
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            phone=phone,
            full_name=full_name,
            preferred_language=preferred_language,
        )
        db.add(user)
        await db.flush()

    db.add(ChannelIdentity(channel=channel, external_id=ext, user_id=user.id))
    await db.commit()
    await db.refresh(user)
    return user

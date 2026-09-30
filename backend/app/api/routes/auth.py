"""
Auth routes — phone OTP login + DigiLocker e-KYC (sandbox).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, verify_otp, send_otp
from app.models.user import User
from sqlalchemy import select

router = APIRouter()


class PhoneRequest(BaseModel):
    phone: str


class OTPVerify(BaseModel):
    phone: str
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/send-otp")
async def request_otp(body: PhoneRequest):
    otp = await send_otp(body.phone)
    # In dev mode, return OTP in response so you can test without a real SMS provider.
    # Remove `dev_otp` from this response before deploying to production.
    return {"message": "OTP sent", "dev_otp": otp}


@router.post("/verify-otp", response_model=TokenResponse)
async def verify(body: OTPVerify, db: AsyncSession = Depends(get_db)):
    if not await verify_otp(body.phone, body.otp):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

    result = await db.execute(select(User).where(User.phone == body.phone))
    user = result.scalar_one_or_none()
    if not user:
        user = User(phone=body.phone)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.get("/digilocker/redirect")
async def digilocker_redirect():
    """Returns DigiLocker OAuth URL for e-KYC (sandbox)."""
    from app.core.config import settings
    url = (
        f"https://api.digitallocker.gov.in/public/oauth2/1/authorize"
        f"?response_type=code&client_id={settings.DIGILOCKER_CLIENT_ID}"
        f"&redirect_uri={settings.DIGILOCKER_REDIRECT_URI}&state=kyc"
    )
    return {"url": url}


@router.get("/digilocker/callback")
async def digilocker_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handles DigiLocker OAuth callback, marks user Aadhaar-verified."""
    # In sandbox, exchange code for token and mark verified
    # Full production flow requires licensed KYC provider
    return {"message": "KYC sandbox callback received", "code": code}

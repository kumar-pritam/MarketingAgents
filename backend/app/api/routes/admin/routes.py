from fastapi import APIRouter, HTTPException, Response, Cookie
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime, timedelta
import secrets
import base64
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv

from app.core.database import (
    UserDB,
    TrackedRunDB,
    PaymentDB,
    PendingPaymentDB,
    AdminConfigDB,
)

_env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(_env_path)

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_COOKIE_NAME = "admin_session"
SESSION_EXPIRY_HOURS = 24

BASE_DIR = Path(__file__).parent.parent.parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PAYMENTS_DIR = DATA_DIR / "payments"

sessions: dict = {}


def create_session() -> str:
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=SESSION_EXPIRY_HOURS)).isoformat(),
    }
    return token


def verify_session(token: Optional[str]) -> bool:
    if not token:
        return False
    session = sessions.get(token)
    if not session:
        return False
    expires = datetime.fromisoformat(session["expires_at"])
    if expires < datetime.now():
        del sessions[token]
        return False
    return True


def get_admin_password_from_env() -> str:
    return os.getenv("ADMIN_PASSWORD", "")


def require_admin(admin_session: Optional[str] = Cookie(None)):
    if not verify_session(admin_session):
        raise HTTPException(status_code=401, detail="Not authenticated")


class LoginRequest(BaseModel):
    password: str


class ConfigUpdate(BaseModel):
    key: str
    value: Any


class LoginResponse(BaseModel):
    success: bool
    message: str


class UsageStats(BaseModel):
    total_runs: int
    anonymous_runs: int
    free_user_runs: int
    pro_runs: int
    anonymous_users: int
    free_users: int
    pro_users: int
    daily_trend: List[dict]
    hourly_trend: List[dict]
    top_agents: List[dict]
    revenue_estimate: float


class UserDetail(BaseModel):
    email: str
    name: str
    tier: str
    subscribed_at: Optional[str]
    subscription_expires: Optional[str]
    runs_used: int
    created_at: Optional[str]


class PaymentDetail(BaseModel):
    user_email: str
    user_name: str
    amount: float
    billing_cycle: str
    payment_method: str
    status: str
    date: str


class PaymentSubmission(BaseModel):
    user_email: str
    user_name: str
    billing_cycle: str
    amount: float
    screenshot_data: str


class ConfigItem(BaseModel):
    key: str
    value: Any
    description: str


class SignUpRequest(BaseModel):
    email: str
    name: str
    tier: str = "free"


class UpdateTierRequest(BaseModel):
    email: str
    tier: str


@router.post("/login", response_model=LoginResponse)
async def admin_login(request: LoginRequest, response: Response):
    admin_password = get_admin_password_from_env()
    if not admin_password:
        raise HTTPException(status_code=500, detail="Admin password not configured")
    if request.password == admin_password:
        token = create_session()
        response.set_cookie(key=ADMIN_COOKIE_NAME, value=token, httponly=True, max_age=SESSION_EXPIRY_HOURS * 3600, samesite="lax")
        return LoginResponse(success=True, message="Login successful")
    return LoginResponse(success=False, message="Invalid password")


@router.post("/logout")
async def admin_logout(response: Response, admin_session: Optional[str] = Cookie(None)):
    if admin_session and admin_session in sessions:
        del sessions[admin_session]
    response.delete_cookie(ADMIN_COOKIE_NAME)
    return {"success": True}


@router.get("/verify")
async def verify_admin(admin_session: Optional[str] = Cookie(None)):
    return {"authenticated": verify_session(admin_session)}


@router.get("/config", response_model=List[ConfigItem])
async def get_config(admin_session: Optional[str] = Cookie(None)):
    require_admin(admin_session)
    try:
        config_items = AdminConfigDB.get_all()
        return [ConfigItem(key=c["key"], value=c["value"], description=c.get("description", "")) for c in config_items]
    except Exception as e:
        print(f"Error getting config: {e}")
        return []


@router.put("/config")
async def update_config(update: ConfigUpdate, admin_session: Optional[str] = Cookie(None)):
    require_admin(admin_session)
    try:
        AdminConfigDB.set(update.key, update.value)
        return {"success": True, "message": f"Updated {update.key}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(admin_session: Optional[str] = Cookie(None)):
    require_admin(admin_session)
    try:
        all_runs = TrackedRunDB.get_all()
        user_runs = TrackedRunDB.count_by_user()
        agent_counts = TrackedRunDB.count_by_agent()
        daily_trend = TrackedRunDB.get_daily_trend(30)
        hourly_trend = TrackedRunDB.get_hourly_trend()
        tier_counts = UserDB.count_by_tier()
        
        pro_users = tier_counts.get("pro", 0)
        free_users = tier_counts.get("free", 0)
        anonymous_users = len([u for u, r in user_runs.items() if u == "anonymous"])
        
        top_agents = [{"agent_id": aid, "runs": count} for aid, count in sorted(agent_counts.items(), key=lambda x: -x[1])[:10]]
        hourly_trend_formatted = [{"hour": int(r["hour"]), "runs": r["runs"]} for r in hourly_trend]
        
        return UsageStats(
            total_runs=len(all_runs),
            anonymous_runs=sum(1 for r in all_runs if r.get("user_id") == "anonymous"),
            free_user_runs=sum(r for u, r in user_runs.items() if u != "anonymous"),
            pro_runs=0,
            anonymous_users=anonymous_users,
            free_users=free_users,
            pro_users=pro_users,
            daily_trend=[{"date": str(r["date"]), "runs": r["runs"]} for r in daily_trend],
            hourly_trend=hourly_trend_formatted,
            top_agents=top_agents,
            revenue_estimate=pro_users * 1000,
        )
    except Exception as e:
        print(f"Error getting usage stats: {e}")
        return UsageStats(
            total_runs=0, anonymous_runs=0, free_user_runs=0, pro_runs=0,
            anonymous_users=0, free_users=0, pro_users=0, daily_trend=[],
            hourly_trend=[{"hour": i, "runs": 0} for i in range(24)], top_agents=[], revenue_estimate=0
        )


@router.get("/users", response_model=List[UserDetail])
async def get_users(admin_session: Optional[str] = Cookie(None)):
    require_admin(admin_session)
    try:
        users = UserDB.get_all()
        return [
            UserDetail(
                email=u.get("email", ""),
                name=u.get("name", ""),
                tier=u.get("tier", "free"),
                subscribed_at=str(u.get("subscribed_at")) if u.get("subscribed_at") else None,
                subscription_expires=str(u.get("subscription_expires")) if u.get("subscription_expires") else None,
                runs_used=u.get("runs_used", 0),
                created_at=str(u.get("created_at")) if u.get("created_at") else None,
            )
            for u in users
        ]
    except Exception as e:
        print(f"Error getting users: {e}")
        return []


@router.put("/users/tier")
async def update_user_tier(request: UpdateTierRequest, admin_session: Optional[str] = Cookie(None)):
    require_admin(admin_session)
    try:
        UserDB.update(request.email, tier=request.tier)
        return {"success": True, "message": f"User {request.email} tier updated to {request.tier}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payments", response_model=List[PaymentDetail])
async def get_payments(admin_session: Optional[str] = Cookie(None)):
    require_admin(admin_session)
    try:
        payments = PaymentDB.get_completed()
        return [
            PaymentDetail(
                user_email=p.get("user_email", ""),
                user_name=p.get("user_name", ""),
                amount=float(p.get("amount", 0)),
                billing_cycle=p.get("billing_cycle", "monthly"),
                payment_method=p.get("payment_method", "upi"),
                status=p.get("status", "completed"),
                date=str(p.get("date", "")),
            )
            for p in payments
        ]
    except Exception as e:
        print(f"Error getting payments: {e}")
        return []


@router.post("/track-signup")
async def track_signup(request: SignUpRequest):
    try:
        UserDB.create(request.email, request.name, request.tier)
        return {"success": True, "message": "User signup tracked"}
    except Exception as e:
        print(f"Error tracking signup: {e}")
        return {"success": False, "message": str(e)}


@router.post("/track-run")
async def track_run(agent_id: str, user_id: str = "anonymous"):
    try:
        TrackedRunDB.create(agent_id, user_id)
        return {"success": True}
    except Exception as e:
        print(f"Error tracking run: {e}")
        return {"success": False}


@router.get("/stats")
async def get_public_stats():
    try:
        all_runs = TrackedRunDB.get_all()
        users = UserDB.get_all()
        agent_counts = TrackedRunDB.count_by_agent()
        return {
            "total_runs": len(all_runs),
            "user_count": len(users),
            "agent_counts": agent_counts,
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {"total_runs": 0, "user_count": 0, "agent_counts": {}}


@router.post("/payments/submit")
async def submit_payment(payment: PaymentSubmission):
    try:
        payment_id = str(uuid.uuid4())[:8]
        PAYMENTS_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = PAYMENTS_DIR / f"{payment_id}.png"
        
        if payment.screenshot_data.startswith("data:image"):
            header, data = payment.screenshot_data.split(",", 1)
            image_data = base64.b64decode(data)
        else:
            image_data = base64.b64decode(payment.screenshot_data)
        
        with open(screenshot_path, "wb") as f:
            f.write(image_data)
        
        PendingPaymentDB.create(
            payment_id=payment_id,
            user_email=payment.user_email,
            user_name=payment.user_name,
            billing_cycle=payment.billing_cycle,
            amount=payment.amount,
            screenshot_path=str(screenshot_path),
        )
        return {"success": True, "message": "Payment submitted for verification", "payment_id": payment_id}
    except Exception as e:
        print(f"Error submitting payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payments/pending")
async def get_pending_payments(admin_session: Optional[str] = Cookie(None)):
    require_admin(admin_session)
    try:
        pending = PendingPaymentDB.get_pending()
        return [
            {
                "id": p.get("id", ""),
                "user_email": p.get("user_email", ""),
                "user_name": p.get("user_name", ""),
                "billing_cycle": p.get("billing_cycle", "monthly"),
                "amount": float(p.get("amount", 0)),
                "screenshot_path": p.get("screenshot_path", ""),
                "status": p.get("status", "pending"),
                "submitted_at": str(p.get("submitted_at", "")),
            }
            for p in pending
        ]
    except Exception as e:
        print(f"Error getting pending payments: {e}")
        return []


@router.post("/payments/{payment_id}/approve")
async def approve_payment(payment_id: str, admin_session: Optional[str] = Cookie(None)):
    require_admin(admin_session)
    try:
        payment = PendingPaymentDB.get_by_id(payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        PendingPaymentDB.update_status(payment_id, "approved")
        
        billing_cycle = payment.get("billing_cycle", "monthly")
        expires = datetime.now()
        if billing_cycle == "yearly":
            expires = expires + timedelta(days=365)
        else:
            expires = expires + timedelta(days=30)
        
        UserDB.update(
            payment.get("user_email", ""),
            tier="pro",
            subscription_expires=expires,
            subscribed_at=datetime.now(),
            billing_cycle=billing_cycle,
        )
        
        PaymentDB.create(
            user_email=payment.get("user_email", ""),
            user_name=payment.get("user_name", ""),
            amount=float(payment.get("amount", 0)),
            billing_cycle=billing_cycle,
            status="completed",
        )
        
        return {"success": True, "message": "Payment approved and user upgraded to Pro"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error approving payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payments/{payment_id}/reject")
async def reject_payment(payment_id: str, admin_session: Optional[str] = Cookie(None)):
    require_admin(admin_session)
    try:
        PendingPaymentDB.update_status(payment_id, "rejected")
        return {"success": True, "message": "Payment rejected"}
    except Exception as e:
        print(f"Error rejecting payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payments/{payment_id}/screenshot")
async def get_payment_screenshot(payment_id: str):
    screenshot_path = PAYMENTS_DIR / f"{payment_id}.png"
    if not screenshot_path.exists():
        raise HTTPException(status_code=404, detail="Screenshot not found")
    from fastapi.responses import FileResponse
    return FileResponse(screenshot_path, media_type="image/png")

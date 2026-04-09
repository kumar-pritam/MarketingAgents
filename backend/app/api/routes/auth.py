from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    set_user_cookie,
    clear_user_cookie,
    require_user,
)
from app.core.database import UserDB, get_cursor

router = APIRouter(prefix="/auth", tags=["auth"])


class SignUpRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class SetPasswordRequest(BaseModel):
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    tier: str
    must_set_password: bool
    subscribed_at: Optional[str]
    subscription_expires: Optional[str]
    created_at: Optional[str]


@router.post("/signup")
async def signup(request: SignUpRequest, response: Response):
    existing = UserDB.get_by_email(request.email)
    if existing and existing.get("password_hash"):
        raise HTTPException(status_code=400, detail="Email already registered")

    if existing:
        UserDB.update(
            request.email,
            name=request.name,
            password_hash=hash_password(request.password),
            must_set_password=False,
            last_login=datetime.now(),
        )
    else:
        UserDB.create_with_password(request.email, request.name, request.password)

    user = UserDB.get_by_email(request.email)
    token = create_access_token(user["id"], user["email"])
    set_user_cookie(response, token)

    return {
        "success": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name", ""),
            "tier": user.get("tier", "free"),
            "must_set_password": user.get("must_set_password", False),
        }
    }


@router.post("/login")
async def login(request: LoginRequest, response: Response):
    user = UserDB.get_by_email(request.email)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.get("password_hash"):
        raise HTTPException(
            status_code=401,
            detail="Please set a password first",
            headers={"X-Must-Set-Password": "true"}
        )
    
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    UserDB.update(request.email, last_login=datetime.now())
    
    token = create_access_token(user["id"], user["email"])
    set_user_cookie(response, token)
    
    return {
        "success": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name", ""),
            "tier": user.get("tier", "free"),
            "must_set_password": False,
            "subscribed_at": str(user.get("subscribed_at")) if user.get("subscribed_at") else None,
            "subscription_expires": str(user.get("subscription_expires")) if user.get("subscription_expires") else None,
        }
    }


@router.post("/logout")
async def logout(response: Response):
    clear_user_cookie(response)
    return {"success": True}


@router.get("/me")
async def get_me(request: Request):
    user_data = require_user(request)
    
    user = UserDB.get_by_id(user_data["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user.get("name", ""),
        "tier": user.get("tier", "free"),
        "must_set_password": user.get("must_set_password", False),
        "subscribed_at": str(user.get("subscribed_at")) if user.get("subscribed_at") else None,
        "subscription_expires": str(user.get("subscription_expires")) if user.get("subscription_expires") else None,
        "created_at": str(user.get("created_at")) if user.get("created_at") else None,
    }


@router.post("/set-password")
async def set_password(request: SetPasswordRequest, http_request: Request):
    user_data = require_user(http_request)
    
    UserDB.update(
        user_data["email"],
        password_hash=hash_password(request.password),
        must_set_password=False,
    )
    
    return {"success": True, "message": "Password set successfully"}


@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    user_data = require_user(request)
    user = UserDB.get_by_id(user_data["user_id"])
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    token = create_access_token(user["id"], user["email"])
    set_user_cookie(response, token)
    
    return {"success": True}

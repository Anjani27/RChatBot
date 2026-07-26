"""Auth API — registration, login, and session management endpoints with email support."""
import uuid
from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field

from app.repositories import user_repository as repo
from app.services import auth_service as auth


router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthPayload(BaseModel):
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=4, max_length=100)


@router.post("/register")
def register(payload: AuthPayload):
    """Register a new user email."""
    # Check if user already exists
    existing = repo.get_user(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered."
        )

    # Hash password and store user
    hashed = auth.hash_password(payload.password)
    try:
        repo.create_user(payload.email, hashed)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {e}"
        )

    return {"status": "success", "message": "User registered successfully."}


@router.post("/login")
def login(payload: AuthPayload):
    """Authenticate and start a new session."""
    user = repo.get_user(payload.email)
    if not user or not auth.verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    # Create new session
    session_id = str(uuid.uuid4())
    repo.create_session(session_id, user["email"])

    return {
        "status": "success",
        "token": session_id,
        "email": user["email"]
    }


@router.post("/logout")
def logout(authorization: str = Header(None)):
    """Terminate the active session."""
    if not authorization:
        raise HTTPException(status_code=400, detail="Authorization header required.")
    
    try:
        _, token = authorization.split(" ")
        repo.delete_session(token)
    except Exception:
        pass
        
    return {"status": "success", "message": "Logged out successfully."}

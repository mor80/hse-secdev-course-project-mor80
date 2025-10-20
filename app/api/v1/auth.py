from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database import get_db
from app.adapters.repositories.user_repository import UserRepository
from app.api.dependencies import get_current_active_user
from app.config import settings
from app.domain.entities import User
from app.domain.models import LoginRequest, Token, UserCreate, UserResponse
from app.services.auth_service import authenticate_user, create_access_token, get_password_hash

router = APIRouter()


async def get_login_credentials(request: Request) -> LoginRequest:
    """
    Resolve login credentials from either JSON payload or form data.
    """
    content_type = (request.headers.get("content-type") or "").lower()

    try:
        if content_type.startswith("application/json"):
            payload = await request.json()
        else:
            form = await request.form()
            payload = dict(form)
    except Exception as exc:
        raise RequestValidationError([{"loc": ("body",), "msg": str(exc), "type": "value_error"}])

    try:
        return LoginRequest.model_validate(payload)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors())


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    repository = UserRepository(db)

    if await repository.get_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    if await repository.get_by_username(user.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = get_password_hash(user.password)
    db_user = await repository.create(user, hashed_password)
    return db_user


@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest = Depends(get_login_credentials), db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.options("/login")
async def login_options() -> dict:
    """
    Support CORS preflight checks for the login endpoint.
    """
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return current_user

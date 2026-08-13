from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserOut, Token
from app.services.auth import register_user, authenticate_user
from app.core.security import create_access_token
from app.core.deps import get_current_user

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@auth_router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Returns the created UserOut record (excluding sensitive credentials).
    Token is intentionally omitted here requiring an explicit login request.
    """
    return register_user(db, user_in)

@auth_router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, expecting form-data with username (email) and password.
    Returns signed Bearer JWT token upon successful authentication.
    """
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return Token(access_token=access_token, token_type="bearer")

@auth_router.post("/logout")
def logout():
    """
    Stateless JWT Logout Endpoint.
    
    TRADEOFF NOTE:
    Because JWT tokens are stateless, server-side session invalidation is not active
    in this phase. The client should discard the token locally upon receiving this response.
    Future phases can implement a Redis-backed token revocation blocklist if required.
    """
    return {"message": "Successfully logged out (client should discard access token)"}

@auth_router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Retrieve details of the currently authenticated user based on Bearer token."""
    return current_user

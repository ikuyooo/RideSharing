from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.settings import Settings, get_settings
from app.db.session import get_db
from app.modules.identity import service
from app.modules.identity.deps import get_current_user
from app.modules.identity.models import User
from app.modules.identity.schemas import GenderIn, LoginIn, RefreshIn, RegisterIn, TokenPair, UserOut

router = APIRouter(tags=["identity"])


@router.post("/api/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, session: Session = Depends(get_db)) -> User:
    return service.register(session, body.email, body.password, body.role, body.display_name)


@router.post("/api/auth/login", response_model=TokenPair)
def login(body: LoginIn, session: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> TokenPair:
    return service.login(session, body.email, body.password, settings)


@router.post("/api/auth/refresh", response_model=TokenPair)
def refresh(body: RefreshIn, session: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> TokenPair:
    return service.refresh(session, body.refresh_token, settings)


@router.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshIn, session: Session = Depends(get_db)) -> Response:
    service.logout(session, body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api/users/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.put("/api/users/me/gender", response_model=UserOut)
def set_gender(body: GenderIn, user: User = Depends(get_current_user), session: Session = Depends(get_db)) -> User:
    return service.set_own_gender(session, session.merge(user), body.gender)

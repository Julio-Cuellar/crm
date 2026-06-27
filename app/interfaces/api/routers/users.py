import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.application.use_cases.create_user import CreateUserUseCase
from app.application.use_cases.get_user import GetUserUseCase
from app.application.use_cases.list_users import ListUsersUseCase
from app.application.use_cases.invite_user import InviteUserUseCase
from app.domain.exceptions.base import AppException
from app.interfaces.api.dependencies.users import (
    get_create_user_use_case,
    get_get_user_use_case,
    get_list_users_use_case
)
from app.interfaces.api.dependencies.invitations import get_invite_user_use_case
from app.interfaces.api.dependencies.auth_bearer import get_current_user
from app.domain.entities.user import User as DomainUser
from app.interfaces.api.schemas.user import UserCreate, UserResponse
from app.interfaces.api.schemas.invitation import InviteRequest, InvitationResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/invite", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    invite_in: InviteRequest,
    current_user: DomainUser = Depends(get_current_user),
    invite_use_case: InviteUserUseCase = Depends(get_invite_user_use_case)
):
    """
    Invita a un nuevo colaborador a unirse al Tenant del usuario autenticado actual.
    Solo permitido para roles OWNER o ADMIN.
    """
    if current_user.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para invitar colaboradores a este negocio."
        )
    try:
        return await invite_use_case.execute(
            tenant_id=current_user.tenant_id,
            email=invite_in.email,
            role=invite_in.role
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})


@router.post("/{tenant_id}", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    tenant_id: uuid.UUID,
    user_in: UserCreate,
    create_use_case: CreateUserUseCase = Depends(get_create_user_use_case)
):
    try:
        user = await create_use_case.execute(
            tenant_id=tenant_id,
            email=user_in.email,
            password=user_in.password,
            name=user_in.name,
            role=user_in.role
        )
        return user
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})


@router.get("/", response_model=list[UserResponse])
async def list_users(
    current_user: DomainUser = Depends(get_current_user),
    list_use_case: ListUsersUseCase = Depends(get_list_users_use_case)
):
    """
    Lista todos los usuarios asociados al tenant del usuario autenticado actual.
    """
    try:
        return await list_use_case.execute(current_user.tenant_id)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    get_use_case: GetUserUseCase = Depends(get_get_user_use_case)
):
    try:
        return await get_use_case.execute(user_id)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})

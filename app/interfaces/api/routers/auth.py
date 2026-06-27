from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.domain.exceptions.base import AppException
from app.interfaces.api.schemas.auth import RegisterRequest, VerifyRequest, LoginRequest, TokenResponse
from app.interfaces.api.schemas.tenant import TenantResponse
from app.interfaces.api.schemas.user import UserResponse
from app.interfaces.api.schemas.invitation import InvitationDetailsResponse, AcceptInvitationRequest
from app.interfaces.api.dependencies.auth import (
    get_register_tenant_use_case,
    get_verify_registration_use_case,
    get_login_use_case
)
from app.interfaces.api.dependencies.invitations import (
    get_get_invitation_by_token_use_case,
    get_accept_invitation_use_case
)
from app.interfaces.api.dependencies.blacklisted_tokens import get_logout_use_case
from app.interfaces.api.dependencies.auth_bearer import get_current_user, security
from app.application.use_cases.register_tenant import RegisterTenantUseCase
from app.application.use_cases.verify_registration import VerifyRegistrationUseCase
from app.application.use_cases.login import LoginUseCase
from app.application.use_cases.get_invitation_by_token import GetInvitationByTokenUseCase
from app.application.use_cases.accept_invitation import AcceptInvitationUseCase
from app.application.use_cases.logout import LogoutUseCase
from app.domain.entities.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_202_ACCEPTED)
async def register_tenant(
    register_in: RegisterRequest,
    use_case: RegisterTenantUseCase = Depends(get_register_tenant_use_case)
):
    """
    Inicia la solicitud de registro para un nuevo Tenant y su administrador.
    Registra los datos temporalmente y envía un token de verificación (por consola/evento).
    """
    try:
        await use_case.execute(
            email=register_in.email,
            password=register_in.password,
            name=register_in.name,
            tenant_name=register_in.tenant_name
        )
        return {
            "message": "Solicitud de registro aceptada. Se ha enviado un código de verificación a su correo electrónico."
        }
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})


@router.post("/verify", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def verify_registration(
    verify_in: VerifyRequest,
    use_case: VerifyRegistrationUseCase = Depends(get_verify_registration_use_case)
):
    """
    Verifica el token de correo. Al completarse con éxito, se crea el Tenant y el
    usuario OWNER de forma automática y asíncrona.
    """
    try:
        tenant = await use_case.execute(
            email=verify_in.email,
            token=verify_in.token
        )
        return tenant
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})


@router.post("/login", response_model=TokenResponse)
async def login(
    login_in: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case)
):
    """
    Autentica al usuario usando email y contraseña, retornando tokens de acceso y refresco JWT.
    """
    try:
        user, access_token, refresh_token = await use_case.execute(
            email=login_in.email,
            password=login_in.password
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Retorna el perfil del usuario autenticado actual. Protegido por JWT.
    """
    return current_user


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    use_case: LogoutUseCase = Depends(get_logout_use_case)
):
    """
    Cierra la sesión del usuario invalidando el token JWT recibido en la lista negra.
    """
    token = credentials.credentials
    await use_case.execute(token)
    return {"message": "Sesión cerrada exitosamente en el servidor."}


@router.get("/invitations/{token}", response_model=InvitationDetailsResponse)
async def get_invitation_details(
    token: str,
    use_case: GetInvitationByTokenUseCase = Depends(get_get_invitation_by_token_use_case)
):
    """
    Retorna los detalles asociados a un token de invitación. Útil para rellenar el formulario de registro del colaborador.
    """
    try:
        invitation, tenant_name = await use_case.execute(token)
        return InvitationDetailsResponse(
            email=invitation.email,
            tenant_name=tenant_name,
            role=invitation.role,
            token=invitation.token
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})


@router.post("/invitations/accept", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def accept_invitation(
    accept_in: AcceptInvitationRequest,
    use_case: AcceptInvitationUseCase = Depends(get_accept_invitation_use_case)
):
    """
    Acepta una invitación de colaborador, crea el usuario definitivo en la base de datos y marca la invitación como utilizada.
    """
    try:
        user = await use_case.execute(
            token=accept_in.token,
            name=accept_in.name,
            password=accept_in.password
        )
        return user
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})

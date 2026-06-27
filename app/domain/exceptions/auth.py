from app.domain.exceptions.base import AppException


class InvalidVerificationTokenException(AppException):
    def __init__(self, message: str = "El token de verificación proporcionado es inválido."):
        super().__init__(
            status_code=400,
            code="INVALID_VERIFICATION_TOKEN",
            message=message
        )


class TokenExpiredException(AppException):
    def __init__(self, message: str = "El token de verificación ha expirado."):
        super().__init__(
            status_code=400,
            code="TOKEN_EXPIRED",
            message=message
        )


class EmailAlreadyRegisteredException(AppException):
    def __init__(self, message: str = "Este correo electrónico ya se encuentra registrado."):
        super().__init__(
            status_code=409,
            code="EMAIL_ALREADY_REGISTERED",
            message=message
        )


class PendingRegistrationNotFoundException(AppException):
    def __init__(self, message: str = "No se encontró ninguna solicitud de registro pendiente para este correo."):
        super().__init__(
            status_code=404,
            code="PENDING_REGISTRATION_NOT_FOUND",
            message=message
        )


class InvalidCredentialsException(AppException):
    def __init__(self, message: str = "Credenciales incorrectas. Verifique su correo o contraseña."):
        super().__init__(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message=message
        )


class InvitationNotFoundException(AppException):
    def __init__(self, message: str = "La invitación solicitada no existe o ya fue utilizada."):
        super().__init__(
            status_code=404,
            code="INVITATION_NOT_FOUND",
            message=message
        )


class InvitationExpiredException(AppException):
    def __init__(self, message: str = "La invitación ha expirado. Por favor solicite una nueva invitación."):
        super().__init__(
            status_code=400,
            code="INVITATION_EXPIRED",
            message=message
        )

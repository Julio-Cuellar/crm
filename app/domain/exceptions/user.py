from app.domain.exceptions.base import AppException


class UserNotFoundException(AppException):
    def __init__(self, message: str = "El usuario solicitado no existe."):
        super().__init__(
            status_code=404,
            code="USER_NOT_FOUND",
            message=message
        )


class UserAlreadyExistsException(AppException):
    def __init__(self, message: str = "Ya existe un usuario registrado con este correo electrónico."):
        super().__init__(
            status_code=409,
            code="USER_ALREADY_EXISTS",
            message=message
        )


class CannotModifyOwnerException(AppException):
    def __init__(self, message: str = "No está permitido modificar o desactivar al usuario propietario (OWNER) del negocio."):
        super().__init__(
            status_code=403,
            code="CANNOT_MODIFY_OWNER",
            message=message
        )

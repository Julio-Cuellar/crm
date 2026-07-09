from app.platform.exceptions import AppException


class ServiceNotFoundException(AppException):
    def __init__(self, message: str = "El servicio solicitado no existe o no pertenece a este negocio."):
        super().__init__(
            status_code=404,
            code="SERVICE_NOT_FOUND",
            message=message
        )
